import argparse
import asyncio
import sys
from collections import Counter

from app.database.connection import pool
from app.services.crime_geometry import calculate_block_midpoint
from app.services.crime_location_strategy import choose_location_strategy
from app.utils.street_normalizer import normalize_street_name
from scripts.profile_crime_block_matches import (
    build_block_index,
    build_intersection_index,
    locate_intersection,
    merge_block_segments,
)

VERSION = "crime-geolocation-v1"


def locate_crime(
    street_name,
    block_number,
    official_streets,
    block_index,
    endpoints,
    invalid_streets,
):
    decision = choose_location_strategy(street_name, block_number, official_streets)

    if decision.reason == "intersection_pending":
        return locate_intersection(decision.streets, endpoints, invalid_streets)

    if decision.next_step != "match_block":
        return None, decision.reason or "strategy_excluded"

    key = (decision.streets[0], block_number)
    candidates = block_index.get(key, [])

    geometry, reason = merge_block_segments(candidates)

    if reason:
        return None, reason

    if geometry["coordinates"][0][:2] == geometry["coordinates"][-1][:2]:
        return None, "block_loop"
    latitude, longitude = calculate_block_midpoint(geometry)

    return {
        "latitude": latitude,
        "longitude": longitude,
        "mapping_method": (
            "merged_block_midpoint" if len(candidates) > 1 else "block_midpoint"
        ),
        "location_precision": "block_approximate",
        "gis_source_ids": sorted({objectid for objectid, _ in candidates}),
    }, None


async def backfill(apply=False):
    await pool.open()

    try:
        async with pool.connection() as conn:
            async with conn.transaction():
                # All reads use the same snapshot.
                # A dry run is also enforced as read-only by PostgreSQL.
                transaction_mode = (
                    "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"
                    if apply
                    else (
                        "SET TRANSACTION ISOLATION LEVEL " "REPEATABLE READ, READ ONLY"
                    )
                )
                await conn.execute(transaction_mode)

                result = await conn.execute(
                    """
                    SELECT record_id, street_name, block_number
                    FROM crime
                    WHERE latitude IS NULL
                      AND longitude IS NULL
                      AND geolocation_version IS DISTINCT FROM %s
                    ORDER BY record_id
                """,
                    (VERSION,),
                )
                crime_rows = await result.fetchall()

                result = await conn.execute("""
                    SELECT DISTINCT streetname
                    FROM official_cville_road_centerlines
                    WHERE streetname IS NOT NULL
                """)
                street_rows = await result.fetchall()

                result = await conn.execute("""
                    SELECT objectid, streetname, block_number, geometry
                    FROM official_cville_road_blocks
                """)
                block_rows = await result.fetchall()

                official_streets = {
                    normalized
                    for (street_name,) in street_rows
                    if (normalized := normalize_street_name(street_name))
                }

                # Build these once, rather than once per incident.
                block_index, skipped = build_block_index(block_rows)
                endpoints, invalid_streets = build_intersection_index(block_rows)

                outcomes = Counter()
                updates = []
                samples = []

                for crime_id, street_name, block_number in crime_rows:
                    location, reason = locate_crime(
                        street_name,
                        block_number,
                        official_streets,
                        block_index,
                        endpoints,
                        invalid_streets,
                    )

                    if location is None:
                        latitude = None
                        longitude = None
                        method = None
                        precision = None
                        source_ids = []
                        outcomes[f"unmapped:{reason}"] += 1
                    else:
                        latitude = location["latitude"]
                        longitude = location["longitude"]
                        method = location["mapping_method"]
                        precision = location["location_precision"]
                        source_ids = location["gis_source_ids"]
                        outcomes[f"mapped:{method}"] += 1

                    updates.append(
                        (
                            latitude,
                            longitude,
                            method,
                            precision,
                            source_ids,
                            reason,
                            VERSION,
                            crime_id,
                            VERSION,
                        )
                    )

                    if len(samples) < 5:
                        samples.append(
                            (
                                crime_id,
                                street_name,
                                latitude,
                                longitude,
                                method,
                                reason,
                            )
                        )

                mapped = sum(
                    count
                    for outcome, count in outcomes.items()
                    if outcome.startswith("mapped:")
                )

                print(f"Eligible incidents: {len(crime_rows):,}")
                print(f"Proposed mapped: {mapped:,}")
                print(f"Proposed unmapped: {len(crime_rows) - mapped:,}")
                print(f"GIS features missing street/block: {skipped:,}")

                for outcome, count in sorted(outcomes.items()):
                    print(f"  {outcome}: {count:,}")

                print("\nSample results:")
                for sample in samples:
                    print(sample)

                if not apply:
                    print("\nDry run complete. No records changed.")
                    return

                async with conn.cursor() as cursor:
                    await cursor.executemany(
                        """
                        UPDATE crime
                        SET latitude = %s,
                            longitude = %s,
                            mapping_method = %s,
                            location_precision = %s,
                            gis_source_ids = %s,
                            unmapped_reason = %s,
                            geolocation_version = %s,
                            geolocation_checked_at = CURRENT_TIMESTAMP
                        WHERE record_id = %s
                          AND latitude IS NULL
                          AND longitude IS NULL
                          AND geolocation_version IS DISTINCT FROM %s
                    """,
                        updates,
                    )

                    updated = cursor.rowcount

                if updated != len(updates):
                    raise RuntimeError(
                        f"Expected {len(updates)} updates, got {updated}. "
                        "Rolling back."
                    )

            # Reaching here means the transaction committed successfully.
            print(f"\nCommitted {updated:,} incident updates.")

    finally:
        await pool.close()


def main():
    parser = argparse.ArgumentParser(
        description="Calculate and optionally save crime coordinates."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Save results. Without this flag, only preview changes.",
    )
    args = parser.parse_args()

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(backfill(apply=args.apply))


if __name__ == "__main__":
    main()
