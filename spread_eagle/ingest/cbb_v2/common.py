"""
Common utilities for CBB V2 ingestion pipeline.

Provides:
- API client with DATE-RANGE pagination (the correct approach for this API)
- Database operations with upsert logic
- Shared constants and configuration
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import pandas as pd
import requests
from sqlalchemy import text
from sqlalchemy.engine import Engine

from spread_eagle.config import get_data_paths, settings
from spread_eagle.core.database import engine as db_engine

# =============================================================================
# CONSTANTS
# =============================================================================

BASE_URL = "https://api.collegebasketballdata.com"
START_YEAR = 2022
RATE_LIMIT_SLEEP = 0.2  # seconds between API calls

# Default schema for raw CBB data
RAW_SCHEMA = "cbb_raw"

# Dataset configuration: (table_name, primary_key_columns)
DATASET_CONFIG = {
    "teams": ("teams", ["id"]),
    "venues": ("venues", ["id"]),
    "games": ("games", ["id"]),
    "team_game_stats": ("team_game_stats", ["game_id", "team_id"]),
    "lines": ("lines", ["game_id", "provider"]),
    "team_season_stats": ("team_season_stats", ["season", "team_id"]),
    "player_season_stats": ("player_season_stats", ["season", "athlete_id"]),
    "game_players": ("game_players", ["game_id", "team_id", "athlete_id"]),
}


# =============================================================================
# API CLIENT - Using DATE-RANGE pagination (proven to work)
# =============================================================================

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
        # End of month
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
    Fetch data using DATE-RANGE pagination (the proven approach).

    The API caps at 3000 records per request but respects startDateRange/endDateRange.
    CBB season runs Nov-Apr, so we chunk by month.

    Args:
        endpoint: API endpoint (e.g., "/games")
        season: Season year (e.g., 2026)
        base_params: Additional parameters
        id_field: Field to use for deduplication
        composite_key: List of field names for composite key deduplication

    Returns:
        List of deduplicated records
    """
    headers = get_headers()
    out: List[Dict[str, Any]] = []
    seen_keys: set = set()

    # Season runs Nov of prior year through Apr of season year
    # e.g., 2026 season = Nov 2025 - Apr 2026
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

        # Dedupe on the fly
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

        time.sleep(RATE_LIMIT_SLEEP)

    return out


def fetch_simple(endpoint: str) -> List[Dict[str, Any]]:
    """Fetch data from API (no pagination, simple GET for reference data)."""
    headers = get_headers()
    resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=60)

    if resp.status_code != 200:
        print(f"    ERROR: {resp.status_code} - {resp.text[:200]}")
        return []

    return resp.json()


