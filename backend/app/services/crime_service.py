from app.database.connection import pool
from app.utils.street_normalizer import normalize_street_name, extract_streets
from app.database.queries import get_map_crimes, get_crime_by_record_id


async def get_crime_streets() -> set[str]:
    async with pool.connection() as conn:
        result = await conn.execute("""
            SELECT DISTINCT street_name
            FROM crime
            WHERE street_name IS NOT NULL
            """)

        rows = await result.fetchall()

    crime_streets = set()

    for row in rows:
        streets = extract_streets(row[0])

        for street in streets:
            crime_streets.add(street)
    return crime_streets


async def property_street_has_crime(street_name: str) -> bool:
    normalized_street = normalize_street_name(street_name)

    crime_streets = await get_crime_streets()

    return normalized_street in crime_streets


async def fetch_map_crimes():
    rows = await get_map_crimes()

    features = [
        {
            "type": "Feature",
            "id": row["record_id"],
            "geometry": {
                "type": "Point",
                "coordinates": [
                    row["longitude"],
                    row["latitude"],
                ],
            },
            "properties": {
                "record_id": row["record_id"],
                "location_precision": row["location_precision"],
            },
        }
        for row in rows
    ]

    return {
        "type": "FeatureCollection",
        "features": features,
    }


async def fetch_crime_by_record_id(record_id: int):
    return await get_crime_by_record_id(record_id)
