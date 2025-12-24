from __future__ import annotations

import json
from typing import Any, Dict, List

import requests
import pandas as pd

from spread_eagle.config import get_data_paths, settings

BASE_URL = "https://api.collegebasketballdata.com"


def fetch_conferences() -> List[Dict[str, Any]]:
    """
    Fetch all conferences (reference data).
    """
    if not settings.cbb_api_key:
        raise RuntimeError("Missing CBB_API_KEY in .env")

    headers = {
        "Authorization": f"Bearer {settings.cbb_api_key}",
        "Accept": "application/json",
    }

    resp = requests.get(f"{BASE_URL}/conferences", headers=headers, timeout=60)

    if resp.status_code != 200:
        print(f"ERROR: {resp.status_code} - {resp.text[:200]}")
        return []

    return resp.json()


def main() -> None:
    paths = get_data_paths("cbb")
    paths.ensure_dirs()

    print("Pulling conferences...")
    conferences = fetch_conferences()

    # Save JSON
    json_path = paths.raw / "conferences.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(conferences, f, indent=2)

    # Save CSV
    if conferences:
        df = pd.json_normalize(conferences, sep="__")
        csv_path = paths.raw / "conferences.csv"
        df.to_csv(csv_path, index=False)
        print(f"Saved CSV -> {csv_path}")

    print(f"Saved JSON -> {json_path}")
    print(f"Total: {len(conferences):,} conferences")


if __name__ == "__main__":
    main()
