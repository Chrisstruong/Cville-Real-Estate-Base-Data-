from scripts.profile_crime_block_matches import (
    build_intersection_index,
    locate_intersection,
)


def make_line(*points):
    return {
        "type": "LineString",
        "coordinates": [list(point) for point in points],
    }


a = (-78.50, 38.03)
b = (-78.49, 38.03)
c = (-78.49, 38.04)

block_rows = [
    (10, "MAIN ST", 100, make_line(a, b)),
    (20, "SIDE ST", 100, make_line(b, c)),
]

endpoints, invalid_streets = build_intersection_index(block_rows)

assert endpoints["MAIN ST"][b] == {10}
assert endpoints["SIDE ST"][b] == {20}
assert not invalid_streets

shared = endpoints["MAIN ST"].keys() & endpoints["SIDE ST"].keys()

assert shared == {b}

print("Intersection index test passed.")

# 1. One shared endpoint: accept.
location, reason = locate_intersection(
    ("MAIN ST", "SIDE ST"),
    endpoints,
    invalid_streets,
)

assert reason is None
assert location["longitude"] == b[0]
assert location["latitude"] == b[1]
assert location["gis_source_ids"] == [10, 20]


# 2. Missing street geometry: leave unmapped.
location, reason = locate_intersection(
    ("MAIN ST", "MISSING ST"),
    endpoints,
    invalid_streets,
)

assert location is None
assert reason == "intersection_no_shared_node"


# 3. Two shared endpoints: ambiguous, so reject.
ambiguous_rows = block_rows + [
    (30, "SIDE ST", 200, make_line(a, c)),
]

ambiguous_endpoints, invalid = build_intersection_index(ambiguous_rows)

location, reason = locate_intersection(
    ("MAIN ST", "SIDE ST"),
    ambiguous_endpoints,
    invalid,
)

assert location is None
assert reason == "intersection_multiple_nodes"


# 4. Incomplete geometry: do not claim a unique junction.
location, reason = locate_intersection(
    ("MAIN ST", "SIDE ST"),
    endpoints,
    {"SIDE ST"},
)

assert location is None
assert reason == "intersection_invalid_geometry"

print("Intersection location tests passed.")

block_rows = [
    (10, "MAIN ST", 100, make_line(a, b)),
    (20, "SIDE ST", 100, make_line(b, c)),
]

endpoints, invalid_streets = build_intersection_index(block_rows)

assert endpoints["MAIN ST"][b] == {10}
assert endpoints["SIDE ST"][b] == {20}
assert not invalid_streets

shared = endpoints["MAIN ST"].keys() & endpoints["SIDE ST"].keys()

assert shared == {b}

print("Intersection index test passed.")
