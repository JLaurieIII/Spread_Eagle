"""
Test API pagination to see what's happening.
"""
import requests
from spread_eagle.config import settings

BASE_URL = "https://api.collegebasketballdata.com"

headers = {
    "Authorization": f"Bearer {settings.cbb_api_key}",
    "Accept": "application/json",
}

# Test with 2025 regular season
season = 2025
season_type = "regular"

print(f"Testing pagination for {season} {season_type}\n")

for page in range(1, 6):  # Test first 5 pages
    offset = (page - 1) * 3000
    params = {
        "season": season,
        "seasonType": season_type,
        "offset": offset,
        "limit": 3000,
    }

    resp = requests.get(f"{BASE_URL}/games", headers=headers, params=params, timeout=60)
    data = resp.json()

    if not data:
        print(f"Page {page} (offset={offset}): EMPTY - no more data")
        break

    ids = [r.get("id") for r in data[:5]]  # First 5 IDs
    last_ids = [r.get("id") for r in data[-3:]]  # Last 3 IDs

    print(f"Page {page} (offset={offset}): {len(data)} records")
    print(f"  First 5 IDs: {ids}")
    print(f"  Last 3 IDs: {last_ids}")
    print()
