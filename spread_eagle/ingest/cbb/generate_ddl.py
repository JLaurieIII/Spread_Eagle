"""
Generate PostgreSQL DDL from CSV/Parquet files.

Usage:
    python -m spread_eagle.ingest.cbb.generate_ddl

Creates:
    - data/cbb/ddl/create_tables.sql (main tables + CDC tables)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd


# Map pandas dtypes to simple PostgreSQL types
DTYPE_MAP = {
    "int64": "INTEGER",
    "float64": "NUMERIC",
    "bool": "BOOLEAN",
    "object": "TEXT",  # Will refine based on content
    "datetime64[ns]": "TIMESTAMP",
    "datetime64[ns, UTC]": "TIMESTAMPTZ",
}

# Known columns that should be specific types
COLUMN_OVERRIDES = {
    "id": "INTEGER",
    "gameId": "INTEGER",
    "teamId": "INTEGER",
    "athleteId": "INTEGER",
    "venueId": "INTEGER",
    "conferenceId": "INTEGER",
    "playerId": "INTEGER",
    "season": "INTEGER",
    "capacity": "INTEGER",
    "homeScore": "INTEGER",
    "awayScore": "INTEGER",
    "homeTeamId": "INTEGER",
    "awayTeamId": "INTEGER",
    "points": "INTEGER",
    "rebounds": "INTEGER",
    "assists": "INTEGER",
    "steals": "INTEGER",
    "blocks": "INTEGER",
    "turnovers": "INTEGER",
    "fouls": "INTEGER",
    "minutes": "INTEGER",
    "games": "INTEGER",
    "starts": "INTEGER",
    "wins": "INTEGER",
    "losses": "INTEGER",
    "spread": "NUMERIC(10,2)",
    "overUnder": "NUMERIC(10,2)",
    "homeMoneyline": "INTEGER",
    "awayMoneyline": "INTEGER",
    "spreadOpen": "NUMERIC(10,2)",
    "overUnderOpen": "NUMERIC(10,2)",
    "pace": "NUMERIC(10,2)",
    "offensiveRating": "NUMERIC(10,2)",
    "defensiveRating": "NUMERIC(10,2)",
    "netRating": "NUMERIC(10,2)",
    "effectiveFieldGoalPct": "NUMERIC(10,2)",
    "trueShootingPct": "NUMERIC(10,4)",
    "usage": "NUMERIC(10,2)",
    "startDate": "TIMESTAMPTZ",
    "startTimeTbd": "BOOLEAN",
    "neutralSite": "BOOLEAN",
    "conferenceGame": "BOOLEAN",
    "dome": "BOOLEAN",
    "grass": "BOOLEAN",
    "homeWinner": "BOOLEAN",
    "awayWinner": "BOOLEAN",
    "starter": "BOOLEAN",
}

# Table configurations
TABLES = {
    "conferences": {
        "source": "data/cbb/raw/conferences/conferences.csv",
        "primary_key": "id",
        "schema": "cbb",
    },
    "venues": {
        "source": "data/cbb/raw/venues/venues.csv",
        "primary_key": "id",
        "schema": "cbb",
    },
    "teams": {
        "source": "data/cbb/raw/teams/teams.csv",
        "primary_key": "id",
        "schema": "cbb",
    },
    "games": {
        "source": "data/cbb/raw/games/games_2022_2026.csv",
        "primary_key": "id",
        "schema": "cbb",
    },
    "betting_lines": {
        "source": "data/cbb/raw/lines/lines_2022_2026.csv",
        "primary_key": None,  # Composite
        "composite_key": ["gameId", "provider"],
        "schema": "cbb",
    },
    "game_team_stats": {
        "source": "data/cbb/raw/team_stats/team_stats_2022_2026.csv",
        "primary_key": None,
        "composite_key": ["gameId", "teamId"],
        "schema": "cbb",
    },
    "game_player_stats": {
        "source": "data/cbb/raw/game_players/game_players_2022_2026.csv",
        "primary_key": None,
        "composite_key": ["gameId", "athleteId"],
        "schema": "cbb",
    },
    "team_season_stats": {
        "source": "data/cbb/raw/team_season_stats/team_season_stats_2022_2026.csv",
        "primary_key": None,
        "composite_key": ["teamId", "season"],
        "schema": "cbb",
    },
    "player_season_stats": {
        "source": "data/cbb/raw/player_season_stats/player_season_stats_2022_2026.csv",
        "primary_key": None,
        "composite_key": ["athleteId", "teamId", "season"],
        "schema": "cbb",
    },
}


def infer_pg_type(col_name: str, dtype: str, sample_values: pd.Series) -> str:
    """Infer PostgreSQL type from pandas dtype and column name."""
    # Check overrides first
    if col_name in COLUMN_OVERRIDES:
        return COLUMN_OVERRIDES[col_name]

    # Check camelCase versions
    snake = to_snake_case(col_name)
    if snake in COLUMN_OVERRIDES:
        return COLUMN_OVERRIDES[snake]

    # Basic dtype mapping
    pg_type = DTYPE_MAP.get(str(dtype), "TEXT")

    # Refine TEXT types based on content
    if pg_type == "TEXT":
        # Check if it looks like JSON
        if sample_values.notna().any():
            first_val = str(sample_values.dropna().iloc[0]) if len(sample_values.dropna()) > 0 else ""
            if first_val.startswith("{") or first_val.startswith("["):
                return "JSONB"

        # Check max length for VARCHAR optimization (optional)
        # For simplicity, just use TEXT

    return pg_type


def to_snake_case(name: str) -> str:
    """Convert camelCase to snake_case."""
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            result.append("_")
        result.append(char.lower())
    return "".join(result)


def generate_create_table(
    table_name: str,
    columns: List[tuple],
    primary_key: str | None,
    composite_key: List[str] | None,
    schema: str,
    is_cdc: bool = False,
) -> str:
    """Generate CREATE TABLE statement."""
    full_name = f"{schema}.{table_name}"
    if is_cdc:
        full_name = f"{schema}.stg_{table_name}"

    lines = [f"CREATE TABLE IF NOT EXISTS {full_name} ("]

    # Add columns
    col_lines = []
    for col_name, pg_type in columns:
        snake_name = to_snake_case(col_name)
        col_lines.append(f"    {snake_name} {pg_type}")

    # Add load_date column
    col_lines.append("    load_date TIMESTAMPTZ DEFAULT NOW()")

    lines.append(",\n".join(col_lines))

    # Add primary key constraint
    if primary_key and not is_cdc:
        pk_snake = to_snake_case(primary_key)
        lines.append(f",\n    PRIMARY KEY ({pk_snake})")
    elif composite_key and not is_cdc:
        pk_cols = ", ".join(to_snake_case(k) for k in composite_key)
        lines.append(f",\n    PRIMARY KEY ({pk_cols})")

    lines.append(");")

    return "\n".join(lines)


def generate_upsert(
    table_name: str,
    columns: List[tuple],
    primary_key: str | None,
    composite_key: List[str] | None,
    schema: str,
) -> str:
    """Generate UPSERT (INSERT ON CONFLICT) statement."""
    main_table = f"{schema}.{table_name}"
    stg_table = f"{schema}.stg_{table_name}"

    col_names = [to_snake_case(c[0]) for c in columns]
    col_list = ", ".join(col_names)

    # Determine conflict columns
    if primary_key:
        conflict_cols = to_snake_case(primary_key)
    elif composite_key:
        conflict_cols = ", ".join(to_snake_case(k) for k in composite_key)
    else:
        return f"-- No primary key defined for {table_name}, manual upsert logic needed"

    # Generate SET clause (exclude key columns)
    if primary_key:
        update_cols = [c for c in col_names if c != to_snake_case(primary_key)]
    else:
        key_cols = [to_snake_case(k) for k in (composite_key or [])]
        update_cols = [c for c in col_names if c not in key_cols]

    set_clause = ",\n        ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)
    set_clause += ",\n        load_date = NOW()"

    return f"""-- Upsert from staging to main table
