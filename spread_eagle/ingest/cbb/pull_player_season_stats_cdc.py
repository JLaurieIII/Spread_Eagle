"""
CDC pull for CBB player season stats for seasons overlapping the date window.

The player season stats endpoint does not support date filters, so we fetch the
season(s) corresponding to the window dates (at most two seasons).

Usage:
    python -m spread_eagle.ingest.cbb.pull_player_season_stats_cdc
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from spread_eagle.ingest.cbb._common import (
    date_to_season,
    fetch_with_params,
    write_cdc_outputs,
)


def pull_player_season_stats_cdc(start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
    """Pull player season stats for seasons overlapping the window."""
    seasons = sorted({date_to_season(start_dt), date_to_season(end_dt)})
    print(f"  PLAYER SEASON STATS CDC seasons={seasons} (window {start_dt.date()} -> {end_dt.date()})")

    all_records: List[Dict[str, Any]] = []
    for season in seasons:
        records = fetch_with_params("/stats/player/season", {"season": season})
        print(f"    {season}: {len(records):,} player season records")
        all_records.extend(records)

    # Dedupe using (athleteId, teamId, season)
    seen: set[Tuple[Any, Any, Any]] = set()
    deduped: List[Dict[str, Any]] = []
    for r in all_records:
        key = (r.get("athleteId"), r.get("teamId"), r.get("season"))
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    write_cdc_outputs(
        "player_season_stats",
        start_dt,
        end_dt,
        deduped,
        s3_prefix="cbb/cdc_7day/player_season_stats",
    )
    return deduped


def main() -> None:
    end_dt = datetime.utcnow()
    start_dt = (end_dt - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    pull_player_season_stats_cdc(start_dt, end_dt)


if __name__ == "__main__":
    main()
