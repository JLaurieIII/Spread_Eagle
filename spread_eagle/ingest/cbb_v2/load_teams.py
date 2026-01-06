"""
Teams data loader - Reference data (full reload only).
No pagination needed - simple endpoint.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

import pandas as pd

from .common import (
    RAW_SCHEMA,
    clean_column_names,
    fetch_simple,
    flatten_json,
    get_data_paths_cbb,
    get_engine,
    ensure_schema_exists,
    upsert_dataframe,
)


def load_teams(
    write_files: bool = True,
    write_db: bool = True,
) -> Dict[str, Any]:
    """
    Load teams reference data.

    Args:
        write_files: Write JSON/CSV files
        write_db: Write to Postgres

    Returns:
        Summary dict with counts
    """
    paths = get_data_paths_cbb()

    print("=" * 60)
    print("  TEAMS LOAD (Reference Data)")
    print("=" * 60)

    # Fetch data (no pagination needed)
    print("\n  Fetching teams...")
    teams = fetch_simple("/teams")
    print(f"  Fetched {len(teams):,} teams")

    if not teams:
        return {"teams": 0, "status": "no_data"}

    # Write files
    if write_files:
        json_path = paths.raw / "teams_v2.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(teams, f, indent=2)
        print(f"  Saved: {json_path.name}")

        df = flatten_json(teams)
        df = clean_column_names(df)
        csv_path = paths.raw / "teams_v2.csv"
        df.to_csv(csv_path, index=False)
        print(f"  Saved: {csv_path.name} ({len(df):,} rows)")

    # Write to DB
    if write_db:
        print(f"\n  Loading to database...")
        engine = get_engine()
        ensure_schema_exists(engine, RAW_SCHEMA)

        df = flatten_json(teams)
        df = clean_column_names(df)

        upsert_dataframe(
            engine=engine,
            df=df,
            table_name="teams",
            schema=RAW_SCHEMA,
            primary_keys=["id"],
        )

    print("\n  DONE!")
    return {"teams": len(teams), "status": "success"}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load CBB teams data")
    parser.add_argument("--no-files", action="store_true", help="Skip file output")
    parser.add_argument("--no-db", action="store_true", help="Skip database load")
    args = parser.parse_args()

    result = load_teams(
        write_files=not args.no_files,
        write_db=not args.no_db,
    )
    print(f"\nResult: {result}")
