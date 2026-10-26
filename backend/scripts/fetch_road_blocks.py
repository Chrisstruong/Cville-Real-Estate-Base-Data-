import json
from pathlib import Path
import os

import psycopg
from psycopg.conninfo import make_conninfo
from psycopg.types.json import Jsonb
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
GEOJSON_FILE = BASE_DIR / "road_blocks.geojson"

# Reuse the same configuration as the FastAPI backend.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

conninfo = make_conninfo(
    host="localhost",
    port=5432,
    dbname="charlottesville_real_estate",
    user=os.getenv("DB_IMPORT_USER"),
    password=os.getenv("DB_IMPORT_PASSWORD"),
)

if not os.getenv("DB_IMPORT_USER") or not os.getenv("DB_IMPORT_PASSWORD"):
    raise RuntimeError("Missing import database credentials")


def main():
    with GEOJSON_FILE.open(encoding="utf-8") as file:
        features = json.load(file)["features"]

    print(f"Features to import: {len(features)}")

    records = []

    for feature in features:
        properties = feature["properties"]

        records.append(
            (
                properties["OBJECTID"],
                properties["STREETNAME"],
                properties["BLOCK"],
                Jsonb(feature["geometry"]),
            )
        )

    with psycopg.connect(conninfo) as conn:
        with conn.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO official_cville_road_blocks (
                    objectid,
                    streetname,
                    block_number,
                    geometry
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (objectid)
                DO UPDATE SET
                    streetname = EXCLUDED.streetname,
                    block_number = EXCLUDED.block_number,
                    geometry = EXCLUDED.geometry;
                """,
                records,
            )

    print("GIS road blocks imported successfully!")


if __name__ == "__main__":
    main()
