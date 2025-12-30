"""
Pull CBB betting lines - FULL historical load (2022-current).

Usage:
    python -m spread_eagle.ingest.cbb.pull_lines_full
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from spread_eagle.ingest.cbb._common import (
    START_YEAR,
    fetch_by_date_ranges,
    get_current_cbb_season,
    upload_folder_to_s3,
)


def main() -> None:
    end_year = get_current_cbb_season()
    output_dir = Path("data/cbb/raw/lines")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"  BETTING LINES FULL LOAD ({START_YEAR}-{end_year})")
    print("=" * 60)

    all_records: List[Dict[str, Any]] = []

    for year in range(START_YEAR, end_year + 1):
        print(f"\n  [{year}]")

        # Use date-range pagination - /lines uses gameId as the key
        season_records = fetch_by_date_ranges("/lines", year, id_field="gameId")
        print(f"    TOTAL: {len(season_records):,} games with lines")

        # Save season JSON
        json_path = output_dir / f"lines_{year}.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(season_records, f, indent=2)
        print(f"    Saved: {json_path.name}")

        all_records.extend(season_records)

    # Final dedupe across seasons
    seen = set()
    deduped = []
    for r in all_records:
        rid = r.get("gameId")
        if rid not in seen:
            seen.add(rid)
            deduped.append(r)
    all_records = deduped

    print(f"\n  GRAND TOTAL: {len(all_records):,} games with lines")

    # Flatten the lines array for CSV/Parquet
    if all_records:
        flat_records = []
        for record in all_records:
            base = {k: v for k, v in record.items() if k != "lines"}
            nested = record.get("lines", [])
            if nested:
                for line in nested:
                    flat_records.append({**base, **line})
            else:
                flat_records.append(base)

        df = pd.DataFrame(flat_records)
        csv_path = output_dir / f"lines_{START_YEAR}_{end_year}.csv"
        df.to_csv(csv_path, index=False)
        print(f"  Saved: {csv_path.name} ({len(df):,} rows)")

        parquet_path = output_dir / f"lines_{START_YEAR}_{end_year}.parquet"
        df.to_parquet(parquet_path, index=False)
        print(f"  Saved: {parquet_path.name}")

    # Upload to S3
    print(f"\n  Uploading to S3...")
    upload_folder_to_s3(output_dir, "cbb/raw/lines")

    print("\n  DONE!")


if __name__ == "__main__":
    main()
