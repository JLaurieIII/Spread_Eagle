from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import requests

from spread_eagle.config import RAW_DIR, settings

BASE_URL = "https://api.collegefootballdata.com"


def fetch_drives(
    *,
    year: int,
    season_type: str,
    week: int | None = None,
) -> List[Dict[str, Any]]:
    """
    Raw /drives pull. Returns EXACT API payload (all fields).

    Endpoint: GET /drives
    Query params we use:
      - year (required)
      - seasonType (regular/postseason)
      - week (optional; we iterate weeks for regular season)

    We intentionally do NOT apply team/offense/defense filters.
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
        f"{BASE_URL}/drives",
        headers=headers,
        params=params,
        timeout=90,
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"CFBD /drives failed | year={year} seasonType={season_type} week={week} "
            f"status={resp.status_code} body={resp.text}"
        )

    data = resp.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected /drives response type: {type(data)}")

    return data


def _safe_val(v: Any) -> Any:
    """
    Convert dict/list values into stable, hashable primitives for dedupe keys.

    CFBD sometimes returns nested objects (e.g., offense/defense as dicts).
    Sets require hashable elements; dict/list are unhashable.
    """
    if isinstance(v, dict):
        # Prefer id, fallback to name, else stable JSON string
        return v.get("id") or v.get("name") or json.dumps(v, sort_keys=True, ensure_ascii=False)
    if isinstance(v, list):
        return json.dumps(v, sort_keys=True, ensure_ascii=False)
    return v


def _drive_identity(record: Dict[str, Any]) -> Tuple[Any, ...]:
    """
    Best-effort stable unique key across CFBD versions.

    Prefer:
      - driveId (or drive_id)
    Else:
      - composite of primitive-safe fields
    """
    drive_id = record.get("driveId") or record.get("drive_id")
    if drive_id is not None:
        return ("driveId", drive_id)

    return (
        "composite",
        _safe_val(record.get("gameId") or record.get("game_id")),
        _safe_val(record.get("driveNumber") or record.get("drive_number")),
        _safe_val(record.get("offense")),
        _safe_val(record.get("defense")),
        _safe_val(record.get("startPeriod") or record.get("start_period")),
        _safe_val(record.get("startYardline") or record.get("start_yardline")),
        _safe_val(record.get("startTime") or record.get("start_time")),
    )


def dedupe(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out: List[Dict[str, Any]] = []
    for r in records:
        key = _drive_identity(r)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def write_json(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def flatten_for_csv(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Flatten drives safely:
      - pd.json_normalize for nested dicts
      - any remaining list/dict columns -> JSON string (so CSV stays loadable)
    """
    df = pd.json_normalize(records, sep="__")

    # Convert any object cells that are dict/list to JSON strings
    for col in df.columns:
        if df[col].dtype == "object":
            sample = df[col].dropna().head(25).tolist()
            if any(isinstance(v, (dict, list)) for v in sample):
                df[col] = df[col].apply(
                    lambda v: json.dumps(v, ensure_ascii=False)
                    if isinstance(v, (dict, list))
                    else v
                )

    return df


def pull_year(year: int) -> Dict[str, List[Dict[str, Any]]]:
    """
    Pull full regular + postseason drives for a year.
      - Regular: weeks 1–17 (iterated)
      - Postseason: one call (no week)
    """
    regular_all: List[Dict[str, Any]] = []
    for week in range(1, 18):
        drives = fetch_drives(year=year, season_type="regular", week=week)
        if drives:
            regular_all.extend(drives)
        time.sleep(0.15)  # be polite

    postseason = fetch_drives(year=year, season_type="postseason", week=None)

    regular_all = dedupe(regular_all)
    postseason = dedupe(postseason)
    combined = dedupe(regular_all + postseason)

    return {"regular": regular_all, "postseason": postseason, "combined": combined}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_year", type=int, default=2022)
    parser.add_argument("--end_year", type=int, default=datetime.now().year)
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Also write flattened CSVs for inspection/loading.",
    )
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    all_years: List[Dict[str, Any]] = []

    for year in range(args.start_year, args.end_year + 1):
        payload = pull_year(year)
        reg = payload["regular"]
        post = payload["postseason"]
        combined = payload["combined"]

        write_json(RAW_DIR / f"drives_{year}_regular_full.json", reg)
        write_json(RAW_DIR / f"drives_{year}_postseason_full.json", post)
        write_json(RAW_DIR / f"drives_{year}_all_full.json", combined)

        print(
            f"[OK] {year} drives: regular={len(reg):,} postseason={len(post):,} combined={len(combined):,}"
        )

        all_years.extend(combined)

        if args.csv:
            df_year = flatten_for_csv(combined)
            csv_year = RAW_DIR / f"drives_{year}_all_full_flat.csv"
            df_year.to_csv(csv_year, index=False)
            print(f"      wrote CSV -> {csv_year}")

    # All-years combined
    all_years = dedupe(all_years)
    all_path = RAW_DIR / f"drives_{args.start_year}_{args.end_year}_all_full.json"
    write_json(all_path, all_years)
    print(f"\nSaved ALL YEARS JSON -> {all_path}")

    if args.csv:
        df_all = flatten_for_csv(all_years)
        csv_all = RAW_DIR / f"drives_{args.start_year}_{args.end_year}_all_full_flat.csv"
        df_all.to_csv(csv_all, index=False)
        print(f"Saved ALL YEARS CSV -> {csv_all}")


if __name__ == "__main__":
    main()
