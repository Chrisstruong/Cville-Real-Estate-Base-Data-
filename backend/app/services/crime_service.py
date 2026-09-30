from app.database.connection import pool
from app.utils.street_normalizer import normalize_street_name, extract_streets


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
