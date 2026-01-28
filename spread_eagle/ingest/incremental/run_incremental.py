"""
Run incremental CBB ingestion (7-day rolling window).

This replaces run_full_load for daily operations.
~6 API calls instead of ~133+.

Usage:
    python -m spread_eagle.ingest.incremental.run_incremental
"""
from __future__ import annotations

from datetime import datetime

from spread_eagle.ingest.incremental.cbb_rolling import (
    pull_cbb_games,
    pull_cbb_lines,
    pull_cbb_team_stats,
    pull_cbb_game_players,
    pull_cbb_team_season_stats,
    pull_cbb_player_season_stats,
)


def main() -> None:
    start = datetime.now()

    print("\n" + "=" * 70)
    print("  CBB INCREMENTAL LOAD - 7-DAY ROLLING WINDOW")
    print("=" * 70 + "\n")

    results = []

    # Date-range endpoints (7-day window, ~4 API calls)
    print("[1/6] GAMES")
    results.append(pull_cbb_games(7))

    print("\n[2/6] BETTING LINES")
    results.append(pull_cbb_lines(7))

    print("\n[3/6] TEAM GAME STATS")
    results.append(pull_cbb_team_stats(7))

    print("\n[4/6] PLAYER GAME STATS")
    results.append(pull_cbb_game_players(7))

    # Season aggregate endpoints (current season only, 2 API calls)
    print("\n[5/6] TEAM SEASON STATS")
    results.append(pull_cbb_team_season_stats())

    print("\n[6/6] PLAYER SEASON STATS")
    results.append(pull_cbb_player_season_stats())

    # Summary
    elapsed = (datetime.now() - start).total_seconds()
    total_records = sum(r["record_count"] for r in results)
    failures = [r for r in results if not r["success"]]

    print("\n" + "=" * 70)
    print("  INCREMENTAL LOAD SUMMARY")
    print("=" * 70)
    for r in results:
        status = "OK" if r["success"] else "FAILED"
        print(f"  {r['endpoint']:.<30} {r['record_count']:>8,} records  [{status}]")

    print(f"\n  Total: {total_records:,} records in {elapsed:.1f}s")
    if failures:
        print(f"  WARNINGS: {len(failures)} endpoint(s) had errors:")
        for f in failures:
            print(f"    - {f['endpoint']}: {f['errors']}")
    else:
        print("  All endpoints succeeded.")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
