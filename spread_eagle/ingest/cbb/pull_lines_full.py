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


def fetch_lines(season: int, season_type: str | None = None) -> List[Dict[str, Any]]:
    """
    Fetch all betting lines for a season/type with pagination.
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

        resp = requests.get(
            f"{BASE_URL}/lines", headers=headers, params=params, timeout=60
        )

        if resp.status_code != 200:
            print(f"      ERROR: {resp.status_code} - {resp.text[:200]}")
            break

        page = resp.json()
        page_count = len(page) if isinstance(page, list) else 0

        if page_count == 0:
            break

        # Dedupe by gameId
        new_ids = {r.get("gameId") for r in page if r.get("gameId") is not None}
        if new_ids and new_ids.issubset(seen_ids):
            break

        out.extend(page)
        seen_ids.update(new_ids)

        if page_count < PAGE_SIZE:
            break

        offset += PAGE_SIZE
        time.sleep(0.15)

    return out


def dedupe_by_id(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for r in records:
        gid = r.get("gameId")
        if gid is None or gid not in seen:
            out.append(r)
            if gid is not None:
                seen.add(gid)
    return out


def pull_season(season: int) -> List[Dict[str, Any]]:
    """
    Pull full regular + postseason betting lines.
    """
    all_lines: List[Dict[str, Any]] = []

    print(f"    regular...")
    regular = fetch_lines(season, "regular")
    all_lines.extend(regular)
    print(f"      -> {len(regular):,} games")

    print(f"    postseason...")
    post = fetch_lines(season, "postseason")
    all_lines.extend(post)
    print(f"      -> {len(post):,} games")

    return dedupe_by_id(all_lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_year", type=int, default=2022)
    parser.add_argument("--end_year", type=int, default=datetime.now().year)
    args = parser.parse_args()

    paths = get_data_paths("cbb")
    paths.ensure_dirs()

    all_years: List[Dict[str, Any]] = []

    for year in range(args.start_year, args.end_year + 1):
        print(f"\n[{year}] Pulling betting lines...")
        lines = pull_season(year)

        # Save individual year
        year_path = paths.raw / f"lines_{year}_all_full.json"
        with year_path.open("w", encoding="utf-8") as f:
            json.dump(lines, f, indent=2)

        print(f"  [OK] {year}: {len(lines):,} games")
        all_years.extend(lines)

    all_years = dedupe_by_id(all_years)

    # Save combined JSON
    all_path = paths.raw / f"lines_{args.start_year}_{args.end_year}_all_full.json"
    with all_path.open("w", encoding="utf-8") as f:
        json.dump(all_years, f, indent=2)

    # Save flat CSV (flatten the nested lines array)
    if all_years:
        # Expand lines array - one row per game per provider
        flat_records = []
        for game in all_years:
            base = {k: v for k, v in game.items() if k != "lines"}
            if game.get("lines"):
                for line in game["lines"]:
                    flat_records.append({**base, **line})
            else:
                # Keep games with no lines for completeness
                flat_records.append(base)
        
        df = pd.DataFrame(flat_records)
        csv_path = paths.raw / f"lines_{args.start_year}_{args.end_year}_all_full_flat.csv"
        df.to_csv(csv_path, index=False)
        print(f"\nSaved FLAT CSV -> {csv_path}")

    print(f"Saved ALL YEARS JSON -> {all_path}")
    print(f"Total: {len(all_years):,} games")


if __name__ == "__main__":
    main()
