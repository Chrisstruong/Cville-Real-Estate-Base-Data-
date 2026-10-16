import asyncio
import sys
from collections import Counter, defaultdict

from app.database.connection import pool
from app.utils.street_normalizer import (
    extract_streets,
    normalize_street_name,
)
from app.services.crime_location_strategy import choose_location_strategy


async def fetch_data():
    async with pool.connection() as conn:
        async with conn.transaction():
            await conn.execute(
                "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
            )

            result = await conn.execute("""
                SELECT street_name, block_number
                FROM crime
                """)
            crime_rows = await result.fetchall()

            result = await conn.execute("""
                SELECT DISTINCT streetname
                FROM official_cville_road_centerlines
                WHERE streetname IS NOT NULL
                AND TRIM(streetname) <> ''
                """)
            gis_rows = await result.fetchall()
    return crime_rows, gis_rows


def classify_location(street_name, block_number):
    streets = list(
        dict.fromkeys(street for street in extract_streets(street_name) if street)
    )

    if not streets:
        category = "Unknown"
    elif len(streets) > 1:
        category = "intersection_candidate"
    elif block_number is not None:
        category = "street_with_block"
    else:
        category = "street_only"
    return category, streets


def analyze_locations(crime_rows, gis_rows):
    official_streets = {
        normalized
        for (street_name,) in gis_rows
        if (normalized := normalize_street_name(street_name))
    }

    categories = Counter()
    validation = Counter()
    strategy_counts = Counter()
    examples = defaultdict(list)

    with_block = 0

    for street_name, block_number in crime_rows:
        decision = choose_location_strategy(
            street_name,
            block_number,
            official_streets,
        )
        label = decision.reason or decision.next_step
        strategy_counts[label] += 1
        if block_number is not None:
            with_block += 1

        category, streets = classify_location(street_name, block_number)
        categories[category] += 1

        matched_count = sum(street in official_streets for street in streets)

        if not streets:
            gis_status = "no_usable_street"
        elif matched_count == len(streets):
            gis_status = "all_streets_found"
        elif matched_count > 0:
            gis_status = "some_streets_found"
        else:
            gis_status = "no_streets_found"

        validation[gis_status] += 1

        example = (street_name, block_number, streets)
        example_groups = [category]

        if gis_status != "all_streets_found":
            example_groups.append("needs_gis_review")

        for group in example_groups:
            if len(examples[group]) < 5 and example not in examples[group]:
                examples[group].append(example)

    total = len(crime_rows)

    assert sum(categories.values()) == total
    assert sum(validation.values()) == total
    assert sum(strategy_counts.values()) == total

    return {
        "total": total,
        "with_block": with_block,
        "without_block": total - with_block,
        "categories": categories,
        "validation": validation,
        "examples": examples,
        "strategy_counts": strategy_counts,
    }


def print_report(report):
    total = report["total"]

    def show_count(label, count):
        percentage = f"{count / total:.2%}" if total else "N/A"
        print(f"{label}: {count:,} ({percentage})")

    print(f"\nTotal crime records: {total:,}")
    show_count("With block number", report["with_block"])
    show_count("Without block number", report["without_block"])

    print("\nLocation categories:")
    for category in (
        "street_with_block",
        "street_only",
        "intersection_candidate",
        "Unknown",
    ):
        show_count(category, report["categories"][category])

    print("\nGIS street-name validation")
    for status in (
        "all_streets_found",
        "some_streets_found",
        "no_streets_found",
        "no_usable_street",
    ):
        show_count(status, report["validation"][status])

    print("\nExamples for inspection")
    for group, examples in sorted(report["examples"].items()):
        print(f"\n{group}:")
        for raw_street, block, streets in examples:
            print(f" raw={raw_street!r}," f"block={block!r}," f"parsed={streets!r}")

    print("\nAll percentages use total crime records.")
    print("GIS name matches do not establish coordinates.")

    print("\nLocation strategy decisions")
    for label, count in sorted(report["strategy_counts"].items()):
        show_count(label, count)


async def main():
    try:
        await pool.open()
        crime_rows, gis_rows = await fetch_data()
    finally:
        await pool.close()
    report = analyze_locations(crime_rows, gis_rows)
    print_report(report)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
