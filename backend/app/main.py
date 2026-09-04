from contextlib import asynccontextmanager

from fastapi import FastAPI
from psycopg.rows import dict_row

from app.database.connection import pool

@asynccontextmanager
async def lifespan(app:FastAPI):
    #Start database connection pool
    await pool.open()

    yield

    #Close database connection pool
    await pool.close()


app = FastAPI(
    title = "Charlottesville Real Estate AI API",
    lifespan=lifespan,
)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/db-health")
async def database_health():
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                SELECT COUNT(*) AS property_count
                FROM real_estate;
                """
            )

            result = await cursor.fetchone()
    
    return {
        "status": "ok",
        "property_count": result["property_count"],
    }