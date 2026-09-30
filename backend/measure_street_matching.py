import asyncio
import sys

from app.database.connection import pool
from app.utils.street_normalizer import (
    normalize_street_name,
    extract_streets,
)
from collections import Counter

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

        # Get every property
        result = await conn.execute("""
            
            SELECT st_name
            FROM real_estate_current_assessment
            WHERE st_name IS NOT NULL
            """)
        property_rows = await result.fetchall()

    await pool.close()

    # real_estate_streets = {"MAIN ST", "OAK ST", "PRESTON AVE"}
    real_estate_streets = {normalize_street_name(row[0]) for row in real_estate_rows}

    # crime_streets = {"MAIN ST", "OAK ST", "MARKET ST"}
    crime_streets = set()
    for row in crime_rows:
        streets = extract_streets(row[0])
        for street in streets:
            crime_streets.add(street)

    # Streets exist in both datasets
    matched_streets = real_estate_streets & crime_streets
    # Real-estate streets that don't appear in crime data
    unmatched_real_estate_streets = real_estate_streets - crime_streets

    # Crime streets that don't match a real-estate street
    unmatched_crime_streets = crime_streets - real_estate_streets

    properties_on_crime_streets = sum(
        1 for row in property_rows if normalize_street_name(row[0]) in crime_streets
    )

    total_streets = len(real_estate_streets)
    total_properties = len(property_rows)

    street_match_rate = len(matched_streets) / total_streets * 100
    # Percentage of properties whose streets appear in crime dataset
    properties_on_crime_streets_rate = (
        properties_on_crime_streets / total_properties * 100
    )
    print("\n===== STREET NORMALIZATION METRICS =====")
    print(f"Real-estate streets: {total_streets}")
    print(f"Matched streets: {len(matched_streets)}")
    print(f"Unmatched streets: {len(unmatched_real_estate_streets)}")
    print(f"Street match rate: {street_match_rate:.2f}%")

    print("\n===== PROPERTY COVERAGE =====")
    print(f"Total properties: {total_properties}")
    print(f"Matched properties: {properties_on_crime_streets}")
    print(f"Unmatched properties: {total_properties - properties_on_crime_streets}")
    print(f"Property coverage: {properties_on_crime_streets_rate:.2f}%")

    print("\n===== UNMATCHED REAL-ESTATE STREETS =====")
    print(f"Count: {len(unmatched_real_estate_streets)}")
    for street in sorted(unmatched_real_estate_streets):
        print(street)

    print("\n===== UNMATCHED CRIME STREETS =====")
    print(f"Count: {len(unmatched_crime_streets)}")
    for street in sorted(unmatched_crime_streets)[:200]:
        print(street)

    unmatched_property_counts = Counter()
    for row in property_rows:
        normalized_street = normalize_street_name(row[0])

        if normalized_street not in crime_streets:
            unmatched_property_counts[normalized_street] += 1

    print("\n===== UNMATCHED PROPERTY DISTRIBUTION =====")
    print(f"Count: {sum(unmatched_property_counts.values())}")

    for street, count in unmatched_property_counts.most_common():
        print(f"{street}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
