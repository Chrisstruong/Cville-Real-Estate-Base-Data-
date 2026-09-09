from app.database.queries import get_properties

async def fetch_properties(limit: int = 10):
    properties = await get_properties(limit)
    
    return {
        "count": len(properties),
        "properties": properties,
    }