def fetch_with_params(
    endpoint: str,
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Fetch data from API with given params (single request)."""
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


# Legacy class for backwards compatibility
class CBBAPIClient:
    """Legacy API client - use fetch_by_date_ranges() instead for paginated data."""

    def __init__(self):
        if not settings.cbb_api_key:
            raise RuntimeError("Missing CBB_API_KEY in .env")
        self.headers = get_headers()

    def fetch(self, endpoint: str, params: Optional[Dict[str, Any]] = None, paginate: bool = True, **kwargs) -> List[Dict[str, Any]]:
        """Fetch data - for non-paginated endpoints only."""
        if paginate:
            print("    WARNING: Use fetch_by_date_ranges() for paginated data!")
        return fetch_simple(endpoint) if not params else fetch_with_params(endpoint, params or {})


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

def get_engine() -> Engine:
    """Get the SQLAlchemy engine."""
    return db_engine


def ensure_schema_exists(engine: Engine, schema: str = RAW_SCHEMA) -> None:
    """Create schema if it doesn't exist."""
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.commit()
    print(f"[DB] Schema '{schema}' ready")


def create_table_from_df(
    engine: Engine,
    df: pd.DataFrame,
    table_name: str,
    schema: str = RAW_SCHEMA,
    primary_keys: Optional[List[str]] = None,
) -> None:
    """
    Create a table from DataFrame schema if it doesn't exist.

    This creates a basic table structure. For production, you may want
    to define explicit DDL with proper types.
    """
    # Use pandas to create table structure, then add primary key
    full_table = f"{schema}.{table_name}"

    # Check if table exists
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = '{table_name}'
            )
        """))
        exists = result.scalar()

    if not exists:
        # Create table using pandas (creates basic structure)
        df.head(0).to_sql(
            table_name,
            engine,
            schema=schema,
            if_exists="replace",
            index=False,
        )
        print(f"[DB] Created table {full_table}")

        # Add primary key if specified
        if primary_keys:
            pk_cols = ", ".join(primary_keys)
            with engine.connect() as conn:
                try:
                    conn.execute(text(f"""
                        ALTER TABLE {full_table}
                        ADD PRIMARY KEY ({pk_cols})
                    """))
                    conn.commit()
                    print(f"[DB] Added primary key ({pk_cols}) to {full_table}")
                except Exception as e:
                    print(f"[DB] Warning: Could not add primary key: {e}")


def upsert_dataframe(
    engine: Engine,
    df: pd.DataFrame,
    table_name: str,
    schema: str = RAW_SCHEMA,
    primary_keys: Optional[List[str]] = None,
    update_on_conflict: bool = True,
) -> int:
    """
    Upsert DataFrame into Postgres table.

    Args:
        engine: SQLAlchemy engine
        df: DataFrame to upsert
        table_name: Target table name
        schema: Database schema
        primary_keys: Columns that form the primary/unique key
        update_on_conflict: If True, update on conflict; if False, skip

    Returns:
        Number of rows affected
    """
    if df.empty:
        print(f"[DB] No data to upsert into {schema}.{table_name}")
        return 0

    full_table = f"{schema}.{table_name}"

    # Ensure table exists
    create_table_from_df(engine, df, table_name, schema, primary_keys)

    # Build upsert query
    columns = df.columns.tolist()
    col_list = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join(f":{c}" for c in columns)

    if primary_keys and update_on_conflict:
        # ON CONFLICT DO UPDATE
        pk_cols = ", ".join(f'"{c}"' for c in primary_keys)
        update_cols = [c for c in columns if c not in primary_keys]
        update_set = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in update_cols)

        if update_cols:
            query = f"""
                INSERT INTO {full_table} ({col_list})
                VALUES ({placeholders})
                ON CONFLICT ({pk_cols}) DO UPDATE SET {update_set}
            """
        else:
            # All columns are primary keys, just skip on conflict
            query = f"""
                INSERT INTO {full_table} ({col_list})
                VALUES ({placeholders})
                ON CONFLICT ({pk_cols}) DO NOTHING
            """
    elif primary_keys:
        # ON CONFLICT DO NOTHING
        pk_cols = ", ".join(f'"{c}"' for c in primary_keys)
        query = f"""
            INSERT INTO {full_table} ({col_list})
            VALUES ({placeholders})
            ON CONFLICT ({pk_cols}) DO NOTHING
        """
    else:
        # Simple insert (may create duplicates)
        query = f"""
            INSERT INTO {full_table} ({col_list})
            VALUES ({placeholders})
        """

    # Execute batch insert
    records = df.to_dict(orient="records")

    with engine.connect() as conn:
        result = conn.execute(text(query), records)
        conn.commit()
        rows_affected = result.rowcount

    print(f"[DB] Upserted {len(records)} records into {full_table} ({rows_affected} affected)")
    return rows_affected


def truncate_table(engine: Engine, table_name: str, schema: str = RAW_SCHEMA) -> None:
    """Truncate a table (for full reload scenarios)."""
    full_table = f"{schema}.{table_name}"
    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE TABLE {full_table} CASCADE"))
        conn.commit()
    print(f"[DB] Truncated {full_table}")


# =============================================================================
# DATA TRANSFORMATION HELPERS
# =============================================================================

def flatten_json(data: List[Dict[str, Any]], sep: str = "_") -> pd.DataFrame:
    """Flatten nested JSON to DataFrame."""
    if not data:
        return pd.DataFrame()
    return pd.json_normalize(data, sep=sep)


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Clean column names for Postgres compatibility."""
    df.columns = [
        c.lower()
        .replace(".", "_")
        .replace("-", "_")
        .replace(" ", "_")
        .replace("__", "_")
        for c in df.columns
    ]
    return df


def dedupe_records(
    records: List[Dict[str, Any]],
    key_func: Callable[[Dict], Any],
) -> List[Dict[str, Any]]:
    """Deduplicate records by a key function."""
    seen = set()
    out = []
    for r in records:
        key = key_func(r)
        if key is not None and key not in seen:
            out.append(r)
            seen.add(key)
        elif key is None:
            out.append(r)
    return out


# =============================================================================
# CDC / INCREMENTAL HELPERS
# =============================================================================

def get_incremental_date_range(days_back: int = 7) -> tuple[datetime, datetime]:
    """Get date range for incremental load."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    return start_date, end_date


def get_current_season() -> int:
    """
    Get the current CBB season year.

    CBB season spans fall-spring, so:
    - Nov 2024 - Mar 2025 = 2025 season
    """
    now = datetime.now()
    if now.month >= 11:  # Nov-Dec = next year's season
        return now.year + 1
    elif now.month <= 4:  # Jan-Apr = current season
        return now.year
    else:  # May-Oct = upcoming season hasn't started
        return now.year + 1


def get_data_paths_cbb():
    """Get CBB data paths."""
    paths = get_data_paths("cbb")
    paths.ensure_dirs()
    return paths
