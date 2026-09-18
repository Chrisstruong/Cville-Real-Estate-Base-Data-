from app.database.queries import get_properties
from app.database.queries import get_largest_properties

MAX_PROPERTY_LIMIT = 20


# 10 is the default value when fetch properties
async def fetch_properties(limit: int = 10):
    limit = max(1, min(limit, MAX_PROPERTY_LIMIT))
    properties = await get_properties(limit)

    return {
        "count": len(properties),
        "properties": properties,
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
    cleaned_properties = []
    for property in properties:
        item = dict(property)

        if item["acreage"] is not None:
            item["acreage"] = float(item["acreage"])

        cleaned_properties.append(item)

    return {
        "count": len(cleaned_properties),
        "properties": cleaned_properties,
    }
