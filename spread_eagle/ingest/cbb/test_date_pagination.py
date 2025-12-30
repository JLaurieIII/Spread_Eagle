"""
Test if we can get more data by filtering by date ranges or conference.
"""
import requests
from spread_eagle.config import settings

BASE_URL = "https://api.collegebasketballdata.com"

headers = {
    "Authorization": f"Bearer {settings.cbb_api_key}",
    "Accept": "application/json",
}

season = 2025

# First, let's see what the actual data range is
print("=" * 50)
print("Checking dates of games returned")
print("=" * 50)
params = {"season": season}
resp = requests.get(f"{BASE_URL}/games", headers=headers, params=params, timeout=60)
data = resp.json()

dates = sorted(set(r.get("startDate", "")[:10] for r in data if r.get("startDate")))
print(f"Got {len(data)} games")
print(f"Date range: {dates[0]} to {dates[-1]}")
print(f"Unique dates: {len(dates)}")

# Try with startDate filter
print("\n" + "=" * 50)
print("Testing startDate filter")
print("=" * 50)
for start in ["2024-11-01", "2024-12-01", "2025-01-01"]:
    params = {"season": season, "startDate": start}
    resp = requests.get(f"{BASE_URL}/games", headers=headers, params=params, timeout=60)
    data = resp.json()
    first_id = data[0].get("id") if data else None
    print(f"  startDate={start}: {len(data)} records, first_id={first_id}")

# Try with endDate filter
print("\n" + "=" * 50)
print("Testing date ranges (chunks)")
print("=" * 50)
date_ranges = [
    ("2024-11-01", "2024-11-30"),
    ("2024-12-01", "2024-12-31"),
    ("2025-01-01", "2025-01-31"),
    ("2025-02-01", "2025-02-28"),
    ("2025-03-01", "2025-03-31"),
]
total_unique = set()
for start, end in date_ranges:
    params = {"season": season, "startDate": start, "endDate": end}
    resp = requests.get(f"{BASE_URL}/games", headers=headers, params=params, timeout=60)
    data = resp.json()
    ids = {r.get("id") for r in data if r.get("id")}
    new_ids = ids - total_unique
    total_unique.update(ids)
    print(f"  {start} to {end}: {len(data)} records, {len(new_ids)} new IDs")

print(f"\nTotal unique games via date ranges: {len(total_unique)}")
