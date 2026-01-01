"""
Load Parquet files to PostgreSQL.

Simple truncate + full load pattern.
"""
import json
import re
from pathlib import Path
from datetime import datetime

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values


def to_snake_case(name: str) -> str:
    """Convert camelCase to snake_case."""
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from spread_eagle.config.settings import settings


# Parquet file -> table mapping
TABLES = {
    "conferences": {
        "file": "conferences/conferences.parquet",
        "table": "cbb.conferences",
        "pk": ["id"],
    },
    "venues": {
        "file": "venues/venues.parquet",
        "table": "cbb.venues",
        "pk": ["id"],
    },
    "teams": {
        "file": "teams/teams.parquet",
        "table": "cbb.teams",
        "pk": ["id"],
    },
    "games": {
        "file": "games/games_2022_2026.parquet",
        "table": "cbb.games",
        "pk": ["id"],
    },
    "betting_lines": {
        "file": "lines/lines_2022_2026.parquet",
        "table": "cbb.betting_lines",
        "pk": ["game_id", "provider"],
    },
    "game_team_stats": {
        "file": "team_stats/team_stats_2022_2026.parquet",
        "table": "cbb.game_team_stats",
        "pk": ["game_id", "team_id"],
    },
    "game_player_stats": {
        "file": "game_players/game_players_2022_2026.parquet",
        "table": "cbb.game_player_stats",
        "pk": ["game_id", "athlete_id"],
    },
    "team_season_stats": {
        "file": "team_season_stats/team_season_stats_2022_2026.parquet",
        "table": "cbb.team_season_stats",
        "pk": ["team_id", "season"],
    },
    "player_season_stats": {
        "file": "player_season_stats/player_season_stats_2022_2026.parquet",
        "table": "cbb.player_season_stats",
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


def get_connection():
    """Get PostgreSQL connection."""
    return psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        connect_timeout=30,
        sslmode="require",
    )


def convert_jsonb(df: pd.DataFrame) -> pd.DataFrame:
    """Convert dict/list columns to JSON strings for PostgreSQL."""
    for col in JSONB_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
            )
    return df


def clean_source_id(df: pd.DataFrame) -> pd.DataFrame:
    """Convert non-numeric source_id values to NULL."""
    if "source_id" in df.columns:
        def safe_int(val):
            if pd.isna(val):
                return None
            try:
                return int(val)
            except (ValueError, TypeError):
                return None
        df["source_id"] = df["source_id"].apply(safe_int)
    return df


def load_table(name: str, data_dir: Path, conn) -> int:
    """Load a single table. Returns row count."""
    config = TABLES[name]
    file_path = data_dir / config["file"]
    table = config["table"]

    if not file_path.exists():
        print(f"  SKIP: {file_path} not found")
        return 0

    # Read Parquet
    df = pd.read_parquet(file_path)

    # Convert column names to snake_case
    df.columns = [to_snake_case(col) for col in df.columns]

    # Handle empty files
    if df.empty:
        print(f"  SKIP: {name} - empty file")
        return 0

    # Convert JSONB columns
    df = convert_jsonb(df)

    # Clean source_id (handle non-numeric values)
    df = clean_source_id(df)

    # Filter out rows with NULL primary key values
    pk_cols = config.get("pk", [])
    for pk_col in pk_cols:
        if pk_col in df.columns:
            before = len(df)
            df = df[df[pk_col].notna()]
            dropped = before - len(df)
            if dropped > 0:
                print(f"(dropped {dropped} NULL {pk_col}) ", end="")

    # Replace NaN with None for proper NULL handling
    df = df.where(pd.notnull(df), None)

    # Convert numpy types to Python native types
    import numpy as np

    def convert_value(val):
        if val is None:
            return None
        # Handle numpy arrays (JSONB columns)
        if isinstance(val, np.ndarray):
            return json.dumps(val.tolist())
        # Handle lists/dicts (JSONB columns)
        if isinstance(val, (list, dict)):
            return json.dumps(val)
        # Check for NaN (scalar only)
        try:
            if pd.isna(val):
                return None
        except (ValueError, TypeError):
            pass  # Not a scalar, continue
        if isinstance(val, (pd.Timestamp,)):
            return val.to_pydatetime()
        # numpy scalar (single value)
        if hasattr(val, 'item') and hasattr(val, 'shape') and val.shape == ():
            return val.item()
        return val

    # Get columns from dataframe
    columns = list(df.columns)

    cur = conn.cursor()

    # Truncate
    cur.execute(f"TRUNCATE TABLE {table} CASCADE")

    # Build INSERT statement
    cols_str = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    insert_sql = f"INSERT INTO {table} ({cols_str}) VALUES %s"

    # Convert to list of tuples with proper type conversion
    values = [tuple(convert_value(v) for v in row) for row in df.values]

    # Bulk insert
    execute_values(cur, insert_sql, values, page_size=1000)

    conn.commit()
    cur.close()

    return len(df)


def run_ddl(conn, ddl_path: Path):
    """Run DDL to create schema and tables if needed."""
    if not ddl_path.exists():
        print(f"DDL file not found: {ddl_path}")
        return

    ddl = ddl_path.read_text()
    cur = conn.cursor()
    cur.execute(ddl)
    conn.commit()
    cur.close()
    print("Schema and tables created/verified")


def main():
    """Load all tables."""
    data_dir = Path(__file__).parent.parent.parent.parent / "data" / "cbb" / "raw"
    ddl_path = Path(__file__).parent.parent.parent.parent / "data" / "cbb" / "ddl" / "create_tables.sql"

    print(f"Data directory: {data_dir}")
    print(f"Connecting to: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    print()

    conn = get_connection()

    # Run DDL first
    run_ddl(conn, ddl_path)
    print()

    # Load order: reference tables first, then fact tables
    load_order = [
        "conferences",
        "venues",
        "teams",
        "games",
        "betting_lines",
        "game_team_stats",
        "game_player_stats",
        "team_season_stats",
        "player_season_stats",
    ]

    total = 0
    print("Loading tables...")
    start = datetime.now()

    for name in load_order:
        print(f"  {name}...", end=" ", flush=True)
        count = load_table(name, data_dir, conn)
        print(f"{count:,} rows")
        total += count

    elapsed = (datetime.now() - start).total_seconds()

    print()
    print(f"Done! Loaded {total:,} total rows in {elapsed:.1f}s")

    conn.close()


if __name__ == "__main__":
    main()
