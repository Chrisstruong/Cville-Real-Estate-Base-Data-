import asyncio
import sys

from app.database.connection import pool
from app.utils.street_normalizer import normalize_street_name

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    await pool.open()

    async with pool.connection() as conn:
        # Get unique real-estate streets
        result = await conn.execute("""
           SELECT DISTINCT st_name
           FROM real_estate_current_assessment
           WHERE st_name IS NOT NULL 
            
            """)
        real_estate_rows = await result.fetchall()

        # Get unique crime streets
        result = await conn.execute("""
            
            SELECT DISTINCT street_name
            FROM crime
            WHERE street_name IS NOT NULL
            """)
        crime_rows = await result.fetchall()

        # Get every property so we can measure property coverage
        result = await conn.execute("""
            
            SELECT st_name
            FROM real_estate_current_assessment
            WHERE st_name IS NOT NULL
            """)
        property_rows = await result.fetchall()

    await pool.close()

    real_estate_streets = {normalize_street_name(row[0]) for row in real_estate_rows}

    crime_streets = {normalize_street_name(row[0]) for row in crime_rows}

    matched_streets = real_estate_streets & crime_streets
    unmatched_streets = real_estate_streets - crime_streets

    matched_properties = sum(
        1 for row in property_rows if normalize_street_name(row[0]) in crime_streets
    )

    total_streets = len(real_estate_streets)
    total_properties = len(property_rows)

    street_match_rate = matched_streets.__len__() / total_streets * 100
    property_coverage = matched_properties / total_properties * 100
    print("\n===== STREET NORMALIZATION METRICS =====")
    print(f"Real-estate streets: {total_streets}")
    print(f"Matched streets: {len(matched_streets)}")
    print(f"Unmatched streets: {len(unmatched_streets)}")
    print(f"Street match rate: {street_match_rate:.2f}%")

    print("\n===== PROPERTY COVERAGE =====")
    print(f"Total properties: {total_properties}")
    print(f"Matched properties: {matched_properties}")
    print(f"Unmatched properties: {total_properties - matched_properties}")
    print(f"Property coverage: {property_coverage:.2f}%")

    print("\n===== UNMATCHED STREETS =====")
    for street in sorted(unmatched_streets):
        print(street)


if __name__ == "__main__":
    asyncio.run(main())
