"""
Run all CBB full load scripts.

Usage:
    python -m spread_eagle.ingest.cbb.run_full_load
"""
from __future__ import annotations

from spread_eagle.ingest.cbb import (
    pull_conferences,
    pull_venues,
    pull_teams,
    pull_games_full,
    pull_lines_full,
    pull_team_stats_full,
    pull_game_players_full,
    pull_team_season_stats_full,
    pull_player_season_stats_full,
)


def main() -> None:
    print("\n" + "=" * 70)
    print("  CBB FULL DATA LOAD - ALL ENDPOINTS")
    print("=" * 70 + "\n")

    # Reference tables (no pagination needed)
    print("\n[1/9] CONFERENCES")
    pull_conferences.main()

    print("\n[2/9] VENUES")
    pull_venues.main()

    print("\n[3/9] TEAMS")
    pull_teams.main()

    # Transactional tables (date-range pagination)
    print("\n[4/9] GAMES")
    pull_games_full.main()

    print("\n[5/9] BETTING LINES")
    pull_lines_full.main()

    print("\n[6/9] TEAM STATS")
    pull_team_stats_full.main()

    print("\n[7/9] GAME PLAYERS")
    pull_game_players_full.main()

    # Season aggregates (simple season filter)
    print("\n[8/9] TEAM SEASON STATS")
    pull_team_season_stats_full.main()

    print("\n[9/9] PLAYER SEASON STATS")
    pull_player_season_stats_full.main()

    print("\n" + "=" * 70)
    print("  ALL DONE!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
