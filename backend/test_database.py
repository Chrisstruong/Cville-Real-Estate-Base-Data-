import asyncio

from app.database.connection import pool
from app.services.properties import fetch_largest_properties


async def main():
    await pool.open()

    try:
        result = await fetch_largest_properties(
            limit=5,
            tax_type="Exempt",
        )

        print(result)

    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(
        main(),
        loop_factory=asyncio.SelectorEventLoop,
    )