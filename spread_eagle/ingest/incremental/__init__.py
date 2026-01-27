"""
Incremental (7-day rolling window) ingestion module.

This module provides reliable, repeatable data pulls for the most recent
7 days across all ingestion endpoints. It prioritizes:

1. Correctness - explicit date windows, no implicit state
2. Completeness - pulls all records in the window
3. Repeatability - idempotent, can be re-run safely
4. Verification - logs record counts and pull metadata

Design Philosophy:
- NO CDC state tracking
- NO implicit "last pulled" logic
- Explicit date windows that can be verified
- S3 landing with manifest metadata
"""

from spread_eagle.ingest.incremental.cbb_rolling import (
    pull_cbb_games,
    pull_cbb_lines,
    pull_cbb_team_stats,
    pull_cbb_game_players,
)

from spread_eagle.ingest.incremental.cfb_rolling import (
    pull_cfb_games,
    pull_cfb_lines,
    pull_cfb_team_stats,
    pull_cfb_game_players,
)

from spread_eagle.ingest.incremental.run_incremental import run_all

__all__ = [
    "pull_cbb_games",
    "pull_cbb_lines",
    "pull_cbb_team_stats",
    "pull_cbb_game_players",
    "pull_cfb_games",
    "pull_cfb_lines",
    "pull_cfb_team_stats",
    "pull_cfb_game_players",
    "run_all",
]
