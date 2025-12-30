"""
Test different pagination methods to find what works.
"""
import requests
from spread_eagle.config import settings

BASE_URL = "https://api.collegebasketballdata.com"

headers = {
    "Authorization": f"Bearer {settings.cbb_api_key}",
    "Accept": "application/json",
}

season = 2025

print("Testing different pagination approaches for /games\n")

# Method 1: offset/limit (what we tried)
print("=" * 50)
print("Method 1: offset/limit")
print("=" * 50)
for offset in [0, 3000]:
    params = {"season": season, "offset": offset, "limit": 3000}
    resp = requests.get(f"{BASE_URL}/games", headers=headers, params=params, timeout=60)
    data = resp.json()
    first_id = data[0].get("id") if data else None
    print(f"  offset={offset}: {len(data)} records, first_id={first_id}")

# Method 2: page/pageSize
print("\n" + "=" * 50)
print("Method 2: page/pageSize")
print("=" * 50)
for page in [1, 2]:
    params = {"season": season, "page": page, "pageSize": 3000}
    resp = requests.get(f"{BASE_URL}/games", headers=headers, params=params, timeout=60)
    data = resp.json()
    first_id = data[0].get("id") if data else None
    print(f"  page={page}: {len(data)} records, first_id={first_id}")

# Method 3: pageNumber/limit
print("\n" + "=" * 50)
print("Method 3: pageNumber/limit")
print("=" * 50)
for page in [0, 1, 2]:
    params = {"season": season, "pageNumber": page, "limit": 3000}
    resp = requests.get(f"{BASE_URL}/games", headers=headers, params=params, timeout=60)
    data = resp.json()
    first_id = data[0].get("id") if data else None
    print(f"  pageNumber={page}: {len(data)} records, first_id={first_id}")

# Method 4: Check total count header
print("\n" + "=" * 50)
print("Method 4: Response headers")
print("=" * 50)
resp = requests.get(f"{BASE_URL}/games", headers=headers, params={"season": season}, timeout=60)
print(f"  Status: {resp.status_code}")
print(f"  Headers: {dict(resp.headers)}")

# Method 5: No limit at all
print("\n" + "=" * 50)
print("Method 5: No limit parameter")
print("=" * 50)
resp = requests.get(f"{BASE_URL}/games", headers=headers, params={"season": season}, timeout=60)
data = resp.json()
print(f"  No limit: {len(data)} records")
