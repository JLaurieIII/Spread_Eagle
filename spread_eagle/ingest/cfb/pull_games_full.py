from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests
import pandas as pd

from spread_eagle.config import RAW_DIR, settings

BASE_URL = "https://api.collegefootballdata.com"


def fetch_games(
    year: int,
    season_type: str,
    week: int | None = None,
) -> List[Dict[str, Any]]:
    """
    Raw /games pull. Returns EXACT API payload (all fields).
    """
    if not settings.cfb_api_key:
        raise RuntimeError("Missing CFB_API_KEY in .env")

    headers = {
        "Authorization": f"Bearer {settings.cfb_api_key}",
        "Accept": "application/json",
    }

    params = {
        "year": year,
        "seasonType": season_type,  # "regular" or "postseason"
    }

    if week is not None:
        params["week"] = week

    resp = requests.get(
        f"{BASE_URL}/games",
        headers=headers,
        params=params,
        timeout=30,
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"CFBD /games failed | year={year} seasonType={season_type} "
            f"week={week} status={resp.status_code} body={resp.text}"
        )

    return resp.json()


def dedupe_by_id(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for r in records:
        gid = r.get("id")
        if gid is None or gid not in seen:
            out.append(r)
            if gid is not None:
                seen.add(gid)
    return out


def pull_year(year: int) -> List[Dict[str, Any]]:
    """
    Pull full regular + postseason for a year.
    """
    all_games: List[Dict[str, Any]] = []

    # Regular season: weeks 1–17
    for week in range(1, 18):
        games = fetch_games(year, season_type="regular", week=week)
        if games:
            all_games.extend(games)
        time.sleep(0.15)

    # Postseason (no weeks)
    postseason_games = fetch_games(year, season_type="postseason")
    all_games.extend(postseason_games)

    return dedupe_by_id(all_games)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_year", type=int, default=2022)
    parser.add_argument("--end_year", type=int, default=datetime.now().year)
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    all_years: List[Dict[str, Any]] = []

    for year in range(args.start_year, args.end_year + 1):
        games = pull_year(year)

        year_path = RAW_DIR / f"games_{year}_all_full.json"
        with year_path.open("w", encoding="utf-8") as f:
            json.dump(games, f, indent=2)

        print(f"[OK] {year}: {len(games):,} games")
        all_years.extend(games)

    all_years = dedupe_by_id(all_years)

    all_path = RAW_DIR / f"games_{args.start_year}_{args.end_year}_all_full.json"
    with all_path.open("w", encoding="utf-8") as f:
        json.dump(all_years, f, indent=2)

    # Optional flat CSV for inspection
    df = pd.json_normalize(all_years, sep="__")
    csv_path = RAW_DIR / f"games_{args.start_year}_{args.end_year}_all_full_flat.csv"
    df.to_csv(csv_path, index=False)

    print(f"\nSaved ALL YEARS JSON -> {all_path}")
    print(f"Saved FLAT CSV -> {csv_path}")


if __name__ == "__main__":
    main()
