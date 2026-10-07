from app.database.queries import (
    get_properties,
    get_largest_properties,
    get_map_properties,
    get_all_map_properties,
    get_property_by_parcel_number,
)
from app.services.crime_service import get_crime_streets
from app.utils.street_normalizer import normalize_street_name

MAX_PROPERTY_LIMIT = 20


# 10 is the default value when fetch properties
async def fetch_properties(limit: int = 10):
    limit = max(1, min(limit, MAX_PROPERTY_LIMIT))

    properties = await get_properties(limit)

    # build normalized crime street set once per request
    crime_streets = await get_crime_streets()

    cleaned_properties = []

    for row in properties:
        item = dict(row)

        normalized_street = normalize_street_name(item["st_name"])

        item["normalized_street"] = normalized_street
        item["has_crime_records"] = normalized_street in crime_streets
        cleaned_properties.append(item)
    return {
        "count": len(cleaned_properties),
        "properties": cleaned_properties,
    }


# Default value: 5
async def fetch_largest_properties(
    limit: int = 5,
):
    # Service-layer guardrail
    limit = max(1, min(limit, MAX_PROPERTY_LIMIT))

    properties = await get_largest_properties(
        limit=limit,
    )

    crime_streets = await get_crime_streets()

    cleaned_properties = []

    for row in properties:
        item = dict(row)

        normalized_street = normalize_street_name(item["st_name"])

        item["normalized_street"] = normalized_street
        item["has_crime_records"] = normalized_street in crime_streets

        cleaned_properties.append(item)

    return {
        "count": len(cleaned_properties),
        "properties": cleaned_properties,
    }


async def fetch_map_properties(limit: int = 10):
    properties = await get_all_map_properties()

    return {
        "count": len(properties),
        "properties": properties,
    }


async def fetch_all_map_properties():
    properties = await get_all_map_properties()

    return {
        "count": len(properties),
        "properties": properties,
    }


async def fetch_property_by_parcel_number(parcel_number: str):
    return await get_property_by_parcel_number(parcel_number)
