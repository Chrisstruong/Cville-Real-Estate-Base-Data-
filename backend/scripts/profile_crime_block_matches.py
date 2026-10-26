import asyncio
import sys
from collections import Counter, defaultdict
from app.services.crime_geometry import (
    calculate_block_midpoint,
    has_usable_line_geometry,
)

from app.database.connection import pool
from app.services.crime_location_strategy import choose_location_strategy
from app.utils.street_normalizer import normalize_street_name


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


def endpoint_key(point):
    """Create a comparable longitude/latitude endpoint."""
    longitude, latitude = point[:2]
    return round(longitude, 7), round(latitude, 7)


def merge_block_segments(candidates):
    """
    candidates: [(objectid, geometry), ...]

    Returns:
        (merged_geometry, None) when safe to merge
        (None, reason) otherwise
    """

    if not candidates:
        return None, "block_not_found"

    if any(not has_usable_line_geometry(geometry) for _, geometry in candidates):
        return None, "unsupported_or_invalid_geometry"

    if len(candidates) == 1:
        return candidates[0][1], None

    edges = []
    adjacency = defaultdict(list)
    seen_shapes = set()

    for _, geometry in candidates:
        points = geometry["coordinates"]
        shape = tuple(endpoint_key(point) for point in points)

        # A -> B and B -> A describe the same shape
        shape_key = min(shape, shape[::-1])

        if shape_key in seen_shapes:
            continue

        seen_shapes.add(shape_key)

        start = shape[0]
        end = shape[-1]

        if start == end:
            return None, "block_loop"

        edge_id = len(edges)
        edges.append(points)

        adjacency[start].append(edge_id)
        adjacency[end].append(edge_id)
    # More than two attached segments creates a branch
    if any(len(edge_ids) > 2 for edge_ids in adjacency.values()):
        return None, "block_branch"

    ends = sorted(point for point, edge_ids in adjacency.items() if len(edge_ids) == 1)

    if len(ends) != 2:
        return None, "block_disconnected_or_loop"

    current = ends[0]
    visited = set()
    merged_points = []

    while True:
        available = [
            edge_id for edge_id in adjacency[current] if edge_id not in visited
        ]

        if not available:
            break

        edge_id = available[0]
        visited.add(edge_id)

        points = edges[edge_id]

        # Orient the segment so it starts where we are
        if endpoint_key(points[0]) != current:
            points = points[::-1]

        if not merged_points:
            merged_points.extend(points)
        else:
            # The shared endpoint is already in the merged line
            merged_points.extend(points[1:])

        current = endpoint_key(points[-1])

    # An open chain could coexist with a separate loop
    # Checking every edge prevents silently ignoring that loop
    if len(visited) != len(edges):
        return None, "block_disconnected_or_loop"

    return {
        "type": "LineString",
        "coordinates": merged_points,
    }, None


def analyze_matches(
    crime_rows,
    street_rows,
    block_rows,
    *,
    merge_segments=False,
):
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

            if len(candidates) > 1 and not merge_segments:
                geometry = None
                reason = "multiple_block_segments"
            else:
                geometry, reason = merge_block_segments(candidates)

            if reason:
                outcome = reason
            else:
                latitude, longitude = calculate_block_midpoint(geometry)

                mapped_locations.append(
                    {
                        "street_name": street_name,
                        "block_number": block_number,
                        "gis_source_ids": [objectid for objectid, _ in candidates],
                        "latitude": latitude,
                        "longitude": longitude,
                        "mapping_method": (
                            "merged_block_midpoint"
                            if len(candidates) > 1
                            else "block_midpoint"
                        ),
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
            "block_branch",
            "block_loop",
            "block_disconnected_or_loop",
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


def build_intersection_index(block_rows):
    endpoints = defaultdict(lambda: defaultdict(set))
    invalid_streets = set()

    for objectid, street_name, block_number, geometry in block_rows:
        street = normalize_street_name(street_name)

        if not street:
            continue

        if not has_usable_line_geometry(geometry):
            invalid_streets.add(street)
            continue

        coordinates = geometry["coordinates"]

        # Only the start and end of each road segment
        for point in (coordinates[0], coordinates[-1]):
            key = endpoint_key(point)
            endpoints[street][key].add(objectid)
    return endpoints, invalid_streets


def locate_intersection(streets, endpoints, invalid_streets):
    # This version supports exactly two distinct streets.
    if len(streets) != 2 or streets[0] == streets[1]:
        return None, "intersection_street_count"

    if any(street in invalid_streets for street in streets):
        return None, "intersection_invalid_geometry"

    left = endpoints.get(streets[0], {})
    right = endpoints.get(streets[1], {})

    shared = left.keys() & right.keys()

    if not shared:
        return None, "intersection_no_shared_node"

    if len(shared) > 1:
        return None, "intersection_multiple_nodes"

    # There is exactly one point, so selecting it is unambiguous.
    point = next(iter(shared))
    longitude, latitude = point

    source_ids = left[point] | right[point]

    return {
        "latitude": latitude,
        "longitude": longitude,
        "gis_source_ids": sorted(source_ids),
        "mapping_method": "shared_gis_endpoint",
        "location_precision": "intersection_approximate",
    }, None


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
                f"GIS IDs={location['gis_source_ids']}"
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

    baseline = analyze_matches(
        crime_rows,
        street_rows,
        block_rows,
    )

    improved = analyze_matches(
        crime_rows,
        street_rows,
        block_rows,
        merge_segments=True,
    )

    before = baseline["outcomes"]["mapped_block"]
    after = improved["outcomes"]["mapped_block"]

    print(f"Baseline mapped: {before:,}")
    print(f"Improved mapped: {after:,}")
    print(f"Additional mapped: {after - before:,}")

    print_report(improved)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
