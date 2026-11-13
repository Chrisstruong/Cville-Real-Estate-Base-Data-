from dataclasses import asdict
from typing import Literal

from app.chat_context import StreetMapContext
from app.services.street_filter_updates import apply_street_filter_update

from agents import function_tool
from agents.run_context import RunContextWrapper
from fastapi import HTTPException
from pydantic import ValidationError

from app.context import RequestContext
from app.map_actions import CrimeFilters, ShowStreetCrimesAction
from app.services.street_crimes import fetch_street_crimes
from app.services.streets import resolve_street_name


@function_tool(failure_error_function=None)
async def get_street_crimes(
    ctx: RunContextWrapper[RequestContext],
    street_name: str,
    start_date: str | None = None,
    end_date: str | None = None,
    category: str | None = None,
) -> dict:
    """Retrieve verified street-associated crime statistics.

    Args:
        street_name: Street name explicitly supplied by the user.
        start_date: Inclusive reporting date, YYYY-MM-DD, or null.
        end_date: Inclusive reporting date, YYYY-MM-DD, or null.
        category: An application crime-category key, or null for all categories.
    """
    context = ctx.context
    context.street_tool_calls += 1
    context.pending_map_action = None

    # This checkpoint supports one street lookup per request.
    if context.street_tool_calls > 1:
        return {
            "status": "limit_reached",
            "message": "Only one street lookup is supported per request.",
        }

    try:
        filters = CrimeFilters(
            start_date=start_date,
            end_date=end_date,
            category=category,
        )
    except ValidationError:
        return {
            "status": "invalid_filters",
            "message": (
                "Provide valid YYYY-MM-DD dates together, with start before "
                "or equal to end, and a supported category key."
            ),
        }

    resolution = await resolve_street_name(street_name)

    if resolution.status != "resolved" or resolution.street is None:
        return {
            "status": resolution.status,
            "candidates": [asdict(street) for street in resolution.candidates],
            "message": (
                "Ask the user to specify an official street name. "
                "Do not choose a suggestion automatically."
            ),
        }

    return await _lookup_street(
        context,
        resolution.street.street_id,
        filters,
    )


async def _lookup_street(
    context: RequestContext,
    street_id: str,
    filters: CrimeFilters,
) -> dict:
    try:
        data = await fetch_street_crimes(
            street_id,
            filters,
        )
    except HTTPException as exc:
        if exc.status_code not in (404, 422):
            raise

        return {
            "status": "unavailable",
            "message": str(exc.detail),
        }

    geometry_available = bool(data["road_blocks"]["features"])

    if geometry_available and context.street_tool_calls == 1:
        context.pending_map_action = ShowStreetCrimesAction(
            type="SHOW_STREET_CRIMES",
            street_id=data["street"]["street_id"],
            filters=filters,
        )

    return {
        "status": "success",
        "street": data["street"],
        "filters": data["filters"],
        "summary": data["summary"],
        "metadata": data["metadata"],
        "map_action_available": context.pending_map_action is not None,
        "message": (
            "Street data was retrieved. Map display requires frontend "
            "execution and is not confirmed by this tool."
        ),
    }


@function_tool(failure_error_function=None)
async def update_street_crime_filters(
    ctx: RunContextWrapper[RequestContext],
    category_operation: Literal["keep", "set", "clear"],
    dates_operation: Literal["keep", "set", "clear"],
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Update filters on the verified active street.

    Args:
        category_operation: Keep, replace, or clear the active category.
        dates_operation: Keep, replace, or clear the active reporting dates.
        category: Category key for set; otherwise null.
        start_date: Inclusive YYYY-MM-DD start for set; otherwise null.
        end_date: Inclusive YYYY-MM-DD end for set; otherwise null.
    """
    context = ctx.context
    context.street_tool_calls += 1
    context.pending_map_action = None

    # Shared limit across explicit lookups and follow-up lookups.
    if context.street_tool_calls > 1:
        return {
            "status": "limit_reached",
            "message": "Only one street lookup is supported per request.",
        }

    active = context.conversation.map_context

    if not isinstance(active, StreetMapContext):
        return {
            "status": "street_required",
            "message": (
                "No street is active. Ask the user to specify a street. "
                "Do not restore a street from conversation history."
            ),
        }

    try:
        filters = apply_street_filter_update(
            active.filters,
            category_operation=category_operation,
            category=category,
            dates_operation=dates_operation,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError:
        return {
            "status": "invalid_filters",
            "message": (
                "The filter update is invalid. Use keep or clear with null "
                "values, or set with a supported category or valid date pair."
            ),
        }

    return await _lookup_street(
        context,
        active.street_id,
        filters,
    )
