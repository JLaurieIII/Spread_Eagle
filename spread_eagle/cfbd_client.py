from __future__ import annotations

from typing import Any, Iterable

import cfbd

from spread_eagle.config import settings


def _client() -> cfbd.ApiClient:
    settings.require()
    cfg = cfbd.Configuration(access_token=settings.cfb_api_key)
    return cfbd.ApiClient(cfg)


def get_postseason_games(year: int, classification: str = "fbs") -> list[Any]:
    """
    Returns postseason games (includes bowls + conference championships + CFP).
    We’ll filter to bowls later if desired.
    """
    with _client() as api_client:
        games_api = cfbd.GamesApi(api_client)
        # API supports season_type='postseason' per docs/examples. :contentReference[oaicite:1]{index=1}
        return games_api.get_games(year=year, season_type="postseason", classification=classification)


def get_lines(year: int) -> list[Any]:
    """
    Returns betting lines for a season, supports season_type='postseason'. :contentReference[oaicite:2]{index=2}
    """
    with _client() as api_client:
        betting_api = cfbd.BettingApi(api_client)
        return betting_api.get_lines(year=year, season_type="postseason")
