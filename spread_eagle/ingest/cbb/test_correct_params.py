"""
Test with CORRECT API parameters: startDateRange/endDateRange (ISO 8601 format).
"""
import requests
from spread_eagle.config import settings

BASE_URL = "https://api.collegebasketballdata.com"

headers = {
    "Authorization": f"Bearer {settings.cbb_api_key}",
    "Accept": "application/json",
}

season = 2025

print(f"Testing games with CORRECT parameters for {season}\n")

# Test 1: Just season, no date range
print("=" * 50)
print("Test 1: Season only (baseline)")
print("=" * 50)
params = {"season": season}
resp = requests.get(f"{BASE_URL}/games", headers=headers, params=params, timeout=60)
data = resp.json()
print(f"  Records: {len(data)}")

# Test 2: With startDateRange (ISO 8601 format)
print("\n" + "=" * 50)
print("Test 2: startDateRange parameter (ISO 8601)")
print("=" * 50)
for start in ["2024-11-01T00:00:00Z", "2024-12-01T00:00:00Z", "2025-01-01T00:00:00Z"]:
    params = {"season": season, "startDateRange": start}
    resp = requests.get(f"{BASE_URL}/games", headers=headers, params=params, timeout=60)
    data = resp.json()
    first_id = data[0].get("id") if data else None
    print(f"  startDateRange={start}: {len(data)} records, first_id={first_id}")

# Test 3: With date ranges
print("\n" + "=" * 50)
print("Test 3: Date range chunks (startDateRange + endDateRange)")
print("=" * 50)
date_ranges = [
    ("2024-11-01T00:00:00Z", "2024-11-30T23:59:59Z"),
    ("2024-12-01T00:00:00Z", "2024-12-31T23:59:59Z"),
    ("2025-01-01T00:00:00Z", "2025-01-31T23:59:59Z"),
    ("2025-02-01T00:00:00Z", "2025-02-28T23:59:59Z"),
    ("2025-03-01T00:00:00Z", "2025-03-31T23:59:59Z"),
    ("2025-04-01T00:00:00Z", "2025-04-30T23:59:59Z"),
]
total_unique = set()
for start, end in date_ranges:
    params = {"season": season, "startDateRange": start, "endDateRange": end}
    resp = requests.get(f"{BASE_URL}/games", headers=headers, params=params, timeout=60)
    data = resp.json()
    ids = {r.get("id") for r in data if r.get("id")}
    new_ids = ids - total_unique
    total_unique.update(ids)
    print(f"  {start[:10]} to {end[:10]}: {len(data)} records, {len(new_ids)} new IDs")

print(f"\nTotal unique games via date ranges: {len(total_unique)}")

# Test 4: By seasonType
print("\n" + "=" * 50)
print("Test 4: By seasonType")
print("=" * 50)
all_by_type = set()
for stype in ["preseason", "regular", "postseason"]:
    params = {"season": season, "seasonType": stype}
    resp = requests.get(f"{BASE_URL}/games", headers=headers, params=params, timeout=60)
    data = resp.json()
    ids = {r.get("id") for r in data if r.get("id")}
    new_ids = ids - all_by_type
    all_by_type.update(ids)
    print(f"  seasonType={stype}: {len(data)} records, {len(new_ids)} new IDs")

print(f"\nTotal unique games via seasonType: {len(all_by_type)}")
