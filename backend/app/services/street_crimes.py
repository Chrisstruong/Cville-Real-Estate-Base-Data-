import math

from fastapi import HTTPException
from psycopg.rows import dict_row

from app.database.connection import pool
from app.map_actions import CrimeFilters
from app.services.crime_categories import CATEGORIES, category_for_offense
from app.services.crime_geometry import has_usable_line_geometry
from app.services.neighborhood_summary import DATE_FILTER
from app.services.streets import make_street_id
from app.utils.street_normalizer import extract_streets, normalize_street_name

MAX_NAMES = 50_000
MAX_RECORDS = 10_000
MAX_ROAD_BLOCKS = 10_000


def feature_collection(features):
    return {
        "type": "FeatureCollection",
        "features": features,
    }


def usable_point(longitude, latitude):
    values = (longitude, latitude)

    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in values
    ):
        return False

    return -180 <= longitude <= 180 and -90 <= latitude <= 90


async def bounded_rows(cursor, query, params, limit):
    await cursor.execute(query, {**params, "limit": limit + 1})
    rows = await cursor.fetchall()

    if len(rows) > limit:
        raise HTTPException(
            status_code=422,
            detail="Street query exceeds the supported result limit.",
        )

    return rows


async def fetch_street_crimes(
    street_id: str,
    filters: CrimeFilters,
) -> dict:
    # Revalidate even when called internally rather than through an endpoint.
    filters = CrimeFilters.model_validate(filters.model_dump())

    async with pool.connection() as conn:
        async with conn.transaction():
            await conn.execute(
                "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
            )
            await conn.execute("SET LOCAL statement_timeout = '15s'")

            async with conn.cursor(row_factory=dict_row) as cursor:
                official_names = await bounded_rows(
                    cursor,
                    """
                    SELECT DISTINCT streetname
                    FROM public.official_cville_road_centerlines
                    WHERE streetname IS NOT NULL
                    ORDER BY streetname
                    LIMIT %(limit)s
                    """,
                    {},
                    MAX_NAMES,
                )

                street_name = next(
                    (
                        normalized
                        for row in official_names
                        if (normalized := normalize_street_name(row["streetname"]))
                        and make_street_id(normalized) == street_id
                    ),
                    None,
                )

                if street_name is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Official street not found.",
                    )

                block_names = await bounded_rows(
                    cursor,
                    """
                    SELECT DISTINCT streetname
                    FROM public.official_cville_road_blocks
                    WHERE streetname IS NOT NULL
                    ORDER BY streetname
                    LIMIT %(limit)s
                    """,
                    {},
                    MAX_NAMES,
                )

                matching_block_names = [
                    row["streetname"]
                    for row in block_names
                    if normalize_street_name(row["streetname"]) == street_name
                ]

                blocks = await bounded_rows(
                    cursor,
                    """
                    SELECT objectid, block_number, geometry
                    FROM public.official_cville_road_blocks
                    WHERE streetname = ANY(%(names)s::text[])
                    ORDER BY objectid
                    LIMIT %(limit)s
                    """,
                    {"names": matching_block_names},
                    MAX_ROAD_BLOCKS,
                )

                date_params = {
                    "date_start": filters.start_date,
                    "date_end": filters.end_date,
                }

                reported_names = await bounded_rows(
                    cursor,
                    """
                    SELECT DISTINCT street_name
                    FROM public.crime
                    WHERE street_name IS NOT NULL
                      AND """
                    + DATE_FILTER
                    + """
                    ORDER BY street_name
                    LIMIT %(limit)s
                    """,
                    date_params,
                    MAX_NAMES,
                )

                matching_reported_names = [
                    row["street_name"]
                    for row in reported_names
                    if street_name in extract_streets(row["street_name"])
                ]

                # Read each crime once; never join it to road segments.
                rows = await bounded_rows(
                    cursor,
                    """
                    SELECT record_id, offense, longitude, latitude,
                           location_precision, mapping_method
                    FROM public.crime
                    WHERE street_name = ANY(%(names)s::text[])
                      AND """
                    + DATE_FILTER
                    + """
                    ORDER BY record_id
                    LIMIT %(limit)s
                    """,
                    {
                        **date_params,
                        "names": matching_reported_names,
                    },
                    MAX_RECORDS,
                )

    # All database reads above share one consistent snapshot.
    road_features = []
    excluded_block_count = 0

    for block in blocks:
        geometry = block["geometry"]

        if not has_usable_line_geometry(geometry):
            excluded_block_count += 1
            continue

        road_features.append(
            {
                "type": "Feature",
                "id": block["objectid"],
                "geometry": {
                    "type": "LineString",
                    "coordinates": [point[:2] for point in geometry["coordinates"]],
                },
                "properties": {
                    "objectid": block["objectid"],
                    "block_number": block["block_number"],
                },
            }
        )

    crime_features = []
    record_ids = []
    counts = dict.fromkeys(CATEGORIES, 0)
    seen_ids = set()

    for row in rows:
        record_id = row["record_id"]

        if record_id in seen_ids:
            continue
        seen_ids.add(record_id)

        category = category_for_offense(row["offense"])

        if filters.category is not None and category != filters.category:
            continue

        record_ids.append(record_id)
        counts[category] += 1

        if not usable_point(row["longitude"], row["latitude"]):
            continue

        crime_features.append(
            {
                "type": "Feature",
                "id": record_id,
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        row["longitude"],
                        row["latitude"],
                    ],
                },
                "properties": {
                    "record_id": record_id,
                    "category": category,
                    "location_precision": (row["location_precision"] or "unknown"),
                    "mapping_method": row["mapping_method"],
                },
            }
        )

    total = len(record_ids)
    mapped = len(crime_features)

    return {
        "street": {
            "street_id": street_id,
            "name": street_name,
        },
        "filters": filters.model_dump(mode="json"),
        "summary": {
            "associated_record_count": total,
            "mapped_record_count": mapped,
            "unmapped_record_count": total - mapped,
            "records_by_category": counts,
        },
        "record_ids": record_ids,
        "crimes": feature_collection(crime_features),
        "road_blocks": feature_collection(road_features),
        "metadata": {
            "membership_basis": "reported_street_name",
            "crime_date_field": "date_reported",
            "crime_date_timezone": "America/New_York",
            "crime_date_range_inclusive": True,
            "category_mapping_version": "1",
            "road_geometry_source": "official_cville_road_blocks",
            "road_geometry_status": (
                "unavailable"
                if not road_features
                else "partial" if excluded_block_count else "available"
            ),
            "excluded_road_block_count": excluded_block_count,
            "notes": [
                "Street association uses normalized reported names.",
                "Intersection records may be associated with multiple streets.",
                "Counts represent source records, including service calls "
                "and police activity.",
                "Mapped points use existing coordinates; their accuracy "
                "is not established by coordinate validation.",
                "No coordinates are generated for unmapped records.",
                "Road geometry represents available official road blocks, "
                "not guaranteed complete street coverage.",
            ],
        },
    }
