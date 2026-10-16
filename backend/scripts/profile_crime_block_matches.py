import asyncio
import math
import sys
from collections import Counter, defaultdict
from pyproj import Transformer

from app.database.connection import pool
from app.services.crime_location_strategy import choose_location_strategy
from app.utils.street_normalizer import normalize_street_name

# WGS84 longitude/latitude -> UTM zone 17N, for this Charlottesville dataset.
TO_METERS = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32617",
    always_xy=True,
)

TO_LON_LAT = Transformer.from_crs(
    "EPSG:32617",
    "EPSG:4326",
    always_xy=True,
)


def calculate_block_midpoint(geometry):
    if not has_usable_line_geometry(geometry):
        raise ValueError("Expected a usable lineString")

    points = [
        TO_METERS.transform(point[0], point[1], errcheck=True)
        for point in geometry["coordinates"]
    ]

    lengths = [
        math.hypot(x2 - x1, y2 - y1) for (x1, y1), (x2, y2) in zip(points, points[1:])
    ]

    total_length = sum(lengths)

    if not math.isfinite(total_length) or total_length <= 0:
        raise ValueError("Road geometry has no usable length")

    halfway = total_length / 2
    distance_walked = 0.0

    for start, end, length in zip(points, points[1:], lengths):
        if length == 0:
            continue

        if distance_walked + length >= halfway:
            fraction = (halfway - distance_walked) / length

            x = start[0] + fraction * (end[0] - start[0])
            y = start[1] + fraction * (end[1] - start[1])

            longitude, latitude = TO_LON_LAT.transform(x, y, errcheck=True)
            return latitude, longitude
        distance_walked += length
    raise ValueError("Could not locate midpoint")


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
                """)
            street_rows = await result.fetchall()

            result = await conn.execute("""
                SELECT objectid, streetname, block_number, geometry
                FROM official_cville_road_blocks
                """)
            block_rows = await result.fetchall()

    return crime_rows, street_rows, block_rows


def build_block_index(block_rows):
    block_index = defaultdict(list)
    skipped = 0

    for objectid, street_name, block_number, geometry in block_rows:
        normalized = normalize_street_name(street_name)

        if not normalized or block_number is None:
            skipped += 1
            continue

        key = (normalized, block_number)
        block_index[key].append((objectid, geometry))
    return block_index, skipped


def has_usable_line_geometry(geometry):
    if not isinstance(geometry, dict):
        return False
    if geometry.get("type") != "LineString":
        return False

    coordinates = geometry.get("coordinates")

    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return False

    for point in coordinates:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            return False

        longitude, latitude = point[:2]

        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in (longitude, latitude)
        ):
            return False

        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            return False
    first_point = coordinates[0][:2]

    return any(point[:2] != first_point for point in coordinates[1:])


def analyze_matches(crime_rows, street_rows, block_rows):
    official_streets = {
        normalized
        for (street_name,) in street_rows
        if (normalized := normalize_street_name(street_name))
    }

    block_index, skipped = build_block_index(block_rows)
    mapped_locations = []

    outcomes = Counter()
    examples = defaultdict(list)
    eligible = 0

    for street_name, block_number in crime_rows:
        decision = choose_location_strategy(street_name, block_number, official_streets)
        candidates = []

        if decision.next_step != "match_block":
            outcome = decision.reason or "strategy_excluded"
        else:
            eligible += 1
            key = (decision.streets[0], block_number)
            candidates = block_index.get(key, [])

            if not candidates:
                outcome = "block_not_found"
            elif len(candidates) > 1:
                outcome = "multiple_block_segments"
            elif not has_usable_line_geometry(candidates[0][1]):
                outcome = "unsupported_or_invalid_geometry"
            else:
                objectid, geometry = candidates[0]
                latitude, longitude = calculate_block_midpoint(geometry)

                mapped_locations.append(
                    {
                        "street_name": street_name,
                        "block_number": block_number,
                        "gis_source_id": objectid,
                        "latitude": latitude,
                        "longitude": longitude,
                        "mapping_method": "block_midpoint",
                        "location_precision": "block_approximate",
                    }
                )

                outcome = "mapped_block"
        outcomes[outcome] += 1

        example = (
            street_name,
            block_number,
            tuple(objectid for objectid, _ in candidates),
        )

        if len(examples[outcome]) < 5 and example not in examples[outcome]:
            examples[outcome].append(example)
    # These checks run after the entire loop
    total = len(crime_rows)

    assert sum(outcomes.values()) == total
    assert eligible == sum(
        outcomes[label]
        for label in (
            "block_not_found",
            "multiple_block_segments",
            "unsupported_or_invalid_geometry",
            "mapped_block",
        )
    )
    assert len(mapped_locations) == outcomes["mapped_block"]

    return {
        "total": total,
        "eligible": eligible,
        "outcomes": outcomes,
        "examples": examples,
        "skipped_gis_features": skipped,
        "mapped_locations": mapped_locations,
    }


def print_report(report):
    total = report["total"]
    eligible = report["eligible"]
    mapped = report["outcomes"]["mapped_block"]

    def percentage(count, denominator):
        return f"{count / denominator:.2%}" if denominator else "N/A"

    print(f"\nTotal crime records: {total:,}")
    print(f"Eligible for block matching: {eligible:,}")
    print("GIS features missing street/block: " f"{report['skipped_gis_features']:,}")

    print("\nOutcomes - percentages of all crime records")
    for outcome, count in sorted(report["outcomes"].items()):
        print(f"{outcome}: {count:,} ({percentage(count, total)})")

    print("\nBaseline mapping coverage")
    print(f"Mapped records: {mapped:,}")
    print(f"Unmapped records: {total - mapped:,}")
    print(f"Among all records: {percentage(mapped, total)}")
    print(f"Among eligible records: {percentage(mapped, eligible)}")

    print("\nExamples")
    for outcome, examples in sorted(report["examples"].items()):
        print(f"\n{outcome}")
        for street_name, block_number, objectids in examples:
            print(
                f" street={street_name!r}, "
                f"block={block_number!r}, "
                f"GIS IDs={objectids}"
            )
        print("\nSample calculated coordinates")
        for location in report["mapped_locations"][:5]:
            print(
                f"{location['block_number']} block of "
                f"{location['street_name']}: "
                f"latitude={location['latitude']:.6f}, "
                f"longitude={location['longitude']:.6f}, "
                f"GIS ID={location['gis_source_id']}"
            )

    print("\nCoordinates calculated in memory only.")
    print("Locations represent approximate road-block midpoints.")
    print("No database records changed.")


async def main():
    try:
        await pool.open()
        crime_rows, street_rows, block_rows = await fetch_data()
    finally:
        await pool.close()

    report = analyze_matches(crime_rows, street_rows, block_rows)
    print_report(report)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
