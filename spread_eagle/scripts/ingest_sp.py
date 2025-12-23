import os
import time
import json
from pathlib import Path
from typing import Any, Dict, List

import requests
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from spread_eagle.config.settings import settings
from spread_eagle.core.database import engine as db_engine

# =========================
# CONFIG SECTION
# =========================

BASE_URL = "https://api.collegefootballdata.com"

# Debug flag:
#   True  -> pull small sample, write JSON/CSVs, SKIP DB writes
#   False -> pull full range, write JSON/CSVs, LOAD into Postgres
DEBUG = False

if DEBUG:
    # Small sample for quick inspection
    YEARS = [2024]
else:
    # Full history when you're ready
    YEARS = list(range(2022, 2027))   # 2022–2026 inclusive

# Target Postgres schema
RAW_DATA_SCHEMA = "raw_data"
TABLE_NAME = "cfb_sp_ratings"

# Where to save files locally
OUTPUT_DIR = Path("cfb_data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_JSON_PATH = OUTPUT_DIR / "sp_ratings_raw.json"
RATINGS_CSV_PATH = OUTPUT_DIR / "sp_ratings_flat.csv"


def get_api_key() -> str:
    """Read CFBD API key from env."""
    api_key = settings.CFB_API_KEY
    if not api_key:
        raise ValueError("CFB_API_KEY environment variable is not set.")
    return api_key


def get_engine() -> Engine:
    """Use existing project engine."""
    return db_engine

def ensure_schema_exists(engine: Engine):
    """Create raw_data schema if it doesn't exist."""
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {RAW_DATA_SCHEMA}"))
        conn.commit()
    print(f"[DB] Schema {RAW_DATA_SCHEMA} checked/created.")

def create_sp_ratings_table(engine: Engine) -> None:
    """Create the SP+ ratings table if it doesn't exist."""
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {RAW_DATA_SCHEMA}.{TABLE_NAME} (
        year INTEGER NOT NULL,
        team VARCHAR(255) NOT NULL,
        conference VARCHAR(255),
        rating DOUBLE PRECISION,
        ranking INTEGER,
        second_order_wins DOUBLE PRECISION,
        sos DOUBLE PRECISION,
        
        -- Offense metrics
        offense_rating DOUBLE PRECISION,
        offense_success DOUBLE PRECISION,
        offense_explosiveness DOUBLE PRECISION,
        offense_rushing DOUBLE PRECISION,
        offense_passing DOUBLE PRECISION,
        offense_standard_downs DOUBLE PRECISION,
        offense_passing_downs DOUBLE PRECISION,
        offense_run_rate DOUBLE PRECISION,
        offense_pace DOUBLE PRECISION,
        
        -- Defense metrics
        defense_rating DOUBLE PRECISION,
        defense_success DOUBLE PRECISION,
        defense_explosiveness DOUBLE PRECISION,
        defense_rushing DOUBLE PRECISION,
        defense_passing DOUBLE PRECISION,
        defense_standard_downs DOUBLE PRECISION,
        defense_passing_downs DOUBLE PRECISION,
        defense_havoc_total DOUBLE PRECISION,
        defense_havoc_front_seven DOUBLE PRECISION,
        defense_havoc_db DOUBLE PRECISION,
        
        -- Special Teams
        special_teams_rating DOUBLE PRECISION,
        
        -- Composite key for upsert logic
        PRIMARY KEY (year, team)
    );
    
    CREATE INDEX IF NOT EXISTS idx_sp_ratings_year ON {RAW_DATA_SCHEMA}.{TABLE_NAME}(year);
    CREATE INDEX IF NOT EXISTS idx_sp_ratings_team ON {RAW_DATA_SCHEMA}.{TABLE_NAME}(team);
    """
    
    with engine.connect() as conn:
        conn.execute(text(ddl))
        conn.commit()
    
    print(f"[DB] Table {RAW_DATA_SCHEMA}.{TABLE_NAME} ready (created or already exists)")


def fetch_sp_ratings(year: int, api_key: str) -> List[Dict[str, Any]]:
    """Call CFBD /ratings/sp endpoint for a given year."""
    url = f"{BASE_URL}/ratings/sp"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    params = {"year": year}

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Error fetching SP+ ratings for year={year}: "
            f"status={resp.status_code}, body={resp.text}"
        )

    data = resp.json()
    if DEBUG:
        print(f"[fetch_sp_ratings] year={year}, returned {len(data)} teams")
    return data


def flatten_sp_ratings(ratings: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Flatten SP+ ratings JSON into a DataFrame with proper column naming.
    """
    if DEBUG:
        print(f"[flatten_sp_ratings] received {len(ratings)} raw rating records")
        if ratings:
            example = ratings[0]
            print("[flatten_sp_ratings] example raw keys:", list(example.keys()))

    rows: List[Dict[str, Any]] = []

    for r in ratings:
        offense = r.get("offense", {}) or {}
        defense = r.get("defense", {}) or {}
        special_teams = r.get("specialTeams", {}) or {}

        rows.append({
            "year": r.get("year"),
            "team": r.get("team"),
            "conference": r.get("conference"),
            "rating": r.get("rating"),
            "ranking": r.get("ranking"),
            "second_order_wins": r.get("secondOrderWins"),
            "sos": r.get("sos"),
            
            # Offense
            "offense_rating": offense.get("rating"),
            "offense_success": offense.get("success"),
            "offense_explosiveness": offense.get("explosiveness"),
            "offense_rushing": offense.get("rushing"),
            "offense_passing": offense.get("passing"),
            "offense_standard_downs": offense.get("standardDowns"),
            "offense_passing_downs": offense.get("passingDowns"),
            "offense_run_rate": offense.get("runRate"),
            "offense_pace": offense.get("pace"),
            
            # Defense
            "defense_rating": defense.get("rating"),
            "defense_success": defense.get("success"),
            "defense_explosiveness": defense.get("explosiveness"),
            "defense_rushing": defense.get("rushing"),
            "defense_passing": defense.get("passing"),
            "defense_standard_downs": defense.get("standardDowns"),
            "defense_passing_downs": defense.get("passingDowns"),
            "defense_havoc_total": defense.get("havoc", {}).get("total") if isinstance(defense.get("havoc"), dict) else None,
            "defense_havoc_front_seven": defense.get("havoc", {}).get("frontSeven") if isinstance(defense.get("havoc"), dict) else None,
            "defense_havoc_db": defense.get("havoc", {}).get("db") if isinstance(defense.get("havoc"), dict) else None,
            
            # Special Teams
            "special_teams_rating": special_teams.get("rating"),
        })

    df = pd.DataFrame(rows)

    if df.empty:
        if DEBUG:
            print("[flatten_sp_ratings] df is empty after building rows")
        return df

    # ---- Type casting ----
    int_cols = ["year", "ranking"]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    float_cols = [
        "rating", "second_order_wins", "sos",
        "offense_rating", "offense_success", "offense_explosiveness",
        "offense_rushing", "offense_passing", "offense_standard_downs",
        "offense_passing_downs", "offense_run_rate", "offense_pace",
        "defense_rating", "defense_success", "defense_explosiveness",
        "defense_rushing", "defense_passing", "defense_standard_downs",
        "defense_passing_downs", "defense_havoc_total", 
        "defense_havoc_front_seven", "defense_havoc_db",
        "special_teams_rating",
    ]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ---- Debug inspection ----
    if DEBUG:
        print("\n[flatten_sp_ratings] df.dtypes:")
        print(df.dtypes)

        print("\n[flatten_sp_ratings] df null ratio:")
        print(df.isna().mean().sort_values(ascending=False).head(15))

        print("\n[flatten_sp_ratings] sample ratings:")
        print(df.head(5))

    return df


def load_sp_ratings(engine: Engine | None, api_key: str) -> None:
    """
    Fetch SP+ ratings across YEARS, save raw JSON, flatten, write CSV,
    and (optionally) push into Postgres.
    """
    all_ratings: List[Dict[str, Any]] = []

    for year in YEARS:
        print(f"=== Fetching SP+ ratings for year {year} ===")
        try:
            ratings = fetch_sp_ratings(year=year, api_key=api_key)
        except RuntimeError as e:
            print(e)
            continue

        if not ratings:
            print(f"  Year {year}: no ratings found")
        else:
            print(f"  Year {year}: {len(ratings)} teams")
            all_ratings.extend(ratings)

        # be polite to the API
        time.sleep(0.2)

    if not all_ratings:
        print("No SP+ ratings fetched; nothing to load.")
        return

    # ---- Save raw JSON for inspection ----
    with RAW_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(all_ratings, f, indent=2)
    print(f"\nSaved raw JSON to: {RAW_JSON_PATH.resolve()}")

    # ---- Flatten and export CSV ----
    df_ratings = flatten_sp_ratings(all_ratings)
    print(f"\nAfter flattening: {len(df_ratings)} team-year records")

    if not df_ratings.empty:
        df_ratings.to_csv(RATINGS_CSV_PATH, index=False)
        print(f"Saved ratings CSV to: {RATINGS_CSV_PATH.resolve()}")

    # ---- Stop here while in DEBUG mode ----
    if DEBUG:
        print("\n[DEBUG] Skipping DB write. Inspect CSV and adjust as needed.")
        return

    # =========================
    # Postgres load
    # =========================
    if engine is None:
        raise RuntimeError("Engine is None but DEBUG is False – cannot write to DB.")

    print(f"\n[DB] Engine URL: {engine.url}")
    
    ensure_schema_exists(engine)
    
    # Create table if needed
    create_sp_ratings_table(engine)
    
    print(f"[DB] About to write {len(df_ratings)} rows to {RAW_DATA_SCHEMA}.{TABLE_NAME}")

    # NOTE: Using if_exists="append" - consider changing to "replace" if you want to 
    # truncate each run, or implement upsert logic for incremental loads
    try:
        df_ratings.to_sql(
            TABLE_NAME,
            engine,
            schema=RAW_DATA_SCHEMA,
            if_exists="append",   # Change to "replace" if you want truncate/reload
            index=False,
            method="multi",
        )
        print(f"[DB] Finished writing {len(df_ratings)} rows into {RAW_DATA_SCHEMA}.{TABLE_NAME}")
    except Exception as e:
        print("[DB] ERROR while writing df_ratings to Postgres:")
        print(repr(e))

    print("Done loading SP+ ratings.")


# =========================
# MAIN
# =========================

def main() -> None:
    api_key = get_api_key()
    # Only need the engine when we're actually writing to Postgres
    engine = get_engine() if not DEBUG else None

    print("\n=== Processing SP+ Ratings ===")
    load_sp_ratings(engine, api_key)

    print("\nAll processing complete.")


if __name__ == "__main__":
    main()
