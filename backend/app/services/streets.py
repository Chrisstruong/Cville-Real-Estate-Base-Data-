from dataclasses import dataclass
from difflib import get_close_matches
from typing import Literal
from urllib.parse import quote

from app.database.connection import pool
from app.utils.street_normalizer import normalize_street_name


@dataclass(frozen=True)
class Street:
    street_id: str
    name: str


@dataclass(frozen=True)
class StreetResolution:
    status: Literal["resolved", "clarification_required", "not_found"]
    street: Street | None
    candidates: tuple[Street, ...]


def make_street_id(normalized_name: str) -> str:
    """Application identifier, not an official GIS primary key."""
    return f"street:{quote(normalized_name, safe='')}"


async def load_street_catalog() -> dict[str, Street]:
    """Resolve names from the official centerline table."""
    async with pool.connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT DISTINCT streetname
                FROM public.official_cville_road_centerlines
                WHERE streetname IS NOT NULL
                  AND btrim(streetname) <> ''
                ORDER BY streetname
                """)
            rows = await cursor.fetchall()

    catalog: dict[str, Street] = {}

    for (source_name,) in rows:
        normalized = normalize_street_name(source_name)

        if normalized:
            catalog[normalized] = Street(
                street_id=make_street_id(normalized),
                name=normalized,
            )

    return catalog


def resolve_from_catalog(
    query: str,
    catalog: dict[str, Street],
) -> StreetResolution:
    """Only exact normalized matches resolve automatically."""
    normalized = normalize_street_name(query)

    if not normalized:
        return StreetResolution(
            status="not_found",
            street=None,
            candidates=(),
        )

    exact = catalog.get(normalized)

    if exact is not None:
        return StreetResolution(
            status="resolved",
            street=exact,
            candidates=(),
        )

    # Suggestions are never treated as confirmed matches.
    query_tokens = set(normalized.split())

    matching_names = sorted(
        name for name in catalog if query_tokens.issubset(set(name.split()))
    )

    if not matching_names:
        matching_names = get_close_matches(
            normalized,
            sorted(catalog),
            n=5,
            cutoff=0.65,
        )

    candidates = tuple(catalog[name] for name in matching_names[:5])

    return StreetResolution(
        status="clarification_required" if candidates else "not_found",
        street=None,
        candidates=candidates,
    )


async def resolve_street_name(query: str) -> StreetResolution:
    catalog = await load_street_catalog()
    return resolve_from_catalog(query, catalog)


async def resolve_street_id(street_id: str) -> Street | None:
    """An incoming identifier must exist in the official catalog."""
    catalog = await load_street_catalog()

    return next(
        (street for street in catalog.values() if street.street_id == street_id),
        None,
    )
