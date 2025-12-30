"""
Test API limits - what's the max records we can get?
"""
import requests
from spread_eagle.config import settings

BASE_URL = "https://api.collegebasketballdata.com"

headers = {
    "Authorization": f"Bearer {settings.cbb_api_key}",
    "Accept": "application/json",
}

# Test with different limits
for limit in [1000, 3000, 5000, 10000, 50000]:
    params = {
        "season": 2025,
        "seasonType": "regular",
        "limit": limit,
    }

    resp = requests.get(f"{BASE_URL}/games", headers=headers, params=params, timeout=60)
    data = resp.json()

    unique_ids = len(set(r.get("id") for r in data if r.get("id")))

    print(f"limit={limit:,}: Got {len(data):,} records, {unique_ids:,} unique IDs")
