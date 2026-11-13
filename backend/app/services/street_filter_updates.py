from typing import Literal

from app.map_actions import CrimeFilters

FilterOperation = Literal["keep", "set", "clear"]


def apply_street_filter_update(
    current: CrimeFilters,
    *,
    category_operation: FilterOperation,
    category: str | None,
    dates_operation: FilterOperation,
    start_date: str | None,
    end_date: str | None,
) -> CrimeFilters:
    allowed = {"keep", "set", "clear"}

    if category_operation not in allowed or dates_operation not in allowed:
        raise ValueError("Unsupported filter operation.")

    current = CrimeFilters.model_validate(current.model_dump())

    if category_operation == "set":
        if category is None:
            raise ValueError("Setting a category requires a category value.")
        next_category = category
    else:
        if category is not None:
            raise ValueError(
                "Category must be null when keeping or clearing the category."
            )

        next_category = current.category if category_operation == "keep" else None

    if dates_operation == "set":
        if start_date is None or end_date is None:
            raise ValueError("Setting dates requires both start and end dates.")

        next_start = start_date
        next_end = end_date
    else:
        if start_date is not None or end_date is not None:
            raise ValueError("Dates must be null when keeping or clearing dates.")

        if dates_operation == "keep":
            next_start = current.start_date
            next_end = current.end_date
        else:
            next_start = None
            next_end = None

    return CrimeFilters(
        start_date=next_start,
        end_date=next_end,
        category=next_category,
    )