INSERT INTO {main_table} ({col_list}, load_date)
SELECT {col_list}, NOW()
FROM {stg_table}
ON CONFLICT ({conflict_cols})
DO UPDATE SET
        {set_clause};

-- Truncate staging table after upsert
TRUNCATE TABLE {stg_table};"""


def main():
    output_dir = Path("data/cbb/ddl")
    output_dir.mkdir(parents=True, exist_ok=True)

    ddl_parts = []
    upsert_parts = []

    # Schema creation
    ddl_parts.append("-- CBB Database Schema")
    ddl_parts.append("-- Generated by generate_ddl.py")
    ddl_parts.append("")
    ddl_parts.append("CREATE SCHEMA IF NOT EXISTS cbb;")
    ddl_parts.append("")

    for table_name, config in TABLES.items():
        source_path = Path(config["source"])

        if not source_path.exists():
            print(f"  WARNING: {source_path} not found, skipping {table_name}")
            continue

        print(f"  Processing: {table_name}")

        # Read CSV to get columns and types
        df = pd.read_csv(source_path, nrows=100)  # Just need schema

        columns = []
        for col in df.columns:
            pg_type = infer_pg_type(col, df[col].dtype, df[col])
            columns.append((col, pg_type))

        # Generate main table DDL
        ddl_parts.append(f"-- Table: {table_name}")
        ddl_parts.append(generate_create_table(
            table_name,
            columns,
            config.get("primary_key"),
            config.get("composite_key"),
            config["schema"],
            is_cdc=False,
        ))
        ddl_parts.append("")

        # Generate CDC staging table DDL
        ddl_parts.append(f"-- Staging table for CDC: stg_{table_name}")
        ddl_parts.append(generate_create_table(
            table_name,
            columns,
            config.get("primary_key"),
            config.get("composite_key"),
            config["schema"],
            is_cdc=True,
        ))
        ddl_parts.append("")

        # Generate upsert statement
        upsert_parts.append(f"-- Upsert: {table_name}")
        upsert_parts.append(generate_upsert(
            table_name,
            columns,
            config.get("primary_key"),
            config.get("composite_key"),
            config["schema"],
        ))
        upsert_parts.append("")

    # Write DDL file
    ddl_path = output_dir / "create_tables.sql"
    with ddl_path.open("w") as f:
        f.write("\n".join(ddl_parts))
    print(f"\n  Saved: {ddl_path}")

    # Write upsert file
    upsert_path = output_dir / "upsert_from_staging.sql"
    with upsert_path.open("w") as f:
        f.write("-- Upsert procedures for CDC pattern\n")
        f.write("-- Load data into stg_* tables, then run these upserts\n\n")
        f.write("\n".join(upsert_parts))
    print(f"  Saved: {upsert_path}")

    print("\n  DONE!")
    print("\n  To run the DDL on your RDS:")
    print("    psql -h spread-eagle-db.cluster-cbwyw8ky62xm.us-east-2.rds.amazonaws.com \\")
    print("         -U postgres -d postgres -f data/cbb/ddl/create_tables.sql")


if __name__ == "__main__":
    main()
