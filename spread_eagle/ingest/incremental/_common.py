"""
Common utilities for incremental (7-day rolling window) ingestion.

All functions here prioritize:
- Explicit date handling
- Clear error reporting (no silent failures)
- Verification metadata
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import boto3
import pandas as pd
import requests

from spread_eagle.config.settings import settings

# API endpoints
CBB_API_BASE = "https://api.collegebasketballdata.com"
CFB_API_BASE = "https://api.collegefootballdata.com"

# S3 config
S3_BUCKET = "spread-eagle"
S3_PROFILE = "spread-eagle-dev"
S3_REGION = "us-east-2"

# Request settings
REQUEST_TIMEOUT = 120
RETRY_DELAY = 2
MAX_RETRIES = 3


def get_date_window(days: int = 7) -> Tuple[datetime, datetime]:
    """
    Get explicit date window for ingestion.

    Returns (start_date, end_date) where:
    - end_date = today at 23:59:59 UTC
    - start_date = (today - days) at 00:00:00 UTC

    This ensures we capture all records in the window regardless
    of when during the day the script runs.
    """
    now = datetime.now(timezone.utc)
    end_date = now.replace(hour=23, minute=59, second=59, microsecond=0)
    start_date = (now - timedelta(days=days)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return start_date, end_date


def format_date_iso(dt: datetime) -> str:
    """Format datetime as ISO string for API calls."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def format_date_ymd(dt: datetime) -> str:
    """Format datetime as YYYY-MM-DD for file paths."""
    return dt.strftime("%Y-%m-%d")


def get_cbb_headers() -> Dict[str, str]:
    """Get CBB API headers with auth."""
    if not settings.cbb_api_key:
        raise RuntimeError("Missing CBB_API_KEY in .env - cannot proceed")
    return {
        "Authorization": f"Bearer {settings.cbb_api_key}",
        "Accept": "application/json",
    }


def get_cfb_headers() -> Dict[str, str]:
    """Get CFB API headers with auth."""
    if not settings.cfb_api_key:
        raise RuntimeError("Missing CFB_API_KEY in .env - cannot proceed")
    return {
        "Authorization": f"Bearer {settings.cfb_api_key}",
        "Accept": "application/json",
    }


def fetch_with_retry(
    url: str,
    headers: Dict[str, str],
    params: Dict[str, Any],
    max_retries: int = MAX_RETRIES,
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Fetch data from API with explicit retry logic.

    Returns:
        Tuple of (records, success_flag)
        - On success: (list of records, True)
        - On failure: (empty list, False)

    This function NEVER silently swallows errors.
    """
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)

            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return data, True
                else:
                    print(f"    WARNING: Expected list, got {type(data).__name__}")
                    return [], False

            elif resp.status_code == 429:
                # Rate limited - wait and retry
                wait_time = RETRY_DELAY * (2 ** attempt)
                print(f"    Rate limited (429), waiting {wait_time}s before retry {attempt}/{max_retries}")
                time.sleep(wait_time)
                continue

            else:
                print(f"    ERROR: HTTP {resp.status_code}: {resp.text[:200]}")
                return [], False

        except requests.exceptions.Timeout:
            last_error = "Timeout"
            print(f"    Timeout on attempt {attempt}/{max_retries}")
            time.sleep(RETRY_DELAY)

        except requests.exceptions.RequestException as e:
            last_error = str(e)
            print(f"    Request error on attempt {attempt}/{max_retries}: {e}")
            time.sleep(RETRY_DELAY)

    print(f"    FAILED after {max_retries} attempts. Last error: {last_error}")
    return [], False


def get_s3_client():
    """Get S3 client with correct profile."""
    session = boto3.Session(profile_name=S3_PROFILE, region_name=S3_REGION)
    return session.client("s3")


def create_manifest(
    sport: str,
    endpoint: str,
    start_date: datetime,
    end_date: datetime,
    record_count: int,
    success: bool,
    errors: List[str],
) -> Dict[str, Any]:
    """
    Create manifest metadata for this ingestion run.

    The manifest provides verification data:
    - What window was pulled
    - How many records were found
    - Whether the pull succeeded
    - Any errors encountered
    """
    return {
        "sport": sport,
        "endpoint": endpoint,
        "window": {
            "start_date": format_date_iso(start_date),
            "end_date": format_date_iso(end_date),
            "days": (end_date - start_date).days,
        },
        "pull_timestamp": datetime.now(timezone.utc).isoformat(),
        "record_count": record_count,
        "success": success,
        "errors": errors,
    }


def save_to_local(
    records: List[Dict[str, Any]],
    output_dir: Path,
    file_prefix: str,
    flatten_field: Optional[str] = None,
) -> Dict[str, Path]:
    """
    Save records to local files (JSON, CSV, Parquet).

    Returns dict of format -> path for uploaded files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}

    # Save raw JSON
    json_path = output_dir / f"{file_prefix}.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, default=str)
    paths["json"] = json_path
    print(f"    Saved: {json_path.name} ({len(records):,} records)")

    if not records:
        return paths

    # Flatten if needed (e.g., lines have nested arrays)
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
    csv_path = output_dir / f"{file_prefix}.csv"
    df.to_csv(csv_path, index=False)
    paths["csv"] = csv_path
    print(f"    Saved: {csv_path.name} ({len(df):,} rows)")

    # Save Parquet
    parquet_path = output_dir / f"{file_prefix}.parquet"
    df.to_parquet(parquet_path, index=False)
    paths["parquet"] = parquet_path
    print(f"    Saved: {parquet_path.name}")

    return paths


def upload_to_s3(
    local_dir: Path,
    s3_prefix: str,
    manifest: Dict[str, Any],
) -> bool:
    """
    Upload directory contents to S3 with manifest.

    Returns True if upload succeeded, False otherwise.
    """
    try:
        s3 = get_s3_client()

        # Upload data files
        for file_path in local_dir.iterdir():
            if file_path.is_file():
                s3_key = f"{s3_prefix}/{file_path.name}"
                s3.upload_file(str(file_path), S3_BUCKET, s3_key)
                print(f"    Uploaded: s3://{S3_BUCKET}/{s3_key}")

        # Upload manifest
        manifest_key = f"{s3_prefix}/_manifest.json"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=manifest_key,
            Body=json.dumps(manifest, indent=2),
            ContentType="application/json",
        )
        print(f"    Uploaded: s3://{S3_BUCKET}/{manifest_key}")

        return True

    except Exception as e:
        print(f"    S3 UPLOAD FAILED: {e}")
        return False


def dedupe_records(
    records: List[Dict[str, Any]],
    key_fields: List[str],
) -> List[Dict[str, Any]]:
    """
    Deduplicate records by composite key.

    Args:
        records: List of records to deduplicate
        key_fields: Field names to use as composite key

    Returns:
        Deduplicated list (first occurrence wins)
    """
    seen = set()
    out = []
    for r in records:
        key = tuple(r.get(k) for k in key_fields)
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out
