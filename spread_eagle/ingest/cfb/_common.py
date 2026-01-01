"""
Common utilities for CFB data ingestion.

College Football Data API uses week-based pagination.
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
import pandas as pd
import requests

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from spread_eagle.config.settings import settings


API_BASE = "https://api.collegefootballdata.com"
S3_BUCKET = "spread-eagle"


def get_headers() -> Dict[str, str]:
    """Get API headers with auth."""
    settings.require("cfb")
    return {"Authorization": f"Bearer {settings.cfb_api_key}"}


def get_s3_client():
    """Get S3 client with correct profile."""
    session = boto3.Session(profile_name="spread-eagle-dev", region_name="us-east-2")
    return session.client("s3")


def to_snake_case(name: str) -> str:
    """Convert camelCase to snake_case."""
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """Flatten nested dict."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def fetch_endpoint(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> List[Dict[str, Any]]:
    """Fetch data from a single endpoint."""
    url = f"{API_BASE}{endpoint}"
    headers = get_headers()

    r = requests.get(url, headers=headers, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def fetch_by_weeks(
    endpoint: str,
    year: int,
    season_type: str = "regular",
    weeks: Optional[List[int]] = None,
    id_field: str = "id",
    extra_params: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch data by iterating through weeks.

    CFB season:
    - Regular: weeks 1-15 (some years vary)
    - Postseason: weeks 1-5
    """
    if weeks is None:
        if season_type == "regular":
            weeks = list(range(0, 16))  # Week 0 through 15
        else:
            weeks = list(range(1, 6))  # Postseason weeks 1-5

    all_records = []
    seen_ids = set()

    for week in weeks:
        params = {
            "year": year,
            "seasonType": season_type,
            "week": week,
        }
        if extra_params:
            params.update(extra_params)

        try:
            data = fetch_endpoint(endpoint, params)

            # Deduplicate by id_field
            for record in data:
                record_id = record.get(id_field)
                if record_id and record_id not in seen_ids:
                    seen_ids.add(record_id)
                    all_records.append(record)
                elif not record_id:
                    all_records.append(record)

            if data:
                print(f"    Week {week}: {len(data)} records")
        except Exception as e:
            print(f"    Week {week}: Error - {e}")

    return all_records


def fetch_by_year_only(
    endpoint: str,
    year: int,
    extra_params: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Fetch data for a full year (no week iteration needed)."""
    params = {"year": year}
    if extra_params:
        params.update(extra_params)

    return fetch_endpoint(endpoint, params, timeout=60)


def save_to_files(
    records: List[Dict[str, Any]],
    output_dir: Path,
    file_prefix: str,
) -> None:
    """Save records to JSON, CSV, and Parquet."""
    if not records:
        print(f"  No records to save for {file_prefix}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    # Save raw JSON
    json_path = output_dir / f"{file_prefix}.json"
    with open(json_path, "w") as f:
        json.dump(records, f, indent=2, default=str)

    # Flatten and convert to DataFrame
    flat_records = []
    for r in records:
        flat = flatten_dict(r)
        flat_records.append(flat)

    df = pd.DataFrame(flat_records)

    # Convert column names to snake_case
    df.columns = [to_snake_case(col) for col in df.columns]

    # Save CSV
    csv_path = output_dir / f"{file_prefix}.csv"
    df.to_csv(csv_path, index=False)

    # Save Parquet
    parquet_path = output_dir / f"{file_prefix}.parquet"
    df.to_parquet(parquet_path, index=False)

    print(f"  Saved {len(df)} records to {output_dir.name}/")


def upload_to_s3(local_dir: Path, s3_prefix: str) -> None:
    """Upload all files in a directory to S3."""
    try:
        s3 = get_s3_client()

        for file_path in local_dir.glob("*"):
            if file_path.is_file():
                s3_key = f"{s3_prefix}/{file_path.name}"
                s3.upload_file(str(file_path), S3_BUCKET, s3_key)
                print(f"  Uploaded: s3://{S3_BUCKET}/{s3_key}")
    except Exception as e:
        print(f"  S3 upload skipped: {e}")
