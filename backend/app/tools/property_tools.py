from agents import function_tool

from app.context import RequestContext
from app.services.properties import fetch_largest_properties
from agents.run_context import RunContextWrapper

MAX_PROPERTY_LIMIT = 20


@function_tool(failure_error_function=None)
async def get_largest_properties(
    ctx: RunContextWrapper[RequestContext],
    limit: int = 5,
    tax_type: str | None = None,
) -> dict:
    """
    Get the largest real-estate properties by acreage.

    Args:
        limit: Maximum number of properties to return.
        tax_type: Optional tax type such as "Taxable" or "Exempt".
    """

    # 1. Get the per-request context
    request_context = ctx.context

    # 2. Deterministic request-level guardrail
    if request_context.property_tool_calls >= request_context.max_property_tool_calls:
        print("REQUEST GUARDRAIL BLOCKED TOOL CALL")

        return {
            "error": "Property lookup limit reached for this request",
            "count": 0,
            "properties": [],
        }
    # 3.Count this tool call
    request_context.property_tool_calls += 1

    # 4.Existing per-call limit logic
    # Guardrail: never allow a request below 1 or above 20
    requested_limit = limit
    limit = max(1, min(limit, MAX_PROPERTY_LIMIT))
    normalized_tax_type = tax_type
    # Normalized agent input to sql as "Exempt" and "Taxable" only
    if tax_type:
        value = tax_type.strip().lower()

        if value in {"exempt", "tax-exempt", "tax exempt"}:  # Taxbale, Exempt
            normalized_tax_type = "Exempt"
        elif value in {"taxable", "tax-paying", "tax paying"}:
            normalized_tax_type = "Taxable"

    print("TOOL CALLED")
    print("requested limit:", requested_limit)
    print("limit:", limit)
    print("tax_type:", normalized_tax_type)

    result = await fetch_largest_properties(
        limit=limit,
        tax_type=normalized_tax_type,
    )

    print("TOOL RESULT COUNT:", result["count"])

    return result
