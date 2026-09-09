from agents import function_tool

from app.services.properties import fetch_largest_properties

@function_tool(failure_error_function=None)
async def get_largest_properties(
    limit: int = 5,
    tax_type: str | None = None,
) -> dict:
    """
    Get the largest real-estate properties by acreage.
    
    Args:
        limit: Maximum number of properties to return.
        tax_type: Optional tax type such as "Taxable" or "Exempt".
    """
    normalized_tax_type = tax_type
    
    if tax_type:
        value = tax_type.strip().lower()
        
        if value in {"exempt", "tax-exempt", "tax exempt"}:
            normalized_tax_type = "Exempt"
        elif value in {"taxable", "tax-paying", "tax paying"}:
            normalized_tax_type = "Taxable"
    
    print("TOOL CALLED")
    print("limit:", limit)
    print("tax_type:", normalized_tax_type)
    
    result = await fetch_largest_properties(
        limit=limit,
        tax_type=normalized_tax_type,
    )
    
    print("TOOL RESULT:")
    print(result)
    
    return result

