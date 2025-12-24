"""Generate Postgres CREATE TABLE DDL statements from CSV headers and sample data."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, List

import pandas as pd


def quote_ident(name: str) -> str:
    """Quote an identifier to preserve original casing and special chars."""
    escaped = name.replace('"', '""')
    return f'"{escaped}"'


def sanitize_table_name(stem: str) -> str:
    """Lowercase and replace non-alphanumerics to make a Postgres-friendly table name."""
    name = re.sub(r"[^a-zA-Z0-9_]+", "_", stem).lower().strip("_")
    if not name or name[0].isdigit():
        name = f"t_{name}"
    return name


_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$")
_BOOL_VALUES = {"true", "false", "t", "f", "yes", "no", "y", "n", "0", "1"}


def _infer_type(values: Iterable[str]) -> str:
    """Infer a Postgres column type from a collection of string values."""
    non_empty = [v.strip() for v in values if isinstance(v, str) and v.strip() != ""]
    if not non_empty:
        return "TEXT"

    # Integer check
    if all(_INT_RE.match(v) for v in non_empty):
        return "BIGINT"

    # Float check
    if all(_FLOAT_RE.match(v) for v in non_empty):
        return "DOUBLE PRECISION"

    # Datetime/Date check
    parsed = pd.to_datetime(non_empty, errors="coerce", utc=True)
    success_ratio = parsed.notna().mean()
    if success_ratio >= 0.9 and parsed.notna().any():
        parsed_non_na = parsed[parsed.notna()]
        all_midnight = all(
            (ts.hour, ts.minute, ts.second, ts.microsecond) == (0, 0, 0, 0)
            for ts in parsed_non_na
        )
        return "DATE" if all_midnight else "TIMESTAMPTZ"

    # Boolean check
    if all(v.lower() in _BOOL_VALUES for v in non_empty):
        return "BOOLEAN"

    return "TEXT"


def infer_table_ddl(csv_path: Path, sample_rows: int | None = 5000, delimiter: str = ",") -> str:
    """Read CSV header/sample rows and return a CREATE TABLE statement."""
    df = pd.read_csv(
        csv_path,
        nrows=sample_rows,
        dtype=str,
        na_values=["", "NA", "N/A", "null", "None"],
        keep_default_na=True,
        low_memory=False,
        sep=delimiter,
    )

    column_types: List[tuple[str, str]] = []
    for col in df.columns:
        inferred = _infer_type(df[col].dropna().astype(str).tolist())
        column_types.append((col, inferred))

    table_name = sanitize_table_name(csv_path.stem)
    columns_sql = ",\n".join(f"    {quote_ident(name)} {col_type}" for name, col_type in column_types)
    return f"CREATE TABLE IF NOT EXISTS {quote_ident(table_name)} (\n{columns_sql}\n);"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Postgres DDL from CSV headers by sampling data for type inference."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Path(s) or glob(s) to CSV files (e.g., data/cbb/raw/*_full_flat.csv)",
    )
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=5000,
        help="Number of rows to sample for type inference (None = full file). Default: 5000",
    )
    parser.add_argument(
        "--delimiter",
        default=",",
        help="CSV delimiter. Default: ','",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths: List[Path] = []
    for pattern in args.paths:
        matched = list(Path().glob(pattern))
        if matched:
            paths.extend(matched)
        else:
            raise FileNotFoundError(f"No files matched pattern: {pattern}")

    for csv_file in paths:
        ddl = infer_table_ddl(csv_file, sample_rows=args.sample_rows, delimiter=args.delimiter)
        print(f"-- {csv_file}")
        print(ddl)
        print()


if __name__ == "__main__":
    main()

