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
        
async def get_largest_properties(
    limit: int = 5,
    tax_type: str | None = None,
):
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cursor:
            
            if tax_type:
                await cursor.execute(
                    """
                    SELECT
                        record_id,
                        parcel_number,
                        street_number,
                        street_name,
                        acreage,
                        zone,
                        tax_type
                    FROM real_estate
                    WHERE tax_type = %s
                    ORDER BY acreage DESC
                    LIMIT %s;
                    """,
                    (tax_type, limit),
                )
            else:
                await cursor.execute(
                    """
                    SELECT 
                        record_id,
                        parcel_number,
                        street_number,
                        street_name,
                        acreage,
                        zone,
                        tax_type
                    FROM real_estate
                    ORDER BY acreage DESC
                    LIMIT %s;
                    """,
                    (limit,),  
                )
            properties = await cursor.fetchall()   
            return properties