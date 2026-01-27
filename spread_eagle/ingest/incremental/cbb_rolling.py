"""
CBB (College Basketball) 7-day rolling window ingestion.

The CBB API (collegebasketballdata.com) supports date-range filtering via
startDateRange and endDateRange parameters, which maps directly to our
7-day rolling window requirement.

Each function:
1. Calculates explicit date window (today - 7 days to today)
2. Fetches all records in that window
3. Deduplicates by appropriate key
4. Saves to local files (JSON, CSV, Parquet)
5. Uploads to S3 with manifest metadata
6. Returns success/failure with verification data

S3 Landing Pattern:
    s3://spread-eagle/cbb/incremental/YYYY-MM-DD/<endpoint>/
    - Each day's pull lands in a date-partitioned folder
    - Includes _manifest.json with pull metadata
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from spread_eagle.ingest.incremental._common import (
    CBB_API_BASE,
    create_manifest,
    dedupe_records,
    fetch_with_retry,
    format_date_iso,
    format_date_ymd,
    get_cbb_headers,
    get_date_window,
    save_to_local,
    upload_to_s3,
)


def _get_cbb_season(dt: datetime) -> int:
    """
    Get CBB season for a given date.

    CBB season runs Nov-Apr, labeled by the ending year.
    e.g., Nov 2024 - Apr 2025 is the "2025" season.
    """
    if dt.month >= 8:
        return dt.year + 1
    return dt.year


def _fetch_cbb_by_date_range(
    endpoint: str,
    start_date: datetime,
    end_date: datetime,
    extra_params: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Fetch CBB data for a date range.

    Returns:
        Tuple of (records, errors)
    """
    headers = get_cbb_headers()
    all_records = []
    errors = []

    # Determine which seasons overlap with our date range
    start_season = _get_cbb_season(start_date)
    end_season = _get_cbb_season(end_date)

    for season in range(start_season, end_season + 1):
        params = {
            "season": season,
            "startDateRange": format_date_iso(start_date),
            "endDateRange": format_date_iso(end_date),
        }
        if extra_params:
            params.update(extra_params)

        url = f"{CBB_API_BASE}{endpoint}"
        records, success = fetch_with_retry(url, headers, params)

        if success:
            all_records.extend(records)
            print(f"    Season {season}: {len(records):,} records")
        else:
            errors.append(f"Failed to fetch season {season}")
            print(f"    Season {season}: FAILED")

    return all_records, errors


def pull_cbb_games(days: int = 7) -> Dict[str, Any]:
    """
    Pull CBB games for the last N days.

    Key field: id (game ID)
    """
    print("\n" + "=" * 60)
    print(f"  CBB GAMES - {days}-DAY ROLLING WINDOW")
    print("=" * 60)

    start_date, end_date = get_date_window(days)
    print(f"  Window: {format_date_ymd(start_date)} to {format_date_ymd(end_date)}")

    # Fetch data
    records, errors = _fetch_cbb_by_date_range("/games", start_date, end_date)

    # Dedupe by game ID
    records = dedupe_records(records, ["id"])
    print(f"  Total: {len(records):,} games (after dedupe)")

    # Save locally
    date_str = format_date_ymd(end_date)
    output_dir = Path(f"data/cbb/incremental/{date_str}/games")
    save_to_local(records, output_dir, "games")

    # Create manifest
    manifest = create_manifest(
        sport="cbb",
        endpoint="games",
        start_date=start_date,
        end_date=end_date,
        record_count=len(records),
        success=len(errors) == 0,
        errors=errors,
    )

    # Upload to S3
    s3_prefix = f"cbb/incremental/{date_str}/games"
    s3_success = upload_to_s3(output_dir, s3_prefix, manifest)

    return {
        "endpoint": "games",
        "record_count": len(records),
        "success": len(errors) == 0 and s3_success,
        "errors": errors,
        "s3_path": f"s3://spread-eagle/{s3_prefix}",
    }


