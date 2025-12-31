"""
Pull CBB team season stats - FULL historical load (2022-current).

Usage:
    python -m spread_eagle.ingest.cbb.pull_team_season_stats_full
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from spread_eagle.ingest.cbb._common import (
    START_YEAR,
    fetch_with_params,
    get_current_cbb_season,
    upload_folder_to_s3,
)


def main() -> None:
    end_year = get_current_cbb_season()
    output_dir = Path("data/cbb/raw/team_season_stats")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"  TEAM SEASON STATS FULL LOAD ({START_YEAR}-{end_year})")
    print("=" * 60)

    all_records: List[Dict[str, Any]] = []

    for year in range(START_YEAR, end_year + 1):
        print(f"\n  [{year}]")

        # Fetch season stats (no date-range needed for season aggregates)
        season_records = fetch_with_params("/stats/team/season", {"season": year})
        print(f"    TOTAL: {len(season_records):,} team season records")

        # Save season JSON
        json_path = output_dir / f"team_season_stats_{year}.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(season_records, f, indent=2)
        print(f"    Saved: {json_path.name}")

        all_records.extend(season_records)

    # Dedupe using (teamId, season)
    seen = set()
    deduped = []
    for r in all_records:
        key = (r.get("teamId"), r.get("season"))
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    all_records = deduped

    print(f"\n  GRAND TOTAL: {len(all_records):,} team season records")

    # Save consolidated CSV and Parquet
    if all_records:
        df = pd.json_normalize(all_records, sep="_")
        csv_path = output_dir / f"team_season_stats_{START_YEAR}_{end_year}.csv"
        df.to_csv(csv_path, index=False)
        print(f"  Saved: {csv_path.name} ({len(df):,} rows)")

        parquet_path = output_dir / f"team_season_stats_{START_YEAR}_{end_year}.parquet"
        df.to_parquet(parquet_path, index=False)
        print(f"  Saved: {parquet_path.name}")

    # Upload to S3
    print(f"\n  Uploading to S3...")
    upload_folder_to_s3(output_dir, "cbb/raw/team_season_stats")

    print("\n  DONE!")


if __name__ == "__main__":
    main()
