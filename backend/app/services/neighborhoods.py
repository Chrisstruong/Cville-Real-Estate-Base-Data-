import asyncio
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import shapely
from fastapi import HTTPException
from psycopg import sql
from psycopg.rows import dict_row
from shapely.geometry import shape

from app.database.connection import pool

DATA_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "planning-neighborhoods.geojson"
)

MAX_CANDIDATES = 50_000
MAX_RESULTS = 10_000

DATASETS = {
    "properties": (
        "real_estate_current_assessment",
        "parcel_number",
        ("parcel_number", "longitude", "latitude"),
    ),
    "crimes": (
        "crime",
        "record_id",
        (
            "record_id",
            "longitude",
            "latitude",
            "location_precision",
        ),
    ),
}


@lru_cache
def load_neighborhoods():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    if data.get("type") != "FeatureCollection":
        raise ValueError("Invalid neighborhood GeoJSON.")

    neighborhoods = {}

    for feature in data["features"]:
        neighborhood_id = feature["properties"]["OBJECTID"]
        geometry = shape(feature["geometry"])

        if (
            not isinstance(neighborhood_id, int)
            or neighborhood_id in neighborhoods
            or geometry.geom_type not in ("Polygon", "MultiPolygon")
            or geometry.is_empty
            or not geometry.is_valid
        ):
            raise ValueError("Invalid neighborhood ID or geometry")

        west, south, east, north = geometry.bounds

        if not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
            raise ValueError("Expected longitude/latitude coordinates.")

        # Accelerates repeated spatial comparisions
        shapely.prepare(geometry)
        neighborhoods[neighborhood_id] = geometry

    if not neighborhoods:
        raise ValueError("Neighborhood dataset is empty.")

    return neighborhoods


def select_unique_members(rows, neighborhood_id, neighborhoods):
    if not rows:
        return [], 0

    points = shapely.points(
        [row["longitude"] for row in rows],
        [row["latitude"] for row in rows],
    )

    selected_polygon = neighborhoods[neighborhood_id]

    # contains excludes points exactly on the polygon boundary
    inside = shapely.contains(selected_polygon, points)
    covered = shapely.covers(selected_polygon, points)

    # Detect points covered by more than one official polygon
    coverage_count = np.zeros(len(rows), dtype=np.int16)

    for polygon in neighborhoods.values():
        coverage_count += shapely.covers(polygon, points).astype(np.int16)

    accepted = inside & (coverage_count == 1)

    # Boundary points and overlapping assignments are excluded
    ambiguous = covered & ~accepted

    matched_rows = [row for row, keep in zip(rows, accepted) if keep]

    return matched_rows, int(ambiguous.sum())


async def fetch_neighborhood_records(
    neighborhood_id: int,
    dataset: str,
):
    neighborhoods = load_neighborhoods()
    polygon = neighborhoods.get(neighborhood_id)

    if polygon is None:
        raise HTTPException(
            status_code=404,
            detail="Neighborhood not found.",
        )
    table, key, columns = DATASETS[dataset]
    west, south, east, north = polygon.bounds

    # Bouding box reduces the candidate set
    # It does not determine final neighborhood membership
    query = sql.SQL("""
        SELECT {columns}
        FROM {table}
        WHERE longitude BETWEEN %s AND %s
          AND latitude BETWEEN %s AND %s
        ORDER BY {key}
        LIMIT %s
    """).format(
        columns=sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        table=sql.Identifier("public", table),
        key=sql.Identifier(key),
    )

    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                query,
                (
                    west,
                    east,
                    south,
                    north,
                    MAX_CANDIDATES + 1,
                ),
            )
            rows = await cursor.fetchall()

    if len(rows) > MAX_CANDIDATES:
        raise HTTPException(
            status_code=422, detail="Too many candidate records; pagination is required"
        )

    # Keep spatial processing off the async event loop.
    matched, ambiguous_count = await asyncio.to_thread(
        select_unique_members,
        rows,
        neighborhood_id,
        neighborhoods,
    )

    if len(matched) > MAX_RESULTS:
        raise HTTPException(
            status_code=422, detail="Too many matching records; pagination is required"
        )
    features = []

    for row in matched:
        properties = {
            column: row[column]
            for column in columns
            if column not in ("longitude", "latitude")
        }

        properties["neighborhood_id"] = neighborhood_id
        properties["membership_basis"] = "mapped_point"

        features.append(
            {
                "type": "Feature",
                "id": row[key],
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        row["longitude"],
                        row["latitude"],
                    ],
                },
                "properties": properties,
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "neighborhood_id": neighborhood_id,
            "count": len(features),
            "ambiguous_excluded": ambiguous_count,
            "membership_basis": "mapped_point",
        },
    }