def pull_cbb_lines(days: int = 7) -> Dict[str, Any]:
    """
    Pull CBB betting lines for the last N days.

    Key field: gameId (lines are nested per game)
    Flattens the nested 'lines' array for CSV/Parquet output.
    """
    print("\n" + "=" * 60)
    print(f"  CBB BETTING LINES - {days}-DAY ROLLING WINDOW")
    print("=" * 60)

    start_date, end_date = get_date_window(days)
    print(f"  Window: {format_date_ymd(start_date)} to {format_date_ymd(end_date)}")

    # Fetch data
    records, errors = _fetch_cbb_by_date_range("/lines", start_date, end_date)

    # Dedupe by gameId (lines endpoint returns one record per game)
    records = dedupe_records(records, ["gameId"])
    print(f"  Total: {len(records):,} games with lines (after dedupe)")

    # Save locally (flatten the 'lines' array)
    date_str = format_date_ymd(end_date)
    output_dir = Path(f"data/cbb/incremental/{date_str}/lines")
    save_to_local(records, output_dir, "lines", flatten_field="lines")

    # Create manifest
    manifest = create_manifest(
        sport="cbb",
        endpoint="lines",
        start_date=start_date,
        end_date=end_date,
        record_count=len(records),
        success=len(errors) == 0,
        errors=errors,
    )

    # Upload to S3
    s3_prefix = f"cbb/incremental/{date_str}/lines"
    s3_success = upload_to_s3(output_dir, s3_prefix, manifest)

    return {
        "endpoint": "lines",
        "record_count": len(records),
        "success": len(errors) == 0 and s3_success,
        "errors": errors,
        "s3_path": f"s3://spread-eagle/{s3_prefix}",
    }


def pull_cbb_team_stats(days: int = 7) -> Dict[str, Any]:
    """
    Pull CBB team game stats for the last N days.

    Endpoint: /games/teams
    Key fields: gameId + teamId (composite)
    """
    print("\n" + "=" * 60)
    print(f"  CBB TEAM STATS - {days}-DAY ROLLING WINDOW")
    print("=" * 60)

    start_date, end_date = get_date_window(days)
    print(f"  Window: {format_date_ymd(start_date)} to {format_date_ymd(end_date)}")

    # Fetch data
    records, errors = _fetch_cbb_by_date_range("/games/teams", start_date, end_date)

    # Dedupe by composite key (gameId + teamId)
    records = dedupe_records(records, ["gameId", "teamId"])
    print(f"  Total: {len(records):,} team-game records (after dedupe)")

    # Save locally
    date_str = format_date_ymd(end_date)
    output_dir = Path(f"data/cbb/incremental/{date_str}/team_stats")
    save_to_local(records, output_dir, "team_stats")

    # Create manifest
    manifest = create_manifest(
        sport="cbb",
        endpoint="team_stats",
        start_date=start_date,
        end_date=end_date,
        record_count=len(records),
        success=len(errors) == 0,
        errors=errors,
    )

    # Upload to S3
    s3_prefix = f"cbb/incremental/{date_str}/team_stats"
    s3_success = upload_to_s3(output_dir, s3_prefix, manifest)

    return {
        "endpoint": "team_stats",
        "record_count": len(records),
        "success": len(errors) == 0 and s3_success,
        "errors": errors,
        "s3_path": f"s3://spread-eagle/{s3_prefix}",
    }


def pull_cbb_game_players(days: int = 7) -> Dict[str, Any]:
    """
    Pull CBB player game stats for the last N days.

    Endpoint: /games/players
    Key fields: gameId + athleteId (composite)

    Note: The API returns nested structure (teams -> players).
    We flatten to one row per player-game.
    """
    print("\n" + "=" * 60)
    print(f"  CBB PLAYER STATS - {days}-DAY ROLLING WINDOW")
    print("=" * 60)

    start_date, end_date = get_date_window(days)
    print(f"  Window: {format_date_ymd(start_date)} to {format_date_ymd(end_date)}")

    # Fetch data
    raw_records, errors = _fetch_cbb_by_date_range("/games/players", start_date, end_date)

    # Flatten: each record is one team-game with a 'players' array
    flat_records = []
    for game_record in raw_records:
        base = {k: v for k, v in game_record.items() if k != "players"}
        players = game_record.get("players", [])
        for player in players:
            flat_records.append({**base, **player})

    # Dedupe by composite key (gameId + athleteId)
    records = dedupe_records(flat_records, ["gameId", "athleteId"])
    print(f"  Total: {len(records):,} player-game records (after dedupe)")

    # Save locally
    date_str = format_date_ymd(end_date)
    output_dir = Path(f"data/cbb/incremental/{date_str}/game_players")
    save_to_local(records, output_dir, "game_players")

    # Create manifest
    manifest = create_manifest(
        sport="cbb",
        endpoint="game_players",
        start_date=start_date,
        end_date=end_date,
        record_count=len(records),
        success=len(errors) == 0,
        errors=errors,
    )

    # Upload to S3
    s3_prefix = f"cbb/incremental/{date_str}/game_players"
    s3_success = upload_to_s3(output_dir, s3_prefix, manifest)

    return {
        "endpoint": "game_players",
        "record_count": len(records),
        "success": len(errors) == 0 and s3_success,
        "errors": errors,
        "s3_path": f"s3://spread-eagle/{s3_prefix}",
    }


