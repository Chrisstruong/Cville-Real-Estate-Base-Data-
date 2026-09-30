# Database query functions that can later be exposed to the AI agent as tools
# queries for psycopg to access the database

from psycopg.rows import dict_row

from app.database.connection import pool


async def get_properties(limit: int = 20):
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                SELECT
                    parcel_number,
                    current_assessed_value,
                    object_id,
                    st_number,
                    st_name,
                    st_unit,
                    legal_description,
                    lot_sqft
                FROM real_estate_current_assessment
                ORDER BY parcel_number
                LIMIT %s;
                """,
                (limit,),
            )

            return await cursor.fetchall()


async def get_largest_properties(
    limit: int = 5,
):
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                SELECT
                    parcel_number,
                    current_assessed_value,
                    object_id,
                    st_number,
                    st_name,
                    st_unit,
                    legal_description,
                    lot_sqft
                FROM real_estate_current_assessment
                ORDER BY lot_sqft DESC
                LIMIT %s;
                """,
                (limit,),
            )

            return await cursor.fetchall()
