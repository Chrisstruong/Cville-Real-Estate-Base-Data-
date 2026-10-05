import json
from urllib.parse import urlencode
from urllib.request import urlopen
import time
import os
from psycopg_pool import AsyncConnectionPool

from app.database.connection import pool
import asyncio
import sys

admin_pool = AsyncConnectionPool(
    conninfo=(
        "host=localhost "
        "dbname=charlottesville_real_estate "
        "user=postgres "
        f"password={os.environ['POSTGRES_ADMIN_PASSWORD']}"
    ),
    open=False,
)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

GIS_QUERY_URL = (
    "https://gisweb.charlottesville.org/"
    "cvgisweb/rest/services/OpenData_1/MapServer/74/query"
)

BATCH_SIZE = 1000


def fetch_parcel_batch(
    offset: int,
    max_retries: int = 3,
) -> list[dict]:

    params = {
        "where": "1=1",
        "outFields": "ParcelNumber,StreetNumber,StreetName",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
        "resultOffset": offset,
        "resultRecordCount": BATCH_SIZE,
        "orderByFields": "OBJECTID",
    }

    url = f"{GIS_QUERY_URL}?{urlencode(params)}"

    for attempt in range(1, max_retries + 1):
        try:
            with urlopen(url, timeout=30) as response:
                data = json.load(response)

            return data.get("features", [])

        except (ConnectionResetError, TimeoutError, OSError) as error:
            print(
                f"Request failed at offset {offset} "
                f"(attempt {attempt}/{max_retries}): {error}"
            )

            if attempt == max_retries:
                raise

            wait_seconds = attempt * 2

            print(f"Retrying in {wait_seconds} seconds...")
            time.sleep(wait_seconds)

    return []


def fetch_all_parcels() -> list[dict]:
    all_features = []
    offset = 0

    while True:
        print(f"Fetching records starting at offset {offset}...")

        features = fetch_parcel_batch(offset)

        print(f"Received {len(features)} records.")

        if not features:
            break

        all_features.extend(features)
        time.sleep(0.25)

        if len(features) < BATCH_SIZE:
            break

        offset += BATCH_SIZE

    return all_features


async def main():
    gis_features = fetch_all_parcels()

    gis_parcels = {
        feature["properties"]["ParcelNumber"].strip()
        for feature in gis_features
        if feature.get("properties", {}).get("ParcelNumber")
    }

    await pool.open()

    try:
        database_parcels = await fetch_database_parcels()

        matched = database_parcels & gis_parcels
        unmatched = database_parcels - gis_parcels

        coverage = len(matched) / len(database_parcels) * 100 if database_parcels else 0

        print("\n===== PARCEL GIS MATCHING =====")
        print(f"Database parcels: {len(database_parcels)}")
        print(f"GIS parcels: {len(gis_parcels)}")
        print(f"Matched: {len(matched)}")
        print(f"Unmatched: {len(unmatched)}")
        print(f"Coordinate coverage: {coverage:.2f}%")

        if unmatched:
            print("\n===== DATABASE PARCELS NOT FOUND IN GIS =====")
            for parcel_number in sorted(unmatched):
                print(parcel_number)

        # Safety check before modifying PostgreSQL
        if coverage < 99:
            print("\nCoverage below 99%. Database was NOT updated.")
            return
        await admin_pool.open()

        try:
            updated = await update_property_coordinates(gis_features)
        finally:
            await admin_pool.close()

        print("\n===== COORDINATE IMPORT =====")
        print(f"GIS coordinate records prepared: {updated}")

    finally:
        await pool.close()


async def fetch_database_parcels() -> set[str]:
    async with pool.connection() as conn:
        result = await conn.execute("""
            SELECT parcel_number
            FROM real_estate_current_assessment
        """)

        rows = await result.fetchall()

    return {row[0].strip() for row in rows if row[0]}


# Update property coordinates in the database based on GIS features
async def update_property_coordinates(gis_features: list[dict]) -> int:
    updates = []

    for feature in gis_features:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry")

        parcel_number = properties.get("ParcelNumber")

        if not parcel_number or not geometry:
            continue

        coordinates = geometry.get("coordinates")

        if not coordinates or len(coordinates) < 2:
            continue

        longitude = coordinates[0]
        latitude = coordinates[1]

        updates.append(
            (
                latitude,
                longitude,
                parcel_number.strip(),
            )
        )

    async with admin_pool.connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.executemany(
                """
                UPDATE real_estate_current_assessment
                SET latitude = %s,
                    longitude = %s
                WHERE parcel_number = %s
                """,
                updates,
            )

        await conn.commit()

    return len(updates)


if __name__ == "__main__":
    asyncio.run(main())
