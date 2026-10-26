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


async def get_map_properties(limit: int = 10):
    limit = max(1, min(limit, 20))

    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                SELECT 
                    parcel_number,
                    current_assessed_value,
                    st_number,
                    st_name,
                    st_unit,
                    lot_sqft,
                    latitude,
                    longitude
                FROM real_estate_current_assessment
                WHERE latitude IS NOT NULL
                AND longitude IS NOT NULL
                ORDER BY parcel_number
                LIMIT %s;
                """,
                (limit,),
            )
            return await cursor.fetchall()


async def get_all_map_properties():
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute("""
                SELECT
                    parcel_number,
                    latitude,
                    longitude
                FROM real_estate_current_assessment
                WHERE latitude IS NOT NULL
                AND longitude IS NOT NULL
                ORDER BY parcel_number;
                """)

            return await cursor.fetchall()


async def get_property_by_parcel_number(parcel_number: str):
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
                    lot_sqft,
                    latitude,
                    longitude
                FROM real_estate_current_assessment
                WHERE parcel_number = %s;
                """,
                (parcel_number,),
            )

            return await cursor.fetchone()


async def get_map_crimes():
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute("""
                SELECT 
                    record_id,
                    latitude,
                    longitude,
                    location_precision
                FROM crime
                WHERE latitude IS NOT NULL
                AND longitude IS NOT NULL
                ORDER BY record_id
                """)

            return await cursor.fetchall()


async def get_crime_by_record_id(record_id: int):
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                SELECT
                    record_id,
                    offense,
                    date_reported,
                    block_number,
                    street_name,
                    latitude,
                    longitude,
                    mapping_method,
                    location_precision
                FROM crime
                WHERE record_id = %s
                """,
                (record_id,),
            )

            return await cursor.fetchone()
