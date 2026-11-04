import json
import logging
from datetime import date
from functools import lru_cache
from typing import Annotated, Literal, Self

import psycopg
from fastapi import APIRouter, HTTPException, Query
from psycopg_pool import PoolTimeout
from pydantic import BaseModel, model_validator

from app.services.neighborhood_summary import fetch_neighborhood_summary
from app.services.neighborhoods import DATA_PATH, load_neighborhoods

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/neighborhoods",
    tags=["Neighborhoods"],
)


class OverviewFilters(BaseModel):
    crime_start_date: date | None = None
    crime_end_date: date | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        start = self.crime_start_date
        end = self.crime_end_date

        if (start is None) != (end is None):
            raise ValueError(
                "Provide both crime_start_date and crime_end_date," " or omit both."
            )

        if start is not None and end is not None:
            if start > end:
                raise ValueError("crime_start_date must be on or before crime_end_date")

            # The SQL uses the midnigjt after the inclusive end date
            if end == date.max:
                raise ValueError("crime_end_date must be earlier than  9999-12-31")
        return self


class NeighborhoodInfo(BaseModel):
    neighborhood_id: int
    name: str
    area_acres: float | None


class PropertySummary(BaseModel):
    property_count: int
    median_assessed_value: float | None
    total_assessed_value: float | None
    median_lot_sqft: float | None
    median_year_built: float | None

    assessed_value_valid_count: int
    assessed_value_excluded_count: int
    lot_sqft_valid_count: int
    lot_sqft_excluded_count: int


class CrimeSummary(BaseModel):
    crime_count: int
    crime_by_category: dict[str, int]
    crime_start_date: date | None
    crime_end_date: date | None
    missing_crime_category_count: int


class OverviewMetadata(BaseModel):
    membership_basis: Literal["mapped_point"]
    category_mapping_version: str

    crime_date_field: Literal["date_reported"]
    crime_date_timezone: Literal["America/New_York"]
    crime_date_range_inclusive: bool

    ambiguous_property_count: int
    ambiguous_crime_count: int

    area_status: Literal["not_calculated"]
    year_built_status: Literal["unavailable"]
    units: dict[str, str]
    notes: list[str]


class NeighborhoodOverview(BaseModel):
    neighborhood: NeighborhoodInfo
    properties: PropertySummary
    crimes: CrimeSummary
    metadata: OverviewMetadata


@lru_cache(maxsize=1)
def neighborhood_names() -> dict[int, str]:
    """Read names from the same boundary snapshot used for membership."""
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    return {
        feature["properties"]["OBJECTID"]: feature["properties"]["NAME"]
        for feature in data["features"]
    }


@router.get(
    "/{neighborhood_id}/overview",
    response_model=NeighborhoodOverview,
    responses={
        404: {"description": "Neighborhood not found"},
        422: {"description": "Invalid input or summary candidate limit exceeded"},
        500: {"description": "Unexpected overview processing failure"},
        503: {"description": "Database temporarily unavailable"},
    },
)
async def neighborhood_overview(
    neighborhood_id: int,
    filters: Annotated[OverviewFilters, Query()],
) -> NeighborhoodOverview:
    try:
        # Check existence before requesting a database connection.
        # Noninteger path values are rejected by FastAPI with HTTP 422.
        if neighborhood_id not in load_neighborhoods():
            raise HTTPException(
                status_code=404,
                detail="Neighborhood not found.",
            )

        name = neighborhood_names()[neighborhood_id]

        summary = await fetch_neighborhood_summary(
            neighborhood_id=neighborhood_id,
            date_start=filters.crime_start_date,
            date_end=filters.crime_end_date,
        )

        return NeighborhoodOverview(
            neighborhood=NeighborhoodInfo(
                neighborhood_id=neighborhood_id,
                name=name,
                # Area calculation is not implemented in the summary service.
                area_acres=None,
            ),
            properties=PropertySummary(
                property_count=summary["property_count"],
                median_assessed_value=summary["median_assessed_value"],
                total_assessed_value=summary["total_assessed_value"],
                median_lot_sqft=summary["median_lot_sqft"],
                median_year_built=None,
                assessed_value_valid_count=summary["assessed_value_valid_count"],
                assessed_value_excluded_count=summary["assessed_value_excluded_count"],
                lot_sqft_valid_count=summary["lot_sqft_valid_count"],
                lot_sqft_excluded_count=summary["lot_sqft_excluded_count"],
            ),
            crimes=CrimeSummary(
                crime_count=summary["crime_count"],
                crime_by_category=summary["crime_by_category"],
                crime_start_date=filters.crime_start_date,
                crime_end_date=filters.crime_end_date,
                missing_crime_category_count=summary["missing_crime_category_count"],
            ),
            metadata=OverviewMetadata(
                membership_basis=summary["membership_basis"],
                category_mapping_version=summary["category_mapping_version"],
                crime_date_field="date_reported",
                crime_date_timezone="America/New_York",
                crime_date_range_inclusive=True,
                ambiguous_property_count=summary["ambiguous_property_count"],
                ambiguous_crime_count=summary["ambiguous_crime_count"],
                area_status="not_calculated",
                year_built_status="unavailable",
                units={
                    "area_acres": "acres",
                    "median_assessed_value": "USD",
                    "total_assessed_value": "USD",
                    "median_lot_sqft": "sq ft",
                },
                notes=[
                    "Membership uses mapped points; crime locations "
                    "may be approximate.",
                    "Unmapped records and ambiguous boundary or overlap "
                    "assignments are excluded.",
                    "Crime counts represent source records, including "
                    "service calls and police activity.",
                    "Assessment and lot-size metrics exclude null, "
                    "nonpositive, and nonfinite values.",
                    "Omitting both dates includes all available reporting dates.",
                ],
            ),
        )

    except HTTPException:
        # Preserve intentional 404 and service-level 422 responses.
        raise

    except (PoolTimeout, psycopg.OperationalError):
        logger.exception(
            "Database unavailable for neighborhood %s",
            neighborhood_id,
        )
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Please try again.",
        ) from None

    except Exception:
        # Log details on the server without exposing SQL or credentials.
        logger.exception(
            "Overview failed for neighborhood %s",
            neighborhood_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to generate the neighborhood overview.",
        ) from None
