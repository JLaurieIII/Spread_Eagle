"""
Games data loader - Supports full and incremental (CDC) modes.
Uses DATE-RANGE pagination for reliable data fetching.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from .common import (
    RAW_SCHEMA,
    START_YEAR,
    clean_column_names,
    dedupe_records,
    fetch_by_date_ranges,
    flatten_json,
    get_current_season,
    get_data_paths_cbb,
    get_engine,
    ensure_schema_exists,
    upsert_dataframe,
)


def load_games(
    start_year: int = START_YEAR,
    end_year: int = None,
    mode: str = "full",
    write_files: bool = True,
    write_db: bool = True,
) -> Dict[str, Any]:
    """
    Load games data using date-range pagination.

    Args:
        start_year: First season to load (default: 2022)
        end_year: Last season to load (default: current season)
        mode: "full" for all data, "incremental" for current season only
        write_files: Write JSON/CSV files
        write_db: Write to Postgres

    Returns:
        Summary dict with counts
    """
    if end_year is None:
        end_year = get_current_season()

    paths = get_data_paths_cbb()

    # Determine year range based on mode
    if mode == "incremental":
        current = get_current_season()
        years = [current]
    else:
        years = list(range(start_year, end_year + 1))

    print("=" * 60)
    print(f"  GAMES {'INCREMENTAL' if mode == 'incremental' else 'FULL'} LOAD ({years[0]}-{years[-1]})")
    print("=" * 60)

    all_games: List[Dict[str, Any]] = []

    for year in years:
        print(f"\n  [{year}]")

        # Use date-range pagination (the proven approach)
        games = fetch_by_date_ranges("/games", year, id_field="id")

        print(f"    TOTAL: {len(games):,} games")

        # Save individual year file
        if write_files:
            year_path = paths.raw / f"games_{year}_v2.json"
            with year_path.open("w", encoding="utf-8") as f:
                json.dump(games, f, indent=2)
            print(f"    Saved: {year_path.name}")

        all_games.extend(games)

    # Final dedupe across seasons
    seen = set()
    deduped = []
    for r in all_games:
        rid = r.get("id")
        if rid not in seen:
            seen.add(rid)
            deduped.append(r)
    all_games = deduped

    print(f"\n  GRAND TOTAL: {len(all_games):,} games")

    if not all_games:
        return {"games": 0, "status": "no_data", "mode": mode}

    # Write combined files
    if write_files:
        # JSON
        all_path = paths.raw / f"games_{start_year}_{end_year}_v2.json"
        with all_path.open("w", encoding="utf-8") as f:
            json.dump(all_games, f, indent=2)
        print(f"  Saved: {all_path.name}")

        # CSV
        df = flatten_json(all_games)
        df = clean_column_names(df)
        csv_path = paths.raw / f"games_{start_year}_{end_year}_v2.csv"
        df.to_csv(csv_path, index=False)
        print(f"  Saved: {csv_path.name} ({len(df):,} rows)")

    # Write to DB
    if write_db:
        print(f"\n  Loading to database...")
        engine = get_engine()
        ensure_schema_exists(engine, RAW_SCHEMA)

        df = flatten_json(all_games)
        df = clean_column_names(df)

        upsert_dataframe(
            engine=engine,
            df=df,
            table_name="games",
            schema=RAW_SCHEMA,
            primary_keys=["id"],
        )

    print("\n  DONE!")
    return {"games": len(all_games), "status": "success", "mode": mode}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load CBB games data")
    parser.add_argument("--start_year", type=int, default=START_YEAR)
    parser.add_argument("--end_year", type=int, default=None)
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    parser.add_argument("--no-files", action="store_true", help="Skip file output")
    parser.add_argument("--no-db", action="store_true", help="Skip database load")
    args = parser.parse_args()

    result = load_games(
        start_year=args.start_year,
        end_year=args.end_year,
        mode=args.mode,
        write_files=not args.no_files,
        write_db=not args.no_db,
    )
    print(f"\nResult: {result}")
