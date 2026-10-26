"""Shared geometry validation and length-based road midpoint calculation."""
import math
from pyproj import Transformer

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


