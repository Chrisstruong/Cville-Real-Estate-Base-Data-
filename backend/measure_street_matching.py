import asyncio
import sys

from app.database.connection import pool
from app.utils.street_normalizer import (
    normalize_street_name,
    extract_streets,
)

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

        # Get official Charlottesville GIS streets
        result = await conn.execute("""
        SELECT DISTINCT streetname
        FROM official_cville_road_centerlines
        WHERE streetname IS NOT NULL
        AND TRIM(streetname) <> ''
        """)
        official_rows = await result.fetchall()
        """
        GIS contains both "HILLSDALE DR" and "HILLSDALE DR ".
        Normalization strips the trailing whitespace, reducing
        631 raw unique GIS street names to 630 normalized names.
        """

        # Get unique crime streets
        result = await conn.execute("""
            
            SELECT DISTINCT street_name
            FROM crime
            WHERE street_name IS NOT NULL AND TRIM(street_name) <> ''
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

    # --------------
    # Normalize datasets: road_centerlines, real estate, and crime streets

    official_streets = {normalize_street_name(row[0]) for row in official_rows}

    # real_estate_streets = {"MAIN ST", "OAK ST", "PRESTON AVE"}
    real_estate_streets = {normalize_street_name(row[0]) for row in real_estate_rows}

    # crime_streets = {"MAIN ST", "OAK ST", "MARKET ST"}
    crime_streets = set()

    for row in crime_rows:
        crime_streets.update(extract_streets(row[0]))

    # ---------------------------------------------------------
    # Validate against official Charlottesville GIS
    # ---------------------------------------------------------

    # Real-estate validation against official GIS
    valid_real_estate_streets = real_estate_streets & official_streets
    invalid_real_estate_streets = real_estate_streets - official_streets

    # Crime validation against official GIS
    valid_crime_streets = crime_streets & official_streets
    invalid_crime_streets = crime_streets - official_streets
    real_estate_validity_rate = (
        len(valid_real_estate_streets) / len(real_estate_streets) * 100
    )

    crime_validity_rate = len(valid_crime_streets) / len(crime_streets) * 100
    # ---------------------------------------------------------
    # Measure overlap between real-estate and crime datasets
    # ---------------------------------------------------------

    matched_streets = real_estate_streets & crime_streets

    unmatched_real_estate_streets = real_estate_streets - crime_streets

    unmatched_crime_streets = crime_streets - real_estate_streets

    street_match_rate = len(matched_streets) / len(real_estate_streets) * 100

    # ---------------------------------------------------------
    # Property coverage
    # ---------------------------------------------------------

    properties_on_crime_streets = sum(
        1 for row in property_rows if normalize_street_name(row[0]) in crime_streets
    )

    total_properties = len(property_rows)

    property_coverage_rate = properties_on_crime_streets / total_properties * 100

    # ---------------------------------------------------------
    # Official GIS validation results
    # ---------------------------------------------------------

    print("\n===== OFFICIAL GIS VALIDATION =====")
    print(f"Official GIS streets: {len(official_streets)}")

    print("\n===== REAL-ESTATE VALIDATION =====")
    print(f"Real-estate streets: {len(real_estate_streets)}")
    print(f"Valid: {len(valid_real_estate_streets)}")
    print(f"Not found in GIS: {len(invalid_real_estate_streets)}")
    print(f"Validity rate: {real_estate_validity_rate:.2f}%")

    print("\n===== CRIME VALIDATION =====")
    print(f"Crime streets: {len(crime_streets)}")
    print(f"Valid: {len(valid_crime_streets)}")
    print(f"Not found in GIS: {len(invalid_crime_streets)}")
    print(f"Validity rate: {crime_validity_rate:.2f}%")

    # ---------------------------------------------------------
    # Existing dataset-overlap metrics
    # ---------------------------------------------------------

    print("\n===== REAL-ESTATE / CRIME OVERLAP =====")
    print(f"Real-estate streets: {len(real_estate_streets)}")
    print(f"Matched streets: {len(matched_streets)}")
    print(f"Not found in crime data: " f"{len(unmatched_real_estate_streets)}")
    print(f"Overlap rate: {street_match_rate:.2f}%")

    print("\n===== PROPERTIES ON STREET CRIME  =====")
    print(f"Total properties: {total_properties}")
    print(f"Matched properties: {properties_on_crime_streets}")
    print(f"Unmatched properties: " f"{total_properties - properties_on_crime_streets}")
    print(f"Property coverage: {property_coverage_rate:.2f}%")

    # ---------------------------------------------------------
    # Streets requiring investigation
    # ---------------------------------------------------------

    print("\n===== REAL-ESTATE STREETS NOT FOUND IN GIS =====")
    print(f"Count: {len(invalid_real_estate_streets)}")

    for street in sorted(invalid_real_estate_streets):
        print(street)

    print("\n===== CRIME STREETS NOT FOUND IN GIS =====")
    print(f"Count: {len(invalid_crime_streets)}")

    for street in sorted(invalid_crime_streets):
        print(street)

    print("\n===== CRIME STREETS NOT FOUND IN REAL ESTATE =====")
    print(f"Count: {len(unmatched_crime_streets)}")

    # for street in sorted(unmatched_crime_streets):
    #     print(street)


if __name__ == "__main__":
    asyncio.run(main())
