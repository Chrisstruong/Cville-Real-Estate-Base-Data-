from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.services.crime_categories import CATEGORIES


class CrimeFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: date | None
    end_date: date | None
    category: str | None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_calendar_date(cls, value):
        if value is None or type(value) is date:
            return value

        if not isinstance(value, str):
            raise ValueError("Dates must use YYYY-MM-DD.")

        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            raise ValueError("Dates must use YYYY-MM-DD.") from None

        if parsed.isoformat() != value:
            raise ValueError("Dates must use YYYY-MM-DD.")

        return parsed

    @field_validator("category", mode="before")
    @classmethod
    def validate_category(cls, value):
        if value is not None:
            if not isinstance(value, str) or value not in CATEGORIES:
                raise ValueError("Unsupported crime category.")
        return value

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if (self.start_date is None) != (self.end_date is None):
            raise ValueError("Provide both dates or neither.")

        if self.start_date is not None and self.end_date is not None:
            if self.start_date > self.end_date:
                raise ValueError("Start date must not follow end date.")

            if self.end_date == date.max:
                raise ValueError("End date must be earlier than 9999-12-31.")

        return self


class ShowStreetCrimesAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["SHOW_STREET_CRIMES"]
    street_id: str = Field(strict=True, min_length=1, max_length=200)
    filters: CrimeFilters

    @field_validator("street_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("Street identifier must not contain outer whitespace.")

        return value


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str
    total_time_seconds: float = Field(ge=0)
    contract_version: Literal[1] = 1

    # Keep actions disabled until official street resolution is implemented.
    map_action: None = None


class ChatTextDelta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["text_delta"] = "text_delta"
    text: str


class ChatComplete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["complete"] = "complete"
    contract_version: Literal[1] = 1
    map_action: ShowStreetCrimesAction | None = None


class ChatError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["error"] = "error"
    code: Literal["agent_failed"] = "agent_failed"
    message: str = "The assistant could not finish the request. Please retry."
