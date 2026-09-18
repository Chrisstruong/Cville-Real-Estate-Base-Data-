from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query
from psycopg.rows import dict_row  # Return query results as dictionary-like rows

from agents import set_default_openai_key
from app.config import settings
from app.services.agent_service import run_real_estate_agent

from pydantic import BaseModel, Field, field_validator

from pydantic import (
    BaseModel,
    Field,
)  # FastAPI use Basemodel to define and validate structured request

from app.database.connection import pool
from app.services.properties import (
    fetch_properties,
    fetch_largest_properties,
)


# Manage the database connection pool during the application's lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start database connection pool
    await pool.open()
    # start receiving requests
    set_default_openai_key(settings.openai_api_key)  # Set openai key
    yield

    # Close database connection pool
    await pool.close()


# Check whether the FastAPI application is running
app = FastAPI(
    title="Charlottesville Real Estate AI API",
    lifespan=lifespan,
)


# Check whether the application can connect to and query the database
@app.get("/health")
async def health():
    return {"status": "healthy"}


# create an url for checking up on database health
@app.get("/db-health")
async def database_health():
    async with pool.connection() as conn:  # Connect to the database
        async with conn.cursor(
            row_factory=dict_row
        ) as cursor:  # cursor lets excute sql queries
            await cursor.execute("""
                SELECT COUNT(*) AS property_count
                FROM real_estate;
                """)

            result = await cursor.fetchone()  # Store response from SQL queries

    return {
        "status": "ok",
        "property_count": result["property_count"],
    }


# Send requests -> /services/properties.py/fetch_properties -> database/queries.py/get_properties
# Annotated let add extra information to parameters
@app.get("/api/properties/")
async def get_properties_endpoint(
    # define fastAPI parameters for limit
    limit: Annotated[
        int, Query(ge=1, le=100)
    ] = 10,  # integer, 1 <= queries <= 100, default value is 10
):
    return await fetch_properties(limit)


@app.get("/api/properties/largest")
async def largest_properties(
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
    tax_type: str | None = None,
):
    return await fetch_largest_properties(limit=limit, tax_type=tax_type)


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Message cannot be empty.")

        return value


@app.post("/api/chat")
async def chat(request: ChatRequest):
    answer = await run_real_estate_agent(request.message)

    return {"answer": answer}
