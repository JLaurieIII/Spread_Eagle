"""
Single-Leg Teaser Strategy

Instead of requiring BOTH teams to survive, pick the SAFER leg from each game.

Strategy:
1. For each game, identify which team has higher teaser survival probability
2. Select games where the safer team has very high (>90%) survival expectation
3. Build 3-4 leg parlays from these "premium" legs
"""
import psycopg2
import pandas as pd
import numpy as np
from itertools import combinations

DB_CONFIG = {
    "host": "spread-eagle-db.cbwyw8ky62xm.us-east-2.rds.amazonaws.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "Sport4788!",
}

conn = psycopg2.connect(**DB_CONFIG)

print("=" * 80)
print("SINGLE-LEG TEASER STRATEGY")
print("=" * 80)

# Load data
query = """
SELECT *
FROM marts_cbb.fct_cbb__teaser_matchups
WHERE has_sufficient_history = true
  AND is_completed = true
ORDER BY game_date, game_id
"""
df = pd.read_sql(query, conn)
print(f"\nLoaded {len(df):,} games")

# =============================================================================
# CREATE SINGLE-LEG PICKS
# =============================================================================
print("\n" + "=" * 80)
print("IDENTIFYING SAFER LEG PER GAME")
print("=" * 80)

# For each game, determine which team is the safer teaser pick
df['home_expected_surv'] = df['home_teaser_10_surv_l10'].fillna(0.80)
df['away_expected_surv'] = df['away_teaser_10_surv_l10'].fillna(0.80)

# Pick the safer leg
df['safer_is_home'] = df['home_expected_surv'] >= df['away_expected_surv']
df['safer_expected_surv'] = np.where(
    df['safer_is_home'],
    df['home_expected_surv'],
    df['away_expected_surv']
)
df['safer_actual_win'] = np.where(
    df['safer_is_home'],
    df['home_teaser_10_win'],
    df['away_teaser_10_win']
)

# Also track the less safe leg
df['other_expected_surv'] = np.where(
    df['safer_is_home'],
    df['away_expected_surv'],
    df['home_expected_surv']
)

print(f"\nSafer Leg Statistics:")
print(f"  Avg expected survival: {df['safer_expected_surv'].mean():.1%}")
print(f"  Actual survival rate:  {df['safer_actual_win'].mean():.1%}")

# =============================================================================
# BACKTEST BY EXPECTED SURVIVAL THRESHOLD
# =============================================================================
print("\n" + "=" * 80)
print("SINGLE-LEG SURVIVAL BY EXPECTED RATE")
print("=" * 80)

thresholds = [0.70, 0.80, 0.85, 0.90, 0.95, 1.00]

print(f"{'Min Expected':>15} {'Games':>8} {'Actual Win%':>12} {'Lift':>10}")
print("-" * 50)

baseline = df['safer_actual_win'].mean()

for min_surv in thresholds:
    filtered = df[df['safer_expected_surv'] >= min_surv]
    if len(filtered) > 10:
        actual = filtered['safer_actual_win'].mean()
        lift = actual - baseline
        print(f"{min_surv:>14.0%} {len(filtered):>8} {actual:>11.1%} {lift:>+9.1%}")

# =============================================================================
# 3-LEG PARLAY SIMULATION (Single Leg Strategy)
# =============================================================================
print("\n" + "=" * 80)
print("3-LEG PARLAY SIMULATION (Picking Safer Leg)")
print("=" * 80)

def simulate_single_leg_parlays(df_filtered, n_legs=3, n_simulations=500):
    """Simulate parlays picking the safer leg from each game."""
    if len(df_filtered) < n_legs:
        return None, 0, 0

    wins = 0
    total = 0

    dates = df_filtered['game_date'].unique()
    np.random.shuffle(dates)

    for date in dates:
        day_games = df_filtered[df_filtered['game_date'] == date]
        if len(day_games) < n_legs:
            continue

        # Try combinations
        for combo in combinations(day_games.index, n_legs):
            selected = df_filtered.loc[list(combo)]
            # Parlay wins if ALL safer legs win
            parlay_win = selected['safer_actual_win'].all()
            wins += parlay_win
            total += 1

            if total >= n_simulations:
                break
        if total >= n_simulations:
            break

    if total == 0:
        return None, 0, 0

    return wins / total, wins, total


filters = [
    ("All games (safer leg)", df, 0.0),
    ("Expected >= 80%", df[df['safer_expected_surv'] >= 0.80], 0.80),
    ("Expected >= 85%", df[df['safer_expected_surv'] >= 0.85], 0.85),
    ("Expected >= 90%", df[df['safer_expected_surv'] >= 0.90], 0.90),
    ("Expected >= 95%", df[df['safer_expected_surv'] >= 0.95], 0.95),
    ("Expected = 100%", df[df['safer_expected_surv'] >= 1.00], 1.00),
]

