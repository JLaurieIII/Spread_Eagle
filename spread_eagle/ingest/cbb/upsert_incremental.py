"""
Upsert incremental data into PostgreSQL.

Reads parquet files from data/cbb/incremental/{date}/ and loads them
into staging tables, then runs upsert SQL to merge into main tables.

This replaces the TRUNCATE + INSERT pattern for daily loads.
Existing data is preserved; only matching rows are updated.

Usage:
    python -m spread_eagle.ingest.cbb.upsert_incremental
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Load .env for local runs (Docker passes env vars directly via DAG)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

# Read from environment (Docker overrides via DAG env params)
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "spread_eagle")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

# Incremental file -> staging table mapping (pk needed for NULL filtering)
TABLES = {
    "games": {
        "dir": "games",
        "file": "games.parquet",
        "staging_table": "cbb.stg_games",
        "main_table": "cbb.games",
        "pk": ["id"],
    },
    "betting_lines": {
        "dir": "lines",
        "file": "lines.parquet",
        "staging_table": "cbb.stg_betting_lines",
        "main_table": "cbb.betting_lines",
        "pk": ["game_id", "provider"],
    },
    "game_team_stats": {
        "dir": "team_stats",
        "file": "team_stats.parquet",
        "staging_table": "cbb.stg_game_team_stats",
        "main_table": "cbb.game_team_stats",
        "pk": ["game_id", "team_id"],
    },
    "game_player_stats": {
        "dir": "game_players",
        "file": "game_players.parquet",
        "staging_table": "cbb.stg_game_player_stats",
        "main_table": "cbb.game_player_stats",
        "pk": ["game_id", "athlete_id"],
    },
    "team_season_stats": {
        "dir": "team_season_stats",
        "file": "team_season_stats.parquet",
        "staging_table": "cbb.stg_team_season_stats",
        "main_table": "cbb.team_season_stats",
        "pk": ["team_id", "season"],
    },
    "player_season_stats": {
        "dir": "player_season_stats",
        "file": "player_season_stats.parquet",
        "staging_table": "cbb.stg_player_season_stats",
        "main_table": "cbb.player_season_stats",
        "pk": ["athlete_id", "team_id", "season"],
    },
}

# Columns that need JSONB conversion
JSONB_COLUMNS = [
    "home_period_points",
    "away_period_points",
    "team_stats_points_by_period",
    "opponent_stats_points_by_period",
    "field_goals",
    "two_point_field_goals",
    "three_point_field_goals",
    "free_throws",
    "rebounds",
]


def to_snake_case(name: str) -> str:
    """Convert camelCase to snake_case."""
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_connection():
    """Get PostgreSQL connection."""
    kwargs = dict(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=30,
    )
    # Use SSL for RDS connections
    if "rds.amazonaws.com" in DB_HOST:
        kwargs["sslmode"] = "require"
    return psycopg2.connect(**kwargs)


def convert_value(val):
    """Convert Python/numpy values for PostgreSQL insertion."""
    if val is None:
        return None
    if isinstance(val, np.ndarray):
        return json.dumps(val.tolist())
    if isinstance(val, (list, dict)):
        return json.dumps(val)
    try:
        if pd.isna(val):
            return None
    except (ValueError, TypeError):
        pass
    if isinstance(val, pd.Timestamp):
        return val.to_pydatetime()
    if hasattr(val, 'item') and hasattr(val, 'shape') and val.shape == ():
        return val.item()
    return val


def load_to_staging(name: str, data_dir: Path, conn) -> int:
    """Load a single incremental parquet file into its staging table."""
    config = TABLES[name]
    file_path = data_dir / config["dir"] / config["file"]
    staging_table = config["staging_table"]

    if not file_path.exists():
        print(f"  SKIP: {file_path} not found")
        return 0

    df = pd.read_parquet(file_path)
    df.columns = [to_snake_case(col) for col in df.columns]

    if df.empty:
        print(f"  SKIP: {name} - empty file")
        return 0

    # Convert JSONB columns
    for col in JSONB_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
            )

    # Clean source_id
    if "source_id" in df.columns:
        def safe_int(val):
            if pd.isna(val):
                return None
            try:
                return int(val)
            except (ValueError, TypeError):
                return None
        df["source_id"] = df["source_id"].apply(safe_int)

    # Filter out rows with NULL primary key values (required for upsert ON CONFLICT)
    pk_cols = config.get("pk", [])
    for pk_col in pk_cols:
        if pk_col in df.columns:
            before = len(df)
            df = df[df[pk_col].notna()]
            dropped = before - len(df)
            if dropped > 0:
                print(f"(dropped {dropped} NULL {pk_col}) ", end="")

    # Replace NaN with None
    df = df.where(pd.notnull(df), None)

    columns = list(df.columns)
    cur = conn.cursor()

    # Truncate staging table (clean slate for this load)
    cur.execute(f"TRUNCATE TABLE {staging_table}")

    # Get the staging table's actual columns from the database
    cur.execute(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'cbb' AND table_name = '{staging_table.split('.')[-1]}'
        ORDER BY ordinal_position
    """)
    db_columns = {row[0] for row in cur.fetchall()}

    # Only insert columns that exist in both dataframe and staging table
    # (skip load_date - it has a DEFAULT)
    valid_columns = [c for c in columns if c in db_columns]
    if not valid_columns:
        print(f"  SKIP: {name} - no matching columns between parquet and staging table")
        conn.rollback()
        cur.close()
        return 0

    cols_str = ", ".join(valid_columns)
    insert_sql = f"INSERT INTO {staging_table} ({cols_str}) VALUES %s"

    # Build values with only valid columns
    col_indices = [columns.index(c) for c in valid_columns]
    values = [
        tuple(convert_value(row[i]) for i in col_indices)
        for row in df.values
    ]

    execute_values(cur, insert_sql, values, page_size=1000)
    conn.commit()
    cur.close()

    return len(df)


