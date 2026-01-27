"""
Teaser Betting Strategy Backtest

Strategy: Select games with LOW volatility and HIGH teaser survival rates,
then parlay 3-4 games with +10 point teasers.

Key metrics to filter on:
- combined_teaser_10_survival: historical teaser win rate for both teams
- combined_stddev_cover: volatility of cover margins (lower = more predictable)
- combined_blowout_rate: rate of blowout losses (lower = safer)
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
print("CBB TEASER STRATEGY BACKTEST")
print("=" * 80)

# =============================================================================
# 1. LOAD DATA
# =============================================================================
query = """
SELECT *
FROM marts_cbb.fct_cbb__teaser_matchups
WHERE has_sufficient_history = true
  AND is_completed = true
ORDER BY game_date, game_id
"""
df = pd.read_sql(query, conn)
print(f"\nLoaded {len(df):,} completed games with sufficient history")
print(f"Date range: {df['game_date'].min()} to {df['game_date'].max()}")

# =============================================================================
# 2. OVERALL STATISTICS
# =============================================================================
print("\n" + "=" * 80)
print("OVERALL TEASER SURVIVAL RATES")
print("=" * 80)

home_8_rate = df['home_teaser_8_win'].mean()
away_8_rate = df['away_teaser_8_win'].mean()
home_10_rate = df['home_teaser_10_win'].mean()
away_10_rate = df['away_teaser_10_win'].mean()
both_8_rate = df['both_teams_teaser_8_win'].mean()
both_10_rate = df['both_teams_teaser_10_win'].mean()

print(f"\nSingle Leg Survival Rates:")
print(f"  Home +8:  {home_8_rate:.1%}")
print(f"  Away +8:  {away_8_rate:.1%}")
print(f"  Home +10: {home_10_rate:.1%}")
print(f"  Away +10: {away_10_rate:.1%}")

print(f"\nBoth Teams Survive (single game):")
print(f"  Both +8:  {both_8_rate:.1%}")
print(f"  Both +10: {both_10_rate:.1%}")

# =============================================================================
# 3. VOLATILITY ANALYSIS
# =============================================================================
print("\n" + "=" * 80)
print("VOLATILITY DISTRIBUTION")
print("=" * 80)

print(f"\nCombined Teaser 10 Survival Distribution:")
print(df['combined_teaser_10_survival'].describe())

print(f"\nCombined Stddev Cover Distribution:")
print(df['combined_stddev_cover'].describe())

# =============================================================================
# 4. FILTER BY VOLATILITY - FIND PREMIUM GAMES
# =============================================================================
print("\n" + "=" * 80)
print("TEASER SURVIVAL BY VOLATILITY BUCKET")
print("=" * 80)

# Create volatility buckets
df['volatility_bucket'] = pd.cut(
    df['combined_stddev_cover'],
    bins=[0, 8, 10, 12, 15, 100],
    labels=['Very Low (<8)', 'Low (8-10)', 'Medium (10-12)', 'High (12-15)', 'Very High (>15)']
)

# Survival rates by bucket
vol_analysis = df.groupby('volatility_bucket', observed=True).agg({
    'game_id': 'count',
    'both_teams_teaser_10_win': 'mean',
    'home_teaser_10_win': 'mean',
    'away_teaser_10_win': 'mean',
}).round(3)
vol_analysis.columns = ['games', 'both_survive_rate', 'home_rate', 'away_rate']

print("\n+10 Teaser Survival by Volatility:")
print(f"{'Volatility':<20} {'Games':>8} {'Both Survive':>14} {'Home':>8} {'Away':>8}")
print("-" * 60)
for idx, row in vol_analysis.iterrows():
    print(f"{str(idx):<20} {int(row['games']):>8} {row['both_survive_rate']:>13.1%} {row['home_rate']:>7.1%} {row['away_rate']:>7.1%}")

# =============================================================================
# 5. FILTER BY HISTORICAL SURVIVAL RATE
# =============================================================================
print("\n" + "=" * 80)
print("TEASER SURVIVAL BY HISTORICAL SURVIVAL RATE")
print("=" * 80)

df['survival_bucket'] = pd.cut(
    df['combined_teaser_10_survival'],
    bins=[0, 0.7, 0.8, 0.85, 0.9, 1.0],
    labels=['<70%', '70-80%', '80-85%', '85-90%', '>90%']
)

surv_analysis = df.groupby('survival_bucket', observed=True).agg({
    'game_id': 'count',
    'both_teams_teaser_10_win': 'mean',
    'home_teaser_10_win': 'mean',
    'away_teaser_10_win': 'mean',
}).round(3)
surv_analysis.columns = ['games', 'both_survive_rate', 'home_rate', 'away_rate']

print("\n+10 Teaser Survival by Historical Team Survival Rate:")
print(f"{'Hist Survival':<15} {'Games':>8} {'Both Survive':>14} {'Home':>8} {'Away':>8}")
print("-" * 60)
for idx, row in surv_analysis.iterrows():
    print(f"{str(idx):<15} {int(row['games']):>8} {row['both_survive_rate']:>13.1%} {row['home_rate']:>7.1%} {row['away_rate']:>7.1%}")

# =============================================================================
# 6. BACKTEST PARLAY STRATEGY
# =============================================================================
print("\n" + "=" * 80)
print("PARLAY BACKTEST SIMULATION")
print("=" * 80)

def simulate_parlays(df_filtered, n_legs=3, n_simulations=1000):
    """
    Simulate random parlays from filtered games.
    Returns win rate and statistics.
    """
    if len(df_filtered) < n_legs:
        return None, 0, 0

    wins = 0
    total = 0

    # Group by date to simulate daily picks
    for date, day_games in df_filtered.groupby('game_date'):
        if len(day_games) < n_legs:
            continue

        # Pick random n_legs games from this day
        if len(day_games) >= n_legs:
            # Try all possible combinations for this day
            for combo in combinations(day_games.index, n_legs):
                selected = df_filtered.loc[list(combo)]
                # Parlay wins if ALL legs win
                parlay_win = selected['both_teams_teaser_10_win'].all()
                wins += parlay_win
                total += 1

                if total >= n_simulations:
                    break
        if total >= n_simulations:
            break

    if total == 0:
        return None, 0, 0

    win_rate = wins / total
    return win_rate, wins, total


print("\nSimulating 3-leg and 4-leg parlays at different filters...")
print("(Using +10 point teasers, requiring BOTH teams to survive in each game)\n")

# Different filter strategies
filters = [
    ("All games", df),
    ("Low volatility (<10)", df[df['combined_stddev_cover'] < 10]),
    ("Very low volatility (<8)", df[df['combined_stddev_cover'] < 8]),
    ("High survival (>85%)", df[df['combined_teaser_10_survival'] > 0.85]),
    ("High survival (>90%)", df[df['combined_teaser_10_survival'] > 0.90]),
    ("Combined: Low vol + High surv", df[(df['combined_stddev_cover'] < 10) & (df['combined_teaser_10_survival'] > 0.85)]),
    ("Premium: Very low vol + Very high surv", df[(df['combined_stddev_cover'] < 8) & (df['combined_teaser_10_survival'] > 0.90)]),
]

print(f"{'Filter':<40} {'Games':>8} {'3-Leg WR':>10} {'4-Leg WR':>10}")
print("-" * 70)

for name, df_filt in filters:
    n_games = len(df_filt)

    if n_games < 3:
        print(f"{name:<40} {n_games:>8} {'N/A':>10} {'N/A':>10}")
        continue

    wr3, _, _ = simulate_parlays(df_filt, n_legs=3, n_simulations=500)
    wr4, _, _ = simulate_parlays(df_filt, n_legs=4, n_simulations=500)

    wr3_str = f"{wr3:.1%}" if wr3 else "N/A"
    wr4_str = f"{wr4:.1%}" if wr4 else "N/A"

    print(f"{name:<40} {n_games:>8} {wr3_str:>10} {wr4_str:>10}")

# =============================================================================
# 7. EXPECTED VALUE CALCULATION
# =============================================================================
print("\n" + "=" * 80)
print("EXPECTED VALUE ANALYSIS")
print("=" * 80)

# Typical teaser parlay odds
odds_3leg = -140  # Risk 140 to win 100
odds_4leg = +150  # Risk 100 to win 150

def ev_calc(win_rate, odds):
    """Calculate expected value per $100 risked."""
    if odds > 0:
        # Positive odds: win amount on $100 bet
        win_amount = odds
        risk = 100
    else:
        # Negative odds: risk amount to win $100
        win_amount = 100
        risk = -odds

    ev = (win_rate * win_amount) - ((1 - win_rate) * risk)
    return ev

print("\nBreakeven Win Rates:")
print(f"  3-leg teaser (-140): {140/(100+140):.1%}")
print(f"  4-leg teaser (+150): {100/(100+150):.1%}")

print("\nExpected Value per $100 risked (using Premium filter):")
df_premium = df[(df['combined_stddev_cover'] < 8) & (df['combined_teaser_10_survival'] > 0.90)]
if len(df_premium) >= 3:
    premium_wr3, _, _ = simulate_parlays(df_premium, n_legs=3, n_simulations=500)
    premium_wr4, _, _ = simulate_parlays(df_premium, n_legs=4, n_simulations=500)

    if premium_wr3:
        ev3 = ev_calc(premium_wr3, odds_3leg)
        print(f"  3-leg ({premium_wr3:.1%} WR at -140): ${ev3:+.2f}")

    if premium_wr4:
        ev4 = ev_calc(premium_wr4, odds_4leg)
        print(f"  4-leg ({premium_wr4:.1%} WR at +150): ${ev4:+.2f}")
else:
    print("  Not enough premium games for analysis")

conn.close()
print("\n" + "=" * 80)
