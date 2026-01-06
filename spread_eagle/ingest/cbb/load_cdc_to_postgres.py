"""
Load 7-day CDC CBB parquet files into Postgres with upsert semantics.

Files are expected in data/cbb/cdc_7day/<endpoint>/<endpoint>_cdc.parquet
and are produced by run_cbb_cdc_week.py.

Usage:
    python -m spread_eagle.ingest.cbb.load_cdc_to_postgres
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from spread_eagle.config.settings import settings

# Parquet file -> table mapping for CDC outputs
TABLES = {
    "games": {
        "file": "games/games_cdc.parquet",
        "table": "cbb.games",
        "pk": ["id"],
    },
    "lines": {
        "file": "lines/lines_cdc.parquet",
        "table": "cbb.betting_lines",
        "pk": ["game_id", "provider"],
    },
    "team_stats": {
        "file": "team_stats/team_stats_cdc.parquet",
        "table": "cbb.game_team_stats",
        "pk": ["game_id", "team_id"],
    },
    "game_players": {
        "file": "game_players/game_players_cdc.parquet",
        "table": "cbb.game_player_stats",
        "pk": ["game_id", "athlete_id"],
    },
    "team_season_stats": {
        "file": "team_season_stats/team_season_stats_cdc.parquet",
        "table": "cbb.team_season_stats",
        "pk": ["team_id", "season"],
    },
    "player_season_stats": {
        "file": "player_season_stats/player_season_stats_cdc.parquet",
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


def to_snake_case(name: str) -> str:
    """Convert camelCase to snake_case."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


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


def convert_value(val):
    """Convert numpy/pandas values to Python primitives suitable for psycopg2."""
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
    if isinstance(val, (pd.Timestamp,)):
        return val.to_pydatetime()
    if hasattr(val, "item") and hasattr(val, "shape") and val.shape == ():
        return val.item()
    return val


def run_ddl(conn, ddl_path: Path):
    """Run DDL to ensure schema/tables exist."""
    if not ddl_path.exists():
        print(f"DDL file not found: {ddl_path}")
        return
    ddl = ddl_path.read_text()
    cur = conn.cursor()
    cur.execute(ddl)
    conn.commit()
    cur.close()
    print("Schema and tables created/verified")


def upsert_table(name: str, data_dir: Path, conn) -> int:
    """Upsert a single CDC table. Returns row count inserted/updated."""
    config = TABLES[name]
    file_path = data_dir / config["file"]
    table = config["table"]
    pk_cols: List[str] = config["pk"]

    if not file_path.exists():
        print(f"  SKIP: {file_path} not found")
        return 0

    print(f"  Loading {name} from {file_path.name} -> {table}")

    df = pd.read_parquet(file_path)
    df.columns = [to_snake_case(col) for col in df.columns]

    if df.empty:
        print(f"  SKIP: {name} - empty file")
        return 0

    df = convert_jsonb(df)
    df = clean_source_id(df)

    # Filter NULL PKs
    for pk_col in pk_cols:
        if pk_col in df.columns:
            before = len(df)
            df = df[df[pk_col].notna()]
            dropped = before - len(df)
            if dropped:
                print(f"    dropped {dropped} NULL {pk_col}")

    # Replace NaN with None
    df = df.where(pd.notnull(df), None)

    columns = list(df.columns)
    non_pk_cols = [c for c in columns if c not in pk_cols]

    cur = conn.cursor()

    cols_str = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    conflict_cols = ", ".join(pk_cols)
    update_str = ", ".join(f"{col}=EXCLUDED.{col}" for col in non_pk_cols)

    insert_sql = (
        f"INSERT INTO {table} ({cols_str}) VALUES %s "
        f"ON CONFLICT ({conflict_cols}) DO UPDATE SET {update_str}"
    )

    values = [tuple(convert_value(v) for v in row) for row in df.values]
    execute_values(cur, insert_sql, values, page_size=1000)
    conn.commit()
    cur.close()

    print(f"  Upserted {len(df):,} rows into {table}")
    return len(df)


def main():
    data_dir = Path(__file__).parent.parent.parent.parent / "data" / "cbb" / "cdc_7day"
    ddl_path = Path(__file__).parent.parent.parent.parent / "data" / "cbb" / "ddl" / "create_tables.sql"

    print(f"Data directory: {data_dir}")
    print(f"Connecting to: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    print()

    conn = get_connection()
    print("Connected to Postgres")

    # Ensure schema exists
    run_ddl(conn, ddl_path)
    print()

    load_order = [
        "games",
        "lines",
        "team_stats",
        "game_players",
        "team_season_stats",
        "player_season_stats",
    ]

    total = 0
    start = datetime.now()
    print("Upserting CDC tables...")

    for name in load_order:
        count = upsert_table(name, data_dir, conn)
        total += count

    elapsed = (datetime.now() - start).total_seconds()
    print()
    print(f"Done! Upserted {total:,} rows in {elapsed:.1f}s")

    conn.close()


if __name__ == "__main__":
    main()
