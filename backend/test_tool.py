import asyncio

from app.database.connection import pool
from app.tools.property_tools import get_largest_properties


async def main():
    await pool.open()

    try:
        result = await get_largest_properties.on_invoke_tool(
            None,
            '{"limit": 5, "tax_type": "Exempt"}',
        )

        print(result)

    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(
        main(),
        loop_factory=asyncio.SelectorEventLoop,
    )