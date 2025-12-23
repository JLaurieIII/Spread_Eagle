from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from typing import Any, Dict, List

import requests
import pandas as pd

from spread_eagle.config import get_data_paths, settings

BASE_URL = "https://api.collegebasketballdata.com"
PAGE_SIZE = 3000
MAX_PAGES = 200


def fetch_team_stats(season: int, season_type: str | None = None) -> List[Dict[str, Any]]:
    """
    Fetch all team game stats for a season/type with pagination.
    """
    if not settings.cbb_api_key:
        raise RuntimeError("Missing CBB_API_KEY in .env")

    headers = {
        "Authorization": f"Bearer {settings.cbb_api_key}",
        "Accept": "application/json",
    }

    offset = 0
    out: List[Dict[str, Any]] = []
    seen_ids: set = set()
    page_num = 0

    while True:
        page_num += 1
        if page_num > MAX_PAGES:
            print(f"      Hit MAX_PAGES={MAX_PAGES}; stopping")
            break

        params: Dict[str, Any] = {"season": season, "offset": offset, "limit": PAGE_SIZE}
        if season_type:
            params["seasonType"] = season_type

        url = f"{BASE_URL}/games/teams"
        start_time = time.time()
        print(
            f"      -> GET {url} season={season} type={season_type or 'all'} "
            f"offset={offset} limit={PAGE_SIZE}"
        )
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=60)
        except Exception as exc:
            elapsed = time.time() - start_time
            print(f"      !! request failed after {elapsed:.2f}s: {exc}")
            break
        elapsed = time.time() - start_time
        print(
            f"         status={resp.status_code} elapsed={elapsed:.2f}s "
            f"len(body)={len(resp.content)}"
        )

        if resp.status_code != 200:
            print(f"      ERROR: {resp.status_code} - {resp.text[:400]}")
            break

        page = resp.json()
        page_count = len(page) if isinstance(page, list) else 0

        if page_count == 0:
            break

        # Dedupe by game_id + team_id combo
        new_ids = {(r.get("game_id"), r.get("team_id")) for r in page 
                   if r.get("game_id") and r.get("team_id")}
        if new_ids and new_ids.issubset(seen_ids):
            break

        out.extend(page)
        seen_ids.update(new_ids)

        if page_count < PAGE_SIZE:
            break

        offset += PAGE_SIZE
        time.sleep(0.15)

    return out


def dedupe_by_game_team(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for r in records:
        key = (r.get("game_id"), r.get("team_id"))
        if key not in seen:
            out.append(r)
            seen.add(key)
    return out


def pull_season(season: int) -> List[Dict[str, Any]]:
    """
    Pull full regular + postseason team stats.
    """
    all_stats: List[Dict[str, Any]] = []

    print(f"    regular...")
    regular = fetch_team_stats(season, "regular")
    all_stats.extend(regular)
    print(f"      -> {len(regular):,} records")

    print(f"    postseason...")
    post = fetch_team_stats(season, "postseason")
    all_stats.extend(post)
    print(f"      -> {len(post):,} records")

    return dedupe_by_game_team(all_stats)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_year", type=int, default=2022)
    parser.add_argument("--end_year", type=int, default=datetime.now().year)
    args = parser.parse_args()

    paths = get_data_paths("cbb")
    paths.ensure_dirs()

    all_years: List[Dict[str, Any]] = []

    for year in range(args.start_year, args.end_year + 1):
        print(f"\n[{year}] Pulling team stats...")
        stats = pull_season(year)

        # Save individual year
        year_path = paths.raw / f"team_stats_{year}_all_full.json"
        with year_path.open("w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)

        print(f"  [OK] {year}: {len(stats):,} records")
        all_years.extend(stats)

    all_years = dedupe_by_game_team(all_years)

    # Save combined JSON
    all_path = paths.raw / f"team_stats_{args.start_year}_{args.end_year}_all_full.json"
    with all_path.open("w", encoding="utf-8") as f:
        json.dump(all_years, f, indent=2)

    # Save flat CSV
    if all_years:
        df = pd.json_normalize(all_years, sep="__")
        csv_path = paths.raw / f"team_stats_{args.start_year}_{args.end_year}_all_full_flat.csv"
        df.to_csv(csv_path, index=False)
        print(f"\nSaved FLAT CSV -> {csv_path}")

    print(f"Saved ALL YEARS JSON -> {all_path}")
    print(f"Total: {len(all_years):,} records")


if __name__ == "__main__":
    main()