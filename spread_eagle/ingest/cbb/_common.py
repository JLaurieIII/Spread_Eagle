"""
Common utilities for CBB data ingestion scripts.

S3 Structure:
    spread-eagle/
        cbb/
            raw/
                conferences/
                venues/
                teams/
                games/
                lines/
                team_stats/
                player_stats/
                team_season_stats/
                player_season_stats/
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
import pandas as pd
import requests

from spread_eagle.config import get_data_paths, settings

BASE_URL = "https://api.collegebasketballdata.com"
PAGE_SIZE = 3000
MAX_PAGES = 200
START_YEAR = 2022
S3_BUCKET = "spread-eagle"


def get_current_cbb_season() -> int:
    """Get current CBB season (Nov-Apr = next year's season)."""
    now = datetime.now()
    return now.year + 1 if now.month >= 8 else now.year


def get_headers() -> Dict[str, str]:
    """Get API headers with auth."""
    if not settings.cbb_api_key:
        raise RuntimeError("Missing CBB_API_KEY in .env")
    return {
        "Authorization": f"Bearer {settings.cbb_api_key}",
        "Accept": "application/json",
    }


def generate_month_ranges(start_year: int, start_month: int, end_year: int, end_month: int) -> List[tuple]:
    """Generate monthly date ranges for pagination."""
    ranges = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        # Start of month
        start = f"{year}-{month:02d}-01T00:00:00Z"
        # End of month (use 28 for Feb, actual last day for others)
        if month == 12:
            end = f"{year}-12-31T23:59:59Z"
        elif month in [4, 6, 9, 11]:
            end = f"{year}-{month:02d}-30T23:59:59Z"
        elif month == 2:
            end = f"{year}-02-28T23:59:59Z"
        else:
            end = f"{year}-{month:02d}-31T23:59:59Z"
        ranges.append((start, end))
        # Next month
        month += 1
        if month > 12:
            month = 1
            year += 1
    return ranges


def fetch_by_date_ranges(
    endpoint: str,
    season: int,
    base_params: Optional[Dict[str, Any]] = None,
    id_field: str = "id",
    composite_key: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch data using date range pagination.

    The API caps at 3000 records per request but respects startDateRange/endDateRange.
    CBB season runs Nov-Apr, so we chunk by month.

    Args:
        composite_key: List of field names to use as composite key for deduplication.
                       If provided, id_field is ignored.
    """
    headers = get_headers()
    out: List[Dict[str, Any]] = []
    seen_keys: set = set()

    # Season runs Nov of prior year through Apr of season year
    # e.g., 2025 season = Nov 2024 - Apr 2025
    month_ranges = generate_month_ranges(season - 1, 11, season, 4)

    for start_date, end_date in month_ranges:
        params = {"season": season, "startDateRange": start_date, "endDateRange": end_date}
        if base_params:
            params.update(base_params)

        try:
            resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers, params=params, timeout=120)
        except requests.exceptions.Timeout:
            print(f"        Timeout for {start_date[:7]}, retrying...")
            time.sleep(2)
            try:
                resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers, params=params, timeout=120)
            except:
                print(f"        Failed for {start_date[:7]}, skipping")
                continue

        if resp.status_code != 200:
            print(f"        ERROR {resp.status_code} for {start_date[:7]}: {resp.text[:100]}")
            continue

        data = resp.json()
        if not isinstance(data, list):
            continue

        # Dedupe on the fly using composite key or single id_field
        new_records = []
        for r in data:
            if composite_key:
                key = tuple(r.get(k) for k in composite_key)
            else:
                key = r.get(id_field)
            if key is not None and key not in seen_keys:
                seen_keys.add(key)
                new_records.append(r)

        out.extend(new_records)
        print(f"        {start_date[:7]}: {len(data)} fetched, {len(new_records)} new")

        time.sleep(0.2)

    return out


def fetch_with_params(
    endpoint: str,
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Fetch data from API with given params (single request, no pagination)."""
    headers = get_headers()

    try:
        resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers, params=params, timeout=120)
    except requests.exceptions.Timeout:
        print(f"        Timeout, retrying...")
        time.sleep(2)
        resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers, params=params, timeout=120)

    if resp.status_code != 200:
        print(f"        ERROR: {resp.status_code} - {resp.text[:200]}")
        return []

    data = resp.json()
    return data if isinstance(data, list) else []


def fetch_simple(endpoint: str) -> List[Dict[str, Any]]:
    """Fetch data from API (no pagination, simple GET)."""
    headers = get_headers()
    resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=60)

    if resp.status_code != 200:
        print(f"    ERROR: {resp.status_code} - {resp.text[:200]}")
        return []

    return resp.json()


def dedupe_records(
    records: List[Dict[str, Any]],
    id_field: str = "id",
    composite_key: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Remove duplicate records."""
    seen = set()
    out = []
    for r in records:
        if composite_key:
            key = tuple(r.get(k) for k in composite_key)
        else:
            key = r.get(id_field)
        if key is None or key not in seen:
            out.append(r)
            if key is not None:
                seen.add(key)
    return out


def save_json(records: List[Dict[str, Any]], path: Path) -> None:
    """Save records to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(f"    Saved: {path.name} ({len(records):,} records)")


def save_csv_parquet(
    records: List[Dict[str, Any]],
    base_path: Path,
    flatten_field: Optional[str] = None,
) -> Dict[str, Path]:
    """Save records to CSV and Parquet."""
    if not records:
        print("    No records to save")
        return {}

    base_path.parent.mkdir(parents=True, exist_ok=True)

    # Flatten if needed (e.g., for lines which have nested arrays)
    if flatten_field:
        flat_records = []
        for record in records:
            base = {k: v for k, v in record.items() if k != flatten_field}
            nested = record.get(flatten_field, [])
            if nested:
                for item in nested:
                    flat_records.append({**base, **item})
            else:
                flat_records.append(base)
        df = pd.DataFrame(flat_records)
    else:
        df = pd.json_normalize(records, sep="_")

    # Save CSV
    csv_path = base_path.with_suffix(".csv")
    df.to_csv(csv_path, index=False)
    print(f"    Saved: {csv_path.name} ({len(df):,} rows)")

    # Save Parquet
    parquet_path = base_path.with_suffix(".parquet")
    df.to_parquet(parquet_path, index=False)
    print(f"    Saved: {parquet_path.name}")

    return {"csv": csv_path, "parquet": parquet_path}


def get_s3_client():
    """Get S3 client with correct profile."""
    session = boto3.Session(profile_name="spread-eagle-dev", region_name="us-east-2")
    return session.client("s3")


def upload_folder_to_s3(local_dir: Path, s3_prefix: str) -> None:
    """Upload all files in a folder to S3."""
    s3 = get_s3_client()

    for file_path in local_dir.iterdir():
        if file_path.is_file():
            s3_key = f"{s3_prefix}/{file_path.name}"
            print(f"    Uploading: s3://{S3_BUCKET}/{s3_key}")
            s3.upload_file(str(file_path), S3_BUCKET, s3_key)


def upload_file_to_s3(local_path: Path, s3_prefix: str) -> str:
    """Upload a single file to S3."""
    s3 = get_s3_client()
    s3_key = f"{s3_prefix}/{local_path.name}"
    print(f"    Uploading: s3://{S3_BUCKET}/{s3_key}")
    s3.upload_file(str(local_path), S3_BUCKET, s3_key)
    return f"s3://{S3_BUCKET}/{s3_key}"
