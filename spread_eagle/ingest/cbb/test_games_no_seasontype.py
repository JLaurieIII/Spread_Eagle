"""
Test games pagination WITHOUT seasonType parameter.
"""
import requests
from spread_eagle.config import settings

BASE_URL = "https://api.collegebasketballdata.com"

headers = {
    "Authorization": f"Bearer {settings.cbb_api_key}",
    "Accept": "application/json",
}

season = 2025

print(f"Testing games pagination for {season} WITHOUT seasonType\n")

all_ids = set()

for page in range(1, 6):
    offset = (page - 1) * 3000
    params = {
        "season": season,
        "offset": offset,
        "limit": 3000,
    }

    resp = requests.get(f"{BASE_URL}/games", headers=headers, params=params, timeout=60)
    data = resp.json()

    if not data:
        print(f"Page {page} (offset={offset}): EMPTY - no more data")
        break

    page_ids = {r.get("id") for r in data if r.get("id")}
    new_ids = page_ids - all_ids

    print(f"Page {page} (offset={offset}): {len(data)} records, {len(new_ids)} NEW unique IDs")

    if len(new_ids) == 0:
        print("  -> All duplicates, stopping")
        break

    all_ids.update(page_ids)

print(f"\nTotal unique IDs collected: {len(all_ids)}")
