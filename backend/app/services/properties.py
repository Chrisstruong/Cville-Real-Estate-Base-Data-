from app.database.queries import get_properties
from app.database.queries import get_largest_properties

async def fetch_properties(limit: int = 10):
    properties = await get_properties(limit)
    
    return {
        "count": len(properties),
        "properties": properties,
    }
    
    
async def fetch_largest_properties(
    limit: int = 5,
    tax_type: str | None = None,
):
    properties = await get_largest_properties(
        limit=limit,
        tax_type=tax_type,
    )
    return {
        "count": len(properties),
        "properties": properties,
    }