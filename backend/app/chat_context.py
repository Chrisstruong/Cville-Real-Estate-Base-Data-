from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.map_actions import CrimeFilters


class HistoryMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("History content cannot be blank.")

        return value


class CityMapContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["city"] = "city"


class NeighborhoodMapContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["neighborhood"]
    neighborhood_id: int = Field(strict=True, ge=1)


class StreetMapContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["street"]
    street_id: str = Field(strict=True, min_length=1, max_length=200)
    filters: CrimeFilters

    @field_validator("street_id")
    @classmethod
    def validate_street_id(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("Street identifier cannot contain outer whitespace.")

        return value


MapContext = Annotated[
    CityMapContext | NeighborhoodMapContext | StreetMapContext,
    Field(discriminator="mode"),
]


class ConversationContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    history: list[HistoryMessage] = Field(
        default_factory=list,
        max_length=8,
    )
    map_context: MapContext = Field(default_factory=CityMapContext)
