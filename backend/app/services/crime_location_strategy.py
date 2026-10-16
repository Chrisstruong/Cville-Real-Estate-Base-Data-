from dataclasses import dataclass
from app.utils.street_normalizer import normalize_street_name, extract_streets


@dataclass(frozen=True)
class LocationDecision:
    next_step: str
    streets: tuple[str, ...]
    reason: str | None


def choose_location_strategy(
    street_name: str | None,
    block_number: int | None,
    official_streets: set[str],
) -> LocationDecision:
    streets = tuple(
        dict.fromkeys(street for street in extract_streets(street_name) if street)
    )

    if not streets:
        return LocationDecision(
            next_step="leave_unmapped",
            streets=streets,
            reason="unknown_location",
        )
    missing_streets = [street for street in streets if street not in official_streets]

    if missing_streets:
        return LocationDecision(
            next_step="review",
            streets=streets,
            reason="street_not_found",
        )
    if len(streets) > 1:
        return LocationDecision(
            next_step="review",
            streets=streets,
            reason="intersection_pending",
        )
    if block_number is None:
        return LocationDecision(
            next_step="review",
            streets=streets,
            reason="missing_block",
        )
    return LocationDecision(
        next_step="match_block",
        streets=streets,
        reason=None,
    )