def run_upsert(conn, ddl_dir: Path) -> None:
    """Run upsert SQL to merge staging data into main tables."""
    upsert_path = ddl_dir / "upsert_from_staging.sql"
    if not upsert_path.exists():
        print(f"  ERROR: Upsert SQL not found: {upsert_path}")
        return

    sql = upsert_path.read_text()
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()
    print("  Upsert complete - staging data merged into main tables")


def main():
    """Load incremental data into staging tables and upsert to main tables."""
    # Find today's incremental data directory
    today = datetime.now().strftime("%Y-%m-%d")
    data_dir = Path(__file__).parent.parent.parent.parent / "data" / "cbb" / "incremental" / today
    ddl_dir = Path(__file__).parent.parent.parent.parent / "data" / "cbb" / "ddl"

    print("=" * 60)
    print("  UPSERT INCREMENTAL DATA")
    print("=" * 60)
    print(f"  Data directory: {data_dir}")
    print(f"  Target: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print()

    if not data_dir.exists():
        print(f"  ERROR: No incremental data found for {today}")
        print(f"  Expected: {data_dir}")
        print(f"  Run the incremental ingest first.")
        return

    conn = get_connection()

    # Load each table into its staging table
    load_order = [
        "games",
        "betting_lines",
        "game_team_stats",
        "game_player_stats",
        "team_season_stats",
        "player_season_stats",
    ]

    total_staged = 0
    print("Loading to staging tables...")
    start = datetime.now()

    for name in load_order:
        print(f"  {name}...", end=" ", flush=True)
        count = load_to_staging(name, data_dir, conn)
        print(f"{count:,} rows")
        total_staged += count

    print(f"\n  Staged {total_staged:,} total rows")

    # Run upsert to merge staging into main tables
    print("\nRunning upsert...")
    run_upsert(conn, ddl_dir)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nDone! Upserted in {elapsed:.1f}s")

    conn.close()


if __name__ == "__main__":
    main()
