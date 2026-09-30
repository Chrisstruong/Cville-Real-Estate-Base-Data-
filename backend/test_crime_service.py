import asyncio
import sys

from app.database.connection import pool
from app.services.crime_service import property_street_has_crime

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    await pool.open()

    try:
        streets = [
            "14TH STREET NW",
            "EMMET STREET",
            "MACAA DR",
        ]

        for street in streets:
            result = await property_street_has_crime(street)
            print(f"{street}: {result}")

    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