def pull_cbb_team_season_stats() -> Dict[str, Any]:
    """
    Pull CBB team season stats for the current season only.

    Endpoint: /stats/team/season
    Key fields: teamId + season (composite)
    """
    print("\n" + "=" * 60)
    print("  CBB TEAM SEASON STATS - CURRENT SEASON")
    print("=" * 60)

    season = _get_cbb_season(datetime.now())
    print(f"  Season: {season}")

    headers = get_cbb_headers()
    url = f"{CBB_API_BASE}/stats/team/season"
    params = {"season": season}
    errors = []

    records, success = fetch_with_retry(url, headers, params)
    if not success:
        errors.append(f"Failed to fetch team season stats for {season}")

    records = dedupe_records(records, ["teamId", "season"])
    print(f"  Total: {len(records):,} team-season records")

    # Save locally
    date_str = format_date_ymd(datetime.now())
    output_dir = Path(f"data/cbb/incremental/{date_str}/team_season_stats")
    save_to_local(records, output_dir, "team_season_stats")

    # Create manifest
    start_date, end_date = get_date_window(1)
    manifest = create_manifest(
        sport="cbb",
        endpoint="team_season_stats",
        start_date=start_date,
        end_date=end_date,
        record_count=len(records),
        success=len(errors) == 0,
        errors=errors,
    )

    # Upload to S3
    s3_prefix = f"cbb/incremental/{date_str}/team_season_stats"
    s3_success = upload_to_s3(output_dir, s3_prefix, manifest)

    return {
        "endpoint": "team_season_stats",
        "record_count": len(records),
        "success": len(errors) == 0 and s3_success,
        "errors": errors,
        "s3_path": f"s3://spread-eagle/{s3_prefix}",
    }


def pull_cbb_player_season_stats() -> Dict[str, Any]:
    """
    Pull CBB player season stats for the current season only.

    Endpoint: /stats/player/season
    Key fields: athleteId + teamId + season (composite)
    """
    print("\n" + "=" * 60)
    print("  CBB PLAYER SEASON STATS - CURRENT SEASON")
    print("=" * 60)

    season = _get_cbb_season(datetime.now())
    print(f"  Season: {season}")

    headers = get_cbb_headers()
    url = f"{CBB_API_BASE}/stats/player/season"
    params = {"season": season}
    errors = []

    records, success = fetch_with_retry(url, headers, params)
    if not success:
        errors.append(f"Failed to fetch player season stats for {season}")

    records = dedupe_records(records, ["athleteId", "teamId", "season"])
    print(f"  Total: {len(records):,} player-season records")

    # Save locally
    date_str = format_date_ymd(datetime.now())
    output_dir = Path(f"data/cbb/incremental/{date_str}/player_season_stats")
    save_to_local(records, output_dir, "player_season_stats")

    # Create manifest
    start_date, end_date = get_date_window(1)
    manifest = create_manifest(
        sport="cbb",
        endpoint="player_season_stats",
        start_date=start_date,
        end_date=end_date,
        record_count=len(records),
        success=len(errors) == 0,
        errors=errors,
    )

    # Upload to S3
    s3_prefix = f"cbb/incremental/{date_str}/player_season_stats"
    s3_success = upload_to_s3(output_dir, s3_prefix, manifest)

    return {
        "endpoint": "player_season_stats",
        "record_count": len(records),
        "success": len(errors) == 0 and s3_success,
        "errors": errors,
        "s3_path": f"s3://spread-eagle/{s3_prefix}",
    }


if __name__ == "__main__":
    # Quick test
    print("\nTesting CBB rolling window ingestion...")
    results = [
        pull_cbb_games(),
        pull_cbb_lines(),
        pull_cbb_team_stats(),
        pull_cbb_game_players(),
        pull_cbb_team_season_stats(),
        pull_cbb_player_season_stats(),
    ]
    print("\n" + "=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)
    for r in results:
        status = "OK" if r["success"] else "FAILED"
        print(f"  {r['endpoint']}: {r['record_count']:,} records [{status}]")
