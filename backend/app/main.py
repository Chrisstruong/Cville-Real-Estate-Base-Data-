from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query
from psycopg.rows import dict_row # Return query results as dictionary-like rows

from app.database.connection import pool
from app.services.properties import fetch_properties

# Manage the database connection pool during the application's lifespan
@asynccontextmanager
async def lifespan(app:FastAPI):
    #Start database connection pool
    await pool.open()
    # start receiving requests
    yield

    #Close database connection pool
    await pool.close()

# Check whether the FastAPI application is running
app = FastAPI(
    title = "Charlottesville Real Estate AI API",
    lifespan=lifespan,
)

# Check whether the application can connect to and query the database
@app.get("/health")
async def health():
    return {"status": "healthy"}

# create an url for checking up on database health
@app.get("/db-health")
async def database_health():
    async with pool.connection() as conn: #Connect to the database
        async with conn.cursor(row_factory=dict_row) as cursor: #cursor lets excute sql queries
            await cursor.execute(
                """
                SELECT COUNT(*) AS property_count
                FROM real_estate;
                """
            )

            result = await cursor.fetchone()  #Store response from SQL queries
    
    return {
        "status": "ok",
        "property_count": result["property_count"],
    }

@app.get("/api/properties/")
async def get_properties_endpoint(
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return await fetch_properties(limit)