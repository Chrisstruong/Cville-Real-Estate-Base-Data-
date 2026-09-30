from app.database.queries import get_properties
from app.database.queries import get_largest_properties
from app.services.crime_service import get_crime_streets
from app.utils.street_normalizer import normalize_street_name

MAX_PROPERTY_LIMIT = 20


# 10 is the default value when fetch properties
async def fetch_properties(limit: int = 10):
    limit = max(1, min(limit, MAX_PROPERTY_LIMIT))

    properties = await get_properties(limit)
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
# tax_type can be string. default value is None if not provided
async def fetch_largest_properties(
    limit: int = 5,
    tax_type: str | None = None,
):
    # Service-layer guardrail
    limit = max(1, min(limit, MAX_PROPERTY_LIMIT))

    properties = await get_largest_properties(
        limit=limit,
        tax_type=tax_type,
    )

    crime_streets = await get_crime_streets()

    cleaned_properties = []

    for row in properties:
        item = dict(row)

    return {
        "count": len(cleaned_properties),
        "properties": cleaned_properties,
    }
