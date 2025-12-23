from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import requests

from spread_eagle.config import RAW_DIR, settings

BASE_URL = "https://api.collegefootballdata.com"


def fetch_lines(
    year: int,
    season_type: str,
    week: int | None = None,
) -> List[Dict[str, Any]]:
    """
    Raw /lines pull. Returns EXACT API payload (all fields).

    CFBD /lines supports:
      - year
      - seasonType (regular/postseason)
      - week (regular season)
    We intentionally do NOT filter further.
    """
    if not settings.cfb_api_key:
        raise RuntimeError("Missing CFB_API_KEY in .env")

    headers = {
        "Authorization": f"Bearer {settings.cfb_api_key}",
        "Accept": "application/json",
    }

    params: Dict[str, Any] = {
        "year": year,
        "seasonType": season_type,  # "regular" or "postseason"
    }
    if week is not None:
        params["week"] = week

    resp = requests.get(
        f"{BASE_URL}/lines",
        headers=headers,
        params=params,
        timeout=60,
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"CFBD /lines failed | year={year} seasonType={season_type} "
            f"week={week} status={resp.status_code} body={resp.text}"
        )

    return resp.json()


def dedupe_by_key(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Lines payload sometimes has no 'id' field consistently across versions.
    We'll dedupe using (id) if present, else fallback to (homeTeam, awayTeam, season, week, seasonType, startDate).
    """
    seen = set()
    out = []
    for r in records:
        rid = r.get("id") or r.get("gameId") or r.get("game_id")
        if rid is not None:
            key = ("id", rid)
        else:
            key = (
                r.get("season"),
                r.get("week"),
                r.get("seasonType"),
                r.get("startDate"),
                r.get("homeTeam"),
                r.get("awayTeam"),
            )
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def pull_year(year: int) -> Dict[str, List[Dict[str, Any]]]:
    """
    Pull full regular + postseason lines for a year.
    Regular is weeks 1–17; postseason is one call.
    Returns dict with keys: regular, postseason, combined
    """
    regular_all: List[Dict[str, Any]] = []
    for week in range(1, 18):
        lines = fetch_lines(year, season_type="regular", week=week)
        if lines:
            regular_all.extend(lines)
        time.sleep(0.15)

    postseason = fetch_lines(year, season_type="postseason", week=None)

    regular_all = dedupe_by_key(regular_all)
    postseason = dedupe_by_key(postseason)
    combined = dedupe_by_key(regular_all + postseason)

    return {"regular": regular_all, "postseason": postseason, "combined": combined}


def write_json(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def flatten_lines_long(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Explode CFBD /lines into one row per (game x provider).
    """
    rows: List[Dict[str, Any]] = []

    for g in records:
        game_id = g.get("id") or g.get("gameId")

        base = {
            "game_id": game_id,
            "season": g.get("season"),
            "season_type": g.get("seasonType"),
            "week": g.get("week"),
            "start_date": g.get("startDate"),

            "home_team_id": g.get("homeTeamId"),
            "home_team": g.get("homeTeam"),
            "home_conference": g.get("homeConference"),
            "home_classification": g.get("homeClassification"),
            "home_score": g.get("homeScore"),

            "away_team_id": g.get("awayTeamId"),
            "away_team": g.get("awayTeam"),
            "away_conference": g.get("awayConference"),
            "away_classification": g.get("awayClassification"),
            "away_score": g.get("awayScore"),
        }

        for line in g.get("lines", []):
            rows.append(
                {
                    **base,
                    "provider": line.get("provider"),
                    "spread": line.get("spread"),
                    "spread_open": line.get("spreadOpen"),
                    "total": line.get("overUnder"),
                    "total_open": line.get("overUnderOpen"),
                    "home_moneyline": line.get("homeMoneyline"),
                    "away_moneyline": line.get("awayMoneyline"),
                    "formatted_spread": line.get("formattedSpread"),
                }
            )

    df = pd.DataFrame(rows)

    # Numeric casting (safe, coercive)
    numeric_cols = [
        "spread",
        "spread_open",
        "total",
        "total_open",
        "home_moneyline",
        "away_moneyline",
        "home_score",
        "away_score",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_year", type=int, default=2022)
    parser.add_argument("--end_year", type=int, default=datetime.now().year)
    parser.add_argument("--csv", action="store_true", help="Also write a flattened CSV for inspection/loading.")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    all_years: List[Dict[str, Any]] = []

    for year in range(args.start_year, args.end_year + 1):
        payload = pull_year(year)
        reg = payload["regular"]
        post = payload["postseason"]
        combined = payload["combined"]

        write_json(RAW_DIR / f"lines_{year}_regular_full.json", reg)
        write_json(RAW_DIR / f"lines_{year}_postseason_full.json", post)
        write_json(RAW_DIR / f"lines_{year}_all_full.json", combined)

        print(f"[OK] {year} lines: regular={len(reg):,} postseason={len(post):,} combined={len(combined):,}")
        all_years.extend(combined)

    all_years = dedupe_by_key(all_years)
    all_path = RAW_DIR / f"lines_{args.start_year}_{args.end_year}_all_full.json"
    write_json(all_path, all_years)

    print(f"\nSaved ALL YEARS JSON -> {all_path}")

    if args.csv:
        df_long = flatten_lines_long(all_years)

        csv_path = RAW_DIR / f"lines_{args.start_year}_{args.end_year}_long.csv"
        df_long.to_csv(csv_path, index=False)

        print(f"Saved LONG CSV (game x provider) -> {csv_path}")


if __name__ == "__main__":
    main()