print(f"\n{'Filter':<30} {'Games':>8} {'Single':>10} {'3-Leg':>10} {'4-Leg':>10}")
print("-" * 75)

for name, df_filt, _ in filters:
    n_games = len(df_filt)

    if n_games < 3:
        print(f"{name:<30} {n_games:>8} {'N/A':>10} {'N/A':>10} {'N/A':>10}")
        continue

    single = df_filt['safer_actual_win'].mean()
    wr3, _, _ = simulate_single_leg_parlays(df_filt, n_legs=3, n_simulations=500)
    wr4, _, _ = simulate_single_leg_parlays(df_filt, n_legs=4, n_simulations=500)

    single_str = f"{single:.1%}"
    wr3_str = f"{wr3:.1%}" if wr3 else "N/A"
    wr4_str = f"{wr4:.1%}" if wr4 else "N/A"

    print(f"{name:<30} {n_games:>8} {single_str:>10} {wr3_str:>10} {wr4_str:>10}")

# =============================================================================
# EXPECTED VALUE
# =============================================================================
print("\n" + "=" * 80)
print("EXPECTED VALUE ANALYSIS")
print("=" * 80)

print("\nBreakeven Win Rates:")
print("  3-leg teaser (-140): 58.3%")
print("  4-leg teaser (+150): 40.0%")

# Best filter
best_filter = df[df['safer_expected_surv'] >= 0.90]
if len(best_filter) >= 3:
    wr3, _, _ = simulate_single_leg_parlays(best_filter, n_legs=3, n_simulations=500)
    wr4, _, _ = simulate_single_leg_parlays(best_filter, n_legs=4, n_simulations=500)

    print(f"\nUsing 'Expected >= 90%' filter:")
    print(f"  Games available: {len(best_filter)}")
    if wr3:
        ev3 = (wr3 * 100) - ((1 - wr3) * 140)
        print(f"  3-leg win rate: {wr3:.1%} (breakeven: 58.3%)")
        print(f"  3-leg EV per $140 risked: ${ev3:+.2f}")
    if wr4:
        ev4 = (wr4 * 150) - ((1 - wr4) * 100)
        print(f"  4-leg win rate: {wr4:.1%} (breakeven: 40.0%)")
        print(f"  4-leg EV per $100 risked: ${ev4:+.2f}")

# =============================================================================
# TODAY'S PICKS
# =============================================================================
print("\n" + "=" * 80)
print("TODAY'S TEASER CANDIDATES (Jan 10)")
print("=" * 80)

# Get today's games (not yet played)
query_today = """
SELECT
    game_date,
    away_team || ' @ ' || home_team as matchup,
    home_spread,
    home_teaser_10_surv_l10 as home_surv,
    away_teaser_10_surv_l10 as away_surv,
    home_stddev_cover_l10 as home_vol,
    away_stddev_cover_l10 as away_vol,
    home_blowout_rate as home_blowout,
    away_blowout_rate as away_blowout
FROM marts_cbb.fct_cbb__teaser_matchups
WHERE game_date = '2026-01-10'
  AND has_sufficient_history = true
ORDER BY
    GREATEST(home_teaser_10_surv_l10, away_teaser_10_surv_l10) DESC NULLS LAST
"""
df_today = pd.read_sql(query_today, conn)

if len(df_today) > 0:
    print(f"\nFound {len(df_today)} games today with sufficient history\n")

    for _, row in df_today.head(15).iterrows():
        home_surv = row['home_surv'] or 0.80
        away_surv = row['away_surv'] or 0.80
        safer = "HOME" if home_surv >= away_surv else "AWAY"
        safer_surv = max(home_surv, away_surv)
        safer_vol = row['home_vol'] if safer == "HOME" else row['away_vol']

        print(f"{row['matchup']}")
        print(f"  Spread: {row['home_spread']:+.1f}")
        print(f"  Home: {home_surv:.0%} survival, {row['home_vol'] or 0:.1f} vol, {row['home_blowout'] or 0:.0%} blowout")
        print(f"  Away: {away_surv:.0%} survival, {row['away_vol'] or 0:.1f} vol, {row['away_blowout'] or 0:.0%} blowout")
        print(f"  >>> SAFER LEG: {safer} ({safer_surv:.0%} expected)")
        print()
else:
    print("No games found for today with sufficient history")

conn.close()
print("=" * 80)
