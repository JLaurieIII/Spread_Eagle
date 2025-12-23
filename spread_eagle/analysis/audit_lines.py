from __future__ import annotations

"""
Audit script for CFBD /lines data (LONG format: one row per game x provider).

PURPOSE
-------
Step through the betting data slowly and intentionally:
- understand provider coverage
- understand field completeness
- understand disagreement between books
- decide what is usable BEFORE modeling or DB loading

INSTRUCTIONS
------------
1) Run the script as-is (ONLY STEP 1 ACTIVE)
2) Uncomment ONE step at a time
3) Inspect output carefully before moving on

Run from project root:
    python -m spread_eagle.analysis.audit_lines
"""

import pandas as pd
from pathlib import Path

# -----------------------------
# CONFIG
# -----------------------------

DATA_PATH = Path("cfb_data/raw/lines_2022_2025_long.csv")

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Expected file not found: {DATA_PATH}\n"
        "Make sure pull_lines_full.py was run with --csv"
    )


# -----------------------------
# LOAD DATA
# -----------------------------

df = pd.read_csv(DATA_PATH)

# =============================
# STEP 1 — BASIC SANITY CHECK
# =============================
# (ACTIVE)
print("\n==============================")
print("STEP 1 — BASIC SANITY CHECK")
print("==============================")

print(f"Data shape (rows, cols): {df.shape}")
print("\nColumns:")
print(df.columns.tolist())

print("\nSample rows:")
print(df.head(5))

print("\nUnique games:", df["game_id"].nunique())
print("Unique providers:", df["provider"].nunique())

# Stop here intentionally
print("\n[STOP] STEP 1 complete. Uncomment the next section when ready.\n")


# =============================
# STEP 2 — PROVIDER COVERAGE
# =============================

print("\n==============================")
print("STEP 2 — PROVIDER COVERAGE")
print("==============================")

provider_counts = (
    df.groupby("provider")
      .size()
      .sort_values(ascending=False)
)

print("\nProvider counts:")
print(provider_counts)

provider_by_season = (
    df.groupby(["season", "provider"])
      .size()
      .unstack(fill_value=0)
)

print("\nProvider coverage by season:")
print(provider_by_season)



# =============================
# STEP 3 — FIELD COMPLETENESS
# =============================

print("\n==============================")
print("STEP 3 — FIELD COMPLETENESS")
print("==============================")

null_rates = df.isna().mean().sort_values(ascending=False)

print("\nNull rate by column:")
print(null_rates)

key_fields = [
    "spread",
    "spread_open",
    "total",
    "total_open",
    "home_moneyline",
    "away_moneyline",
]

field_by_provider = (
    df.groupby("provider")[key_fields]
      .apply(lambda x: x.notna().mean())
)

print("\nField completeness by provider:")
print(field_by_provider)



# =============================
# STEP 4 — SPREAD DISAGREEMENT
# =============================

print("\n==============================")
print("STEP 4 — SPREAD DISAGREEMENT")
print("==============================")

spread_stats = (
    df.groupby("game_id")["spread"]
      .agg(["min", "max", "mean", "std", "count"])
)

spread_stats["range"] = spread_stats["max"] - spread_stats["min"]

print("\nSpread disagreement summary:")
print(spread_stats["range"].describe())

print("\nTop 10 games by spread disagreement:")
print(spread_stats.sort_values("range", ascending=False).head(10))
"""


# =============================
# STEP 5 — CONSENSUS CHECK
# =============================
"""
print("\n==============================")
print("STEP 5 — CONSENSUS COVERAGE")
print("==============================")

consensus = df[df["provider"] == "consensus"]

consensus_games = consensus.groupby("season")["game_id"].nunique()
total_games = df.groupby("season")["game_id"].nunique()

coverage = (consensus_games / total_games).rename("consensus_coverage")

print("\nConsensus coverage by season:")
print(coverage)



# =============================
# STEP 6 — LINE MOVEMENT
# =============================

print("\n==============================")
print("STEP 6 — LINE MOVEMENT (OPEN → CLOSE)")
print("==============================")

movement = df.dropna(subset=["spread", "spread_open"]).copy()
movement["spread_move"] = movement["spread"] - movement["spread_open"]

print("\nOverall spread movement:")
print(movement["spread_move"].describe())

print("\nSpread movement by provider:")
print(
    movement.groupby("provider")["spread_move"]
    .describe())
