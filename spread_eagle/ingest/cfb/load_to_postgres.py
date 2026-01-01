"""
Load CFB Parquet files to PostgreSQL.

Simple truncate + full load pattern.
"""
import json
import re
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from spread_eagle.config.settings import settings


def to_snake_case(name: str) -> str:
    """Convert camelCase to snake_case."""
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# Parquet file -> table mapping
TABLES = {
    "conferences": {
        "file": "conferences/conferences.parquet",
        "table": "cfb.conferences",
        "pk": ["id"],
    },
    "venues": {
        "file": "venues/venues.parquet",
        "table": "cfb.venues",
        "pk": ["id"],
    },
    "teams": {
        "file": "teams/teams.parquet",
        "table": "cfb.teams",
        "pk": ["id"],
    },
    "games": {
        "file": "games/games_2022_2025.parquet",
        "table": "cfb.games",
        "pk": ["id"],
    },
    "betting_lines": {
        "file": "lines/lines_2022_2025.parquet",
        "table": "cfb.betting_lines",
        "pk": ["game_id", "provider"],
    },
    "game_team_stats": {
        "file": "team_stats/team_stats_2022_2025.parquet",
        "table": "cfb.game_team_stats",
        "pk": ["game_id", "team"],
    },
    "game_player_stats": {
        "file": "game_players/game_players_2022_2025.parquet",
        "table": "cfb.game_player_stats",
        "pk": ["game_id", "athlete_id", "category", "stat_type"],
    },
    "team_season_stats": {
        "file": "team_season_stats/team_season_stats_2022_2025.parquet",
        "table": "cfb.team_season_stats",
        "pk": ["season", "team"],
    },
    "player_season_stats": {
        "file": "player_season_stats/player_season_stats_2022_2025.parquet",
        "table": "cfb.player_season_stats",
        "pk": ["season", "player_id", "team"],
    },
}


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


def convert_value(val):
    """Convert numpy types to Python native types."""
    if val is None:
        return None
    # Handle numpy arrays
    if isinstance(val, np.ndarray):
        return json.dumps(val.tolist())
    # Handle lists/dicts
    if isinstance(val, (list, dict)):
        return json.dumps(val)
    # Check for NaN
    try:
        if pd.isna(val):
            return None
    except (ValueError, TypeError):
        pass
    if isinstance(val, (pd.Timestamp,)):
        return val.to_pydatetime()
    # numpy scalar
    if hasattr(val, 'item') and hasattr(val, 'shape') and val.shape == ():
        return val.item()
    return val


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

    # Filter out rows with NULL primary key values
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

    # Get columns
    columns = list(df.columns)

    cur = conn.cursor()

    # Truncate
    cur.execute(f"TRUNCATE TABLE {table} CASCADE")

    # Build INSERT
    cols_str = ", ".join(columns)
    insert_sql = f"INSERT INTO {table} ({cols_str}) VALUES %s"

    # Convert to tuples
    values = [tuple(convert_value(v) for v in row) for row in df.values]

    # Bulk insert
    execute_values(cur, insert_sql, values, page_size=1000)

    conn.commit()
    cur.close()

    return len(df)


def run_ddl(conn, ddl_path: Path):
    """Run DDL to create schema and tables."""
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
    """Load all CFB tables."""
    data_dir = Path(__file__).parent.parent.parent.parent / "data" / "cfb" / "raw"
    ddl_path = Path(__file__).parent.parent.parent.parent / "data" / "cfb" / "ddl" / "create_tables.sql"

    print(f"Data directory: {data_dir}")
    print(f"Connecting to: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    print()

    conn = get_connection()

    # Run DDL first
    run_ddl(conn, ddl_path)
    print()

    # Load order
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
