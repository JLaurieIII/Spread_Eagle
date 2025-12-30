"""
Pull CBB teams (reference data).

Usage:
    python -m spread_eagle.ingest.cbb.pull_teams
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from spread_eagle.ingest.cbb._common import (
    fetch_simple,
    upload_folder_to_s3,
)


def main() -> None:
    output_dir = Path("data/cbb/raw/teams")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  TEAMS FULL LOAD")
    print("=" * 60)

    records = fetch_simple("/teams")
    print(f"  Fetched: {len(records):,} teams")

    if records:
        # Save JSON
        json_path = output_dir / "teams.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        print(f"  Saved: {json_path.name}")

        # Save CSV and Parquet
        df = pd.json_normalize(records, sep="_")
        csv_path = output_dir / "teams.csv"
        df.to_csv(csv_path, index=False)
        print(f"  Saved: {csv_path.name} ({len(df):,} rows)")

        parquet_path = output_dir / "teams.parquet"
        df.to_parquet(parquet_path, index=False)
        print(f"  Saved: {parquet_path.name}")

        # Upload to S3
        print(f"\n  Uploading to S3...")
        upload_folder_to_s3(output_dir, "cbb/raw/teams")

    print("\n  DONE!")


if __name__ == "__main__":
    main()
