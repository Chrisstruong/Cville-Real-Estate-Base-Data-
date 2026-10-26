import asyncio
import sys

from app.database.connection import pool


async def report_coverage():
    await pool.open()

    try:
        async with pool.connection() as conn:
            async with conn.transaction():
                # Keep every count consistent and prevent accidental writes.
                await conn.execute("""
                    SET TRANSACTION
                    ISOLATION LEVEL REPEATABLE READ,
                    READ ONLY
                """)

                result = await conn.execute("""
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (
                            WHERE latitude IS NOT NULL
                              AND longitude IS NOT NULL
                        ) AS mapped,
                        COUNT(*) FILTER (
                            WHERE latitude IS NULL
                              AND longitude IS NULL
                        ) AS unmapped,
                        COUNT(*) FILTER (
                            WHERE (latitude IS NULL)
                               <> (longitude IS NULL)
                        ) AS incomplete
                    FROM crime
                """)

                total, mapped, unmapped, incomplete = await result.fetchone()

                result = await conn.execute("""
                    SELECT
                        COALESCE(mapping_method, 'missing_method'),
                        COALESCE(location_precision, 'missing_precision'),
                        COUNT(*)
                    FROM crime
                    WHERE latitude IS NOT NULL
                      AND longitude IS NOT NULL
                    GROUP BY mapping_method, location_precision
                    ORDER BY COUNT(*) DESC
                """)
                methods = await result.fetchall()

                result = await conn.execute("""
                    SELECT
                        COALESCE(unmapped_reason, 'not_processed_or_no_reason'),
                        COUNT(*)
                    FROM crime
                    WHERE latitude IS NULL
                      AND longitude IS NULL
                    GROUP BY unmapped_reason
                    ORDER BY COUNT(*) DESC
                """)
                reasons = await result.fetchall()

                result = await conn.execute("""
                    SELECT
                        COALESCE(geolocation_version, 'not_versioned'),
                        COUNT(*)
                    FROM crime
                    GROUP BY geolocation_version
                    ORDER BY COUNT(*) DESC
                """)
                versions = await result.fetchall()

                result = await conn.execute("""
                    SELECT
                        COUNT(*) FILTER (
                            WHERE latitude IS NOT NULL
                              AND longitude IS NOT NULL
                              AND (
                                  NOT (latitude BETWEEN -90 AND 90)
                                  OR NOT (longitude BETWEEN -180 AND 180)
                              )
                        ) AS invalid_coordinates,
                        COUNT(*) FILTER (
                            WHERE latitude IS NOT NULL
                              AND longitude IS NOT NULL
                              AND (
                                  mapping_method IS NULL
                                  OR location_precision IS NULL
                                  OR COALESCE(
                                      cardinality(gis_source_ids), 0
                                  ) = 0
                              )
                        ) AS missing_mapping_metadata,
                        COUNT(*) FILTER (
                            WHERE latitude IS NOT NULL
                              AND longitude IS NOT NULL
                              AND unmapped_reason IS NOT NULL
                        ) AS mapped_with_failure_reason,
                        COUNT(*) FILTER (
                            WHERE latitude IS NULL
                              AND longitude IS NULL
                              AND unmapped_reason IS NULL
                        ) AS unmapped_without_reason
                    FROM crime
                """)

                (
                    invalid_coordinates,
                    missing_mapping_metadata,
                    mapped_with_failure_reason,
                    unmapped_without_reason,
                ) = await result.fetchone()

        def percent(count):
            return f"{count / total:.2%}" if total else "N/A"

        print("Persisted crime mapping coverage")
        print(f"Total records: {total:,}")
        print(f"Mapped: {mapped:,} ({percent(mapped)})")
        print(f"Unmapped: {unmapped:,} ({percent(unmapped)})")
        print(f"Incomplete coordinate pairs: {incomplete:,}")

        print("\nMapping method and precision")
        for method, precision, count in methods:
            print(
                f"  {method} / {precision}: "
                f"{count:,} ({percent(count)} of all records)"
            )

        print("\nUnmapped reasons")
        for reason, count in reasons:
            print(f"  {reason}: {count:,} ({percent(count)})")

        print("\nGeolocation versions")
        for version, count in versions:
            print(f"  {version}: {count:,}")

        checks = {
            "Incomplete coordinate pairs": incomplete,
            "Invalid coordinate ranges": invalid_coordinates,
            "Mapped records missing method, precision, or GIS sources": missing_mapping_metadata,
            "Mapped records with an unmapped reason": mapped_with_failure_reason,
            "Unmapped records without a reason": unmapped_without_reason,
        }

        print("\nData quality checks")
        for label, count in checks.items():
            print(f"  {label}: {count:,}")

        counts_consistent = (
            total == mapped + unmapped + incomplete
            and sum(count for _, _, count in methods) == mapped
            and sum(count for _, count in reasons) == unmapped
            and sum(count for _, count in versions) == total
        )

        if not counts_consistent:
            raise RuntimeError("Coverage counts do not reconcile.")

        if any(checks.values()):
            raise RuntimeError("Data quality checks found records requiring review.")

        print("\nAll checks passed. No database records changed.")

    finally:
        await pool.close()


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(report_coverage())


if __name__ == "__main__":
    main()
