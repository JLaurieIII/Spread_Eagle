"""
CBB V2 Master Orchestrator

Single entry point for all CBB data ingestion. Designed for Airflow integration.

Usage:
    # Full load all datasets (historical backfill)
    python -m spread_eagle.ingest.cbb_v2.run_ingest --mode full --start_year 2022 --end_year 2025

    # Incremental load (daily/hourly runs)
    python -m spread_eagle.ingest.cbb_v2.run_ingest --mode incremental

    # Load specific datasets only
    python -m spread_eagle.ingest.cbb_v2.run_ingest --mode full --datasets games,lines

    # Skip database writes (file output only)
    python -m spread_eagle.ingest.cbb_v2.run_ingest --mode incremental --no-db

    # Skip file writes (database only)
    python -m spread_eagle.ingest.cbb_v2.run_ingest --mode incremental --no-files

Available datasets:
    - teams          (reference data, always full)
    - venues         (reference data, always full)
    - games          (supports incremental)
    - team_game_stats (supports incremental)
    - lines          (supports incremental)
    - team_season_stats (supports incremental)
    - player_season_stats (supports incremental)
    - game_players   (supports incremental)
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from .load_teams import load_teams
from .load_venues import load_venues
from .load_games import load_games
from .load_team_game_stats import load_team_game_stats
from .load_lines import load_lines
from .load_team_season_stats import load_team_season_stats
from .load_player_season_stats import load_player_season_stats
from .load_game_players import load_game_players

# Dataset loading order (respects dependencies)
# Reference data first, then games, then dependent data
DATASET_ORDER = [
    "teams",
    "venues",
    "games",
    "team_game_stats",
    "lines",
    "team_season_stats",
    "player_season_stats",
    "game_players",
]

# Datasets that support incremental mode
INCREMENTAL_DATASETS = {
    "games",
    "team_game_stats",
    "lines",
    "team_season_stats",
    "player_season_stats",
    "game_players",
}

# Reference datasets (always full reload)
REFERENCE_DATASETS = {"teams", "venues"}


def run_ingest(
    mode: str = "full",
    start_year: int = 2022,
    end_year: Optional[int] = None,
    datasets: Optional[List[str]] = None,
    write_files: bool = True,
    write_db: bool = True,
) -> Dict[str, Any]:
    """
    Run the CBB data ingestion pipeline.

    Args:
        mode: "full" for complete historical load, "incremental" for recent data
        start_year: First season to load (for full mode)
        end_year: Last season to load (defaults to current year)
        datasets: List of datasets to load (None = all)
        write_files: Write JSON/CSV output files
        write_db: Write to Postgres database

    Returns:
        Summary dict with results for each dataset
    """
    if end_year is None:
        end_year = datetime.now().year

    # Validate datasets
    if datasets:
        invalid = set(datasets) - set(DATASET_ORDER)
        if invalid:
            raise ValueError(f"Invalid datasets: {invalid}. Valid options: {DATASET_ORDER}")
        load_datasets = [d for d in DATASET_ORDER if d in datasets]
    else:
        load_datasets = DATASET_ORDER

    print("=" * 60)
    print(f"CBB V2 INGESTION PIPELINE")
    print("=" * 60)
    print(f"Mode: {mode.upper()}")
    print(f"Year Range: {start_year} - {end_year}")
    print(f"Datasets: {', '.join(load_datasets)}")
    print(f"Write Files: {write_files}")
    print(f"Write DB: {write_db}")
    print("=" * 60)

    results: Dict[str, Any] = {
        "start_time": datetime.now().isoformat(),
        "mode": mode,
        "datasets": {},
    }

    total_start = time.time()

    for dataset in load_datasets:
        print(f"\n{'='*60}")
        print(f"LOADING: {dataset.upper()}")
        print(f"{'='*60}")

        dataset_start = time.time()

        try:
            if dataset == "teams":
                result = load_teams(write_files=write_files, write_db=write_db)

            elif dataset == "venues":
                result = load_venues(write_files=write_files, write_db=write_db)

            elif dataset == "games":
                result = load_games(
                    start_year=start_year,
                    end_year=end_year,
                    mode=mode if dataset in INCREMENTAL_DATASETS else "full",
                    write_files=write_files,
                    write_db=write_db,
                )

            elif dataset == "team_game_stats":
                result = load_team_game_stats(
                    start_year=start_year,
                    end_year=end_year,
                    mode=mode if dataset in INCREMENTAL_DATASETS else "full",
                    write_files=write_files,
                    write_db=write_db,
                )

            elif dataset == "lines":
                result = load_lines(
                    start_year=start_year,
                    end_year=end_year,
                    mode=mode if dataset in INCREMENTAL_DATASETS else "full",
                    write_files=write_files,
                    write_db=write_db,
                )

            elif dataset == "team_season_stats":
                result = load_team_season_stats(
                    start_year=start_year,
                    end_year=end_year,
                    mode=mode if dataset in INCREMENTAL_DATASETS else "full",
                    write_files=write_files,
                    write_db=write_db,
                )

            elif dataset == "player_season_stats":
                result = load_player_season_stats(
                    start_year=start_year,
                    end_year=end_year,
                    mode=mode if dataset in INCREMENTAL_DATASETS else "full",
                    write_files=write_files,
                    write_db=write_db,
                )

            elif dataset == "game_players":
                result = load_game_players(
                    start_year=start_year,
                    end_year=end_year,
                    mode=mode if dataset in INCREMENTAL_DATASETS else "full",
                    write_files=write_files,
                    write_db=write_db,
                )

            else:
                result = {"status": "unknown_dataset"}

            result["duration_seconds"] = round(time.time() - dataset_start, 2)
            results["datasets"][dataset] = result

            print(f"\n[DONE] {dataset}: {result}")

        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "duration_seconds": round(time.time() - dataset_start, 2),
            }
            results["datasets"][dataset] = error_result
            print(f"\n[ERROR] {dataset}: {e}")

    # Summary
    total_duration = round(time.time() - total_start, 2)
    results["end_time"] = datetime.now().isoformat()
    results["total_duration_seconds"] = total_duration

    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"Total Duration: {total_duration}s")
    print("\nResults by dataset:")
    for dataset, result in results["datasets"].items():
        status = result.get("status", "unknown")
        duration = result.get("duration_seconds", 0)
        print(f"  {dataset}: {status} ({duration}s)")

    # Check for any errors
    errors = [d for d, r in results["datasets"].items() if r.get("status") == "error"]
    if errors:
        print(f"\nWARNING: {len(errors)} dataset(s) had errors: {errors}")
        results["overall_status"] = "partial_success"
    else:
        results["overall_status"] = "success"

    return results


def main():
    parser = argparse.ArgumentParser(
        description="CBB V2 Master Ingestion Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--mode",
        choices=["full", "incremental"],
        default="full",
        help="Load mode: 'full' for historical, 'incremental' for recent only",
    )

    parser.add_argument(
        "--start_year",
        type=int,
        default=2022,
        help="First season to load (default: 2022)",
    )

    parser.add_argument(
        "--end_year",
        type=int,
        default=datetime.now().year,
        help="Last season to load (default: current year)",
    )

    parser.add_argument(
        "--datasets",
        type=str,
        default=None,
        help="Comma-separated list of datasets to load (default: all)",
    )

    parser.add_argument(
        "--no-files",
        action="store_true",
        help="Skip writing JSON/CSV files",
    )

    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Skip writing to database",
    )

    args = parser.parse_args()

    # Parse datasets
    datasets = None
    if args.datasets:
        datasets = [d.strip() for d in args.datasets.split(",")]

    # Run ingestion
    try:
        results = run_ingest(
            mode=args.mode,
            start_year=args.start_year,
            end_year=args.end_year,
            datasets=datasets,
            write_files=not args.no_files,
            write_db=not args.no_db,
        )

        # Exit with error code if there were failures
        if results.get("overall_status") != "success":
            sys.exit(1)

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
