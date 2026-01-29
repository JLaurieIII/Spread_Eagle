"""
Game Players loader - Per-game player box scores.
Uses DATE-RANGE pagination for reliable data fetching.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

import pandas as pd

from .common import (
    RAW_SCHEMA,
    START_YEAR,
    clean_column_names,
    fetch_by_date_ranges,
    get_current_season,
    get_data_paths_cbb,
    get_engine,
    ensure_schema_exists,
    upsert_dataframe,
)


def flatten_game_players(games: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Flatten game players data - expand the nested players array.
    Creates one row per game x team x player combination.
    """
    flat_records = []
    for game in games:
        base = {k: v for k, v in game.items() if k != "players"}
        if game.get("players"):
            for player in game["players"]:
                flat_records.append({**base, **player})
        else:
            flat_records.append(base)

    return pd.DataFrame(flat_records)


def load_game_players(
    start_year: int = START_YEAR,
    end_year: int = None,
    mode: str = "full",
    write_files: bool = True,
    write_db: bool = True,
) -> Dict[str, Any]:
    """
    Load game players using date-range pagination.

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
    print(f"  GAME PLAYERS {'INCREMENTAL' if mode == 'incremental' else 'FULL'} LOAD ({years[0]}-{years[-1]})")
    print("=" * 60)

    all_stats: List[Dict[str, Any]] = []

    for year in years:
        print(f"\n  [{year}]")

        # Use date-range pagination with composite key
        stats = fetch_by_date_ranges(
            "/games/players",
            year,
            composite_key=["gameId", "teamId"],
        )

        print(f"    TOTAL: {len(stats):,} game-team records")

        # Save individual year file
        if write_files:
            year_path = paths.raw / f"game_players_{year}_v2.json"
            with year_path.open("w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2)
            print(f"    Saved: {year_path.name}")

        all_stats.extend(stats)

    # Final dedupe across seasons
    seen = set()
    deduped = []
    for r in all_stats:
        key = (r.get("gameId"), r.get("teamId"))
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    all_stats = deduped

    print(f"\n  GRAND TOTAL: {len(all_stats):,} game-team records")

    if not all_stats:
        return {"game_players": 0, "status": "no_data", "mode": mode}

    # Write combined files
    if write_files:
        all_path = paths.raw / f"game_players_{start_year}_{end_year}_v2.json"
        with all_path.open("w", encoding="utf-8") as f:
            json.dump(all_stats, f, indent=2)
        print(f"  Saved: {all_path.name}")

        df = flatten_game_players(all_stats)
        df = clean_column_names(df)
        csv_path = paths.raw / f"game_players_{start_year}_{end_year}_v2.csv"
        df.to_csv(csv_path, index=False)
        print(f"  Saved: {csv_path.name} ({len(df):,} rows)")

    # Write to DB
    if write_db:
        print(f"\n  Loading to database...")
        engine = get_engine()
        ensure_schema_exists(engine, RAW_SCHEMA)

        df = flatten_game_players(all_stats)
        df = clean_column_names(df)

        # Rename for consistency
        if "gameid" in df.columns:
            df = df.rename(columns={"gameid": "game_id"})
        if "teamid" in df.columns:
            df = df.rename(columns={"teamid": "team_id"})
        if "athleteid" in df.columns:
            df = df.rename(columns={"athleteid": "athlete_id"})

        upsert_dataframe(
            engine=engine,
            df=df,
            table_name="game_players",
            schema=RAW_SCHEMA,
            primary_keys=["game_id", "team_id", "athlete_id"],
        )

    print("\n  DONE!")
    return {"game_players": len(all_stats), "status": "success", "mode": mode}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load CBB game player stats")
    parser.add_argument("--start_year", type=int, default=START_YEAR)
    parser.add_argument("--end_year", type=int, default=None)
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    parser.add_argument("--no-files", action="store_true", help="Skip file output")
    parser.add_argument("--no-db", action="store_true", help="Skip database load")
    args = parser.parse_args()

    result = load_game_players(
        start_year=args.start_year,
        end_year=args.end_year,
        mode=args.mode,
        write_files=not args.no_files,
        write_db=not args.no_db,
    )
    print(f"\nResult: {result}")
