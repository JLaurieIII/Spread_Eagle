"""
Run 7-day CDC pulls for key CBB endpoints and write csv/json/parquet outputs.

Endpoints included:
- games
- lines
- game_players
- team_stats
- team_season_stats
- player_season_stats

Usage:
    python -m spread_eagle.ingest.cbb.run_cbb_cdc_week
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from spread_eagle.ingest.cbb.pull_game_players_cdc import pull_game_players_cdc
from spread_eagle.ingest.cbb.pull_games_cdc import pull_games_cdc
from spread_eagle.ingest.cbb.pull_lines_cdc import pull_lines_cdc
from spread_eagle.ingest.cbb.pull_player_season_stats_cdc import pull_player_season_stats_cdc
from spread_eagle.ingest.cbb.pull_team_season_stats_cdc import pull_team_season_stats_cdc
from spread_eagle.ingest.cbb.pull_team_stats_cdc import pull_team_stats_cdc


def main() -> None:
    end_dt = datetime.utcnow()
    start_dt = (end_dt - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)

    print("=" * 70)
    print(f"CBB CDC WINDOW: {start_dt.date()} -> {end_dt.date()} (UTC)")
    print("=" * 70)

    counts: Dict[str, int] = {}

    counts["games"] = len(pull_games_cdc(start_dt, end_dt))
    counts["lines"] = len(pull_lines_cdc(start_dt, end_dt))
    counts["game_players"] = len(pull_game_players_cdc(start_dt, end_dt))
    counts["team_stats"] = len(pull_team_stats_cdc(start_dt, end_dt))
    counts["team_season_stats"] = len(pull_team_season_stats_cdc(start_dt, end_dt))
    counts["player_season_stats"] = len(pull_player_season_stats_cdc(start_dt, end_dt))

    print("\nSummary (records fetched):")
    for endpoint, count in counts.items():
        print(f"  {endpoint}: {count:,}")

    print("\nOutputs written to data/cbb/cdc_7day/<endpoint>/")


if __name__ == "__main__":
    main()
