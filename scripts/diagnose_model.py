"""
Diagnose why the O/U model is performing worse than random.

Hypothesis testing:
1. Are rolling stats being calculated correctly?
2. Is there data leakage (or anti-leakage)?
3. How does Vegas line alone perform as a baseline?
4. Are the features actually predictive?
"""
import psycopg2
import pandas as pd
import numpy as np
from scipy import stats

DB_CONFIG = {
    "host": "spread-eagle-db.cbwyw8ky62xm.us-east-2.rds.amazonaws.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "Sport4788!",
}

conn = psycopg2.connect(**DB_CONFIG)

print("=" * 80)
print("CBB O/U MODEL DIAGNOSTICS")
print("=" * 80)

# =============================================================================
# TEST 1: Vegas Line as Baseline
# =============================================================================
print("\n\n1. BASELINE TEST: Vegas Line Alone")
print("-" * 60)

query = """
SELECT
    game_date,
    vegas_total,
    actual_total,
    CASE WHEN actual_total > vegas_total THEN 1 ELSE 0 END as over_hit
FROM marts_cbb.fct_cbb__ml_features_ou
WHERE is_completed = true
  AND actual_total > 0
  AND vegas_total IS NOT NULL
ORDER BY game_date
"""
df = pd.read_sql(query, conn)

# If we just predict vegas_total, what's our MAE?
vegas_mae = np.abs(df['actual_total'] - df['vegas_total']).mean()
vegas_rmse = np.sqrt(((df['actual_total'] - df['vegas_total'])**2).mean())

# What's the over rate?
over_rate = df['over_hit'].mean()

print(f"   Games analyzed: {len(df):,}")
print(f"   Vegas MAE: {vegas_mae:.2f} points (baseline to beat)")
print(f"   Vegas RMSE: {vegas_rmse:.2f} points")
print(f"   Actual Over Rate: {over_rate:.1%}")
print(f"   (If over_rate != 50%, market is miscalibrated or data issue)")

# =============================================================================
# TEST 2: Rolling Stats Verification
# =============================================================================
print("\n\n2. ROLLING STATS VERIFICATION")
print("-" * 60)
print("   Checking if rolling averages make sense for a sample team...")

query = """
SELECT
    rs.game_date,
    rs.team_id,
    t.display_name as team_name,
    gs.points_scored as actual_pts_this_game,
    rs.avg_points_scored_l5 as rolling_avg_before_game,
    rs.games_played_season
FROM intermediate_cbb.int_cbb__team_rolling_stats rs
JOIN intermediate_cbb.int_cbb__team_game_stats gs
    ON rs.game_id = gs.game_id AND rs.team_id = gs.team_id
JOIN cbb.teams t ON rs.team_id = t.id
WHERE rs.season = 2026
  AND rs.games_played_season >= 5
ORDER BY t.display_name, rs.game_date
LIMIT 30
"""
df_roll = pd.read_sql(query, conn)
print(df_roll.to_string())

# =============================================================================
# TEST 3: Feature Correlations with Target
# =============================================================================
print("\n\n3. FEATURE CORRELATIONS WITH ACTUAL_TOTAL")
print("-" * 60)

query = """
SELECT
    vegas_total,
    actual_total,
    combined_avg_total_l5,
    combined_avg_total_l10,
    combined_avg_pace_l5,
    home_avg_pts_scored_l5,
    away_avg_pts_scored_l5,
    home_avg_def_rating_l5,
    away_avg_def_rating_l5
FROM marts_cbb.fct_cbb__ml_features_ou
WHERE is_completed = true
  AND actual_total > 0
  AND has_sufficient_history = true
"""
df_feat = pd.read_sql(query, conn)

print(f"   Correlation with actual_total:")
for col in df_feat.columns:
    if col != 'actual_total':
        corr = df_feat['actual_total'].corr(df_feat[col])
        print(f"   {col:<35} r = {corr:+.3f}")

# =============================================================================
# TEST 4: Check for Data Issues
# =============================================================================
print("\n\n4. DATA QUALITY CHECKS")
print("-" * 60)

# How many games have NULL rolling stats?
query = """
SELECT
    COUNT(*) as total_games,
    SUM(CASE WHEN combined_avg_total_l5 IS NULL THEN 1 ELSE 0 END) as null_combined_l5,
    SUM(CASE WHEN home_avg_pts_scored_l5 IS NULL THEN 1 ELSE 0 END) as null_home_pts,
    SUM(CASE WHEN vegas_total IS NULL THEN 1 ELSE 0 END) as null_vegas,
    SUM(CASE WHEN actual_total = 0 THEN 1 ELSE 0 END) as zero_total,
    SUM(CASE WHEN actual_total IS NULL THEN 1 ELSE 0 END) as null_total
FROM marts_cbb.fct_cbb__ml_features_ou
"""
df_quality = pd.read_sql(query, conn)
print(df_quality.to_string())

# =============================================================================
# TEST 5: Simple Linear Model Test
# =============================================================================
print("\n\n5. SIMPLE MODEL TEST (Vegas + Combined Avg)")
print("-" * 60)

query = """
SELECT
    game_date,
    vegas_total,
    actual_total,
    combined_avg_total_l5,
    CASE WHEN actual_total > vegas_total THEN 1 ELSE 0 END as over_hit
FROM marts_cbb.fct_cbb__ml_features_ou
WHERE is_completed = true
  AND actual_total > 0
  AND combined_avg_total_l5 IS NOT NULL
ORDER BY game_date
"""
df_simple = pd.read_sql(query, conn)

# Simple rule: if combined_avg > vegas, predict over
df_simple['pred_over'] = (df_simple['combined_avg_total_l5'] > df_simple['vegas_total']).astype(int)
simple_accuracy = (df_simple['pred_over'] == df_simple['over_hit']).mean()

print(f"   Simple rule: Predict OVER if team's combined avg L5 > Vegas")
print(f"   Accuracy: {simple_accuracy:.1%}")

# Better simple model: average of vegas and combined_avg
df_simple['simple_pred'] = (df_simple['vegas_total'] + df_simple['combined_avg_total_l5']) / 2
df_simple['better_pred_over'] = (df_simple['simple_pred'] > df_simple['vegas_total']).astype(int)

simple_mae = np.abs(df_simple['actual_total'] - df_simple['simple_pred']).mean()
print(f"\n   Blended prediction (avg of Vegas + Combined L5):")
print(f"   MAE: {simple_mae:.2f} points")

conn.close()
print("\n" + "=" * 80)
