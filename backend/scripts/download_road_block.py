import json
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

API_URL = (
    "https://gisweb.charlottesville.org"
    "/cvgisweb/rest/services/RCL_Blocks/MapServer/0/query"
)

PAGE_SIZE = 200
MAX_RETRIES = 5

BASE_DIR = Path(__file__).resolve().parent
CHECKPOINT_FILE = BASE_DIR / "road_blocks_progress.json"
OUTPUT_FILE = BASE_DIR / "road_blocks.geojson"


def save_progress(features):
    CHECKPOINT_FILE.write_text(json.dumps(features), encoding="utf-8")


def fetch_page(offset):
    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": 4326,
        "resultOffset": offset,
        "resultRecordCount": PAGE_SIZE,
        "orderByFields": "OBJECTID ASC",
        "f": "geojson",
    }

    url = API_URL + "?" + urllib.parse.urlencode(params)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Connection": "close",
                },
            )

            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.load(response)

            if "error" in data:
                raise RuntimeError(data["error"])

            if data.get("type") != "FeatureCollection":
                raise RuntimeError("Unexpected GIS response")

            return data["features"]

        except (
            ConnectionResetError,
            TimeoutError,
            urllib.error.URLError,
        ) as error:
            print(f"Attempt {attempt} failed: {error}")

            if attempt == MAX_RETRIES:
                raise

            time.sleep(2**attempt)


def main():
    if CHECKPOINT_FILE.exists():
        features = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        print(f"Resuming from {len(features)} features")
    else:
        features = []

    ids = [f["properties"]["OBJECTID"] for f in features]

    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate IDs in checkpoint")

    offset = len(features)

    while True:
        page = fetch_page(offset)

        if not page:
            break

        page_ids = [feature["properties"]["OBJECTID"] for feature in page]

        if len(page_ids) != len(set(page_ids)):
            raise RuntimeError("Duplicate IDs within page")

        if set(page_ids).intersection(ids):
            raise RuntimeError("Duplicate IDs across pages")

        features.extend(page)
        ids.extend(page_ids)

        save_progress(features)

        offset += len(page)
        print(f"Downloaded {len(features)} features")

        if len(page) < PAGE_SIZE:
            break

        time.sleep(0.5)

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": features,
            }
        ),
        encoding="utf-8",
    )

    print(f"\nDownload complete: {len(features)} features")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
