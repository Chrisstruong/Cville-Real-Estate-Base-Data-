from agents import function_tool
from agents.run_context import RunContextWrapper

from app.context import RequestContext
from app.services.properties import fetch_largest_properties

MAX_PROPERTY_LIMIT = 20


@function_tool(failure_error_function=None)
async def get_largest_properties(
    ctx: RunContextWrapper[RequestContext],
    limit: int = 5,
) -> dict:
    """
    Get the largest real-estate properties by lot square footage.

    Args:
        limit: Maximum number of properties to return.
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

    # Per-call guardrail
    requested_limit = limit
    limit = max(1, min(limit, MAX_PROPERTY_LIMIT))

    print("TOOL CALLED")
    print("requested limit:", requested_limit)
    print("limit:", limit)

    result = await fetch_largest_properties(
        limit=limit,
    )

    print("TOOL RESULT COUNT:", result["count"])

    return result
