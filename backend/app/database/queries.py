# This is where the agent model has access to

from psycopg.rows import dict_row

from app.database.connection import pool

async def get_properties(limit: int = 20):
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                SELECT 
                    record_id,
                    parcel_number,
                    street_number,
                    street_name,
                    unit,
                    state_code,
                    tax_type,
                    zone,
                    tax_dist,
                    legal,
                    acreage,
                    gpin
                FROM real_estate
                ORDER BY record_id
                LIMIT %s;
                """,
                (limit,),
            )
            
            return await cursor.fetchall()