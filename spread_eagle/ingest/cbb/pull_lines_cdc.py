"""
CDC pull for CBB betting lines over a date window (default: last 7 days).

Usage:
    python -m spread_eagle.ingest.cbb.pull_lines_cdc
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from spread_eagle.ingest.cbb._common import fetch_date_window, write_cdc_outputs


def pull_lines_cdc(start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
    """Pull lines between start_dt and end_dt (inclusive window)."""
    print(f"  LINES CDC {start_dt.date()} -> {end_dt.date()}")
    records = fetch_date_window("/lines", start_dt, end_dt, id_field="gameId")
    print(f"    {len(records):,} games with lines fetched")
    write_cdc_outputs(
        "lines",
        start_dt,
        end_dt,
        records,
        flatten_field="lines",
        s3_prefix="cbb/cdc_7day/lines",
    )
    return records


def main() -> None:
    end_dt = datetime.utcnow()
    start_dt = (end_dt - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    pull_lines_cdc(start_dt, end_dt)


if __name__ == "__main__":
    main()
