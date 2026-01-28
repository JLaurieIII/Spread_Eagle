"""
Explore spread data available for building teaser model.
"""
import psycopg2
import pandas as pd
import numpy as np

DB_CONFIG = {
    "host": "spread-eagle-db.cbwyw8ky62xm.us-east-2.rds.amazonaws.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "Sport4788!",
}

conn = psycopg2.connect(**DB_CONFIG)

print("=" * 80)
print("CBB SPREAD DATA EXPLORATION")
print("=" * 80)

# 1. Check betting_lines for spread data
print("\n1. SPREAD DATA AVAILABILITY")
print("-" * 60)

query = """
SELECT
    provider,
    COUNT(*) as total_lines,
    SUM(CASE WHEN spread IS NOT NULL THEN 1 ELSE 0 END) as has_spread,
    SUM(CASE WHEN over_under IS NOT NULL THEN 1 ELSE 0 END) as has_total,
    AVG(ABS(spread)) as avg_spread
FROM cbb.betting_lines
GROUP BY provider
ORDER BY total_lines DESC
"""
df = pd.read_sql(query, conn)
print(df.to_string())

# 2. Join games with lines to see spread margins
print("\n\n2. SPREAD MARGIN ANALYSIS (Bovada)")
print("-" * 60)

query = """
WITH game_results AS (
    SELECT
        bl.game_id,
        bl.start_date::date as game_date,
        bl.home_team,
        bl.away_team,
        bl.home_score,
        bl.away_score,
        bl.spread as home_spread,  -- negative = home favored
        bl.over_under as total,
        (bl.home_score - bl.away_score) as home_margin,
        (bl.home_score - bl.away_score) + bl.spread as home_cover_margin,
        (bl.home_score + bl.away_score) as actual_total,
        (bl.home_score + bl.away_score) - bl.over_under as total_margin
    FROM cbb.betting_lines bl
    WHERE bl.provider = 'Bovada'
      AND bl.home_score IS NOT NULL
      AND bl.away_score IS NOT NULL
      AND bl.spread IS NOT NULL
      AND bl.home_score > 0
)
SELECT
    COUNT(*) as games,
    AVG(ABS(home_cover_margin)) as avg_abs_cover_margin,
    STDDEV(home_cover_margin) as stddev_cover_margin,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ABS(home_cover_margin)) as median_abs_cover,

    -- How often do games stay close to the spread?
    SUM(CASE WHEN ABS(home_cover_margin) <= 3 THEN 1 ELSE 0 END)::float / COUNT(*) as within_3_rate,
    SUM(CASE WHEN ABS(home_cover_margin) <= 5 THEN 1 ELSE 0 END)::float / COUNT(*) as within_5_rate,
    SUM(CASE WHEN ABS(home_cover_margin) <= 7 THEN 1 ELSE 0 END)::float / COUNT(*) as within_7_rate,
    SUM(CASE WHEN ABS(home_cover_margin) <= 10 THEN 1 ELSE 0 END)::float / COUNT(*) as within_10_rate,

    -- Teaser survival rates (getting +8 or +10 points)
    SUM(CASE WHEN home_cover_margin >= -8 THEN 1 ELSE 0 END)::float / COUNT(*) as home_teaser_8_win_rate,
    SUM(CASE WHEN home_cover_margin >= -10 THEN 1 ELSE 0 END)::float / COUNT(*) as home_teaser_10_win_rate,
    SUM(CASE WHEN home_cover_margin <= 8 THEN 1 ELSE 0 END)::float / COUNT(*) as away_teaser_8_win_rate,
    SUM(CASE WHEN home_cover_margin <= 10 THEN 1 ELSE 0 END)::float / COUNT(*) as away_teaser_10_win_rate
FROM game_results
"""
df = pd.read_sql(query, conn)

print(f"Total games with Bovada spreads: {df['games'].iloc[0]:,}")
print(f"\nSpread Margin Statistics:")
print(f"  Avg absolute cover margin: {df['avg_abs_cover_margin'].iloc[0]:.1f} pts")
print(f"  Stddev cover margin: {df['stddev_cover_margin'].iloc[0]:.1f} pts")
print(f"  Median absolute cover margin: {df['median_abs_cover'].iloc[0]:.1f} pts")
print(f"\nGames staying close to spread:")
print(f"  Within 3 pts: {df['within_3_rate'].iloc[0]:.1%}")
print(f"  Within 5 pts: {df['within_5_rate'].iloc[0]:.1%}")
print(f"  Within 7 pts: {df['within_7_rate'].iloc[0]:.1%}")
print(f"  Within 10 pts: {df['within_10_rate'].iloc[0]:.1%}")
print(f"\nTeaser Survival Rates (baseline):")
print(f"  Home team +8 pts: {df['home_teaser_8_win_rate'].iloc[0]:.1%}")
print(f"  Home team +10 pts: {df['home_teaser_10_win_rate'].iloc[0]:.1%}")
print(f"  Away team +8 pts: {df['away_teaser_8_win_rate'].iloc[0]:.1%}")
print(f"  Away team +10 pts: {df['away_teaser_10_win_rate'].iloc[0]:.1%}")

# 3. Sample of actual games
print("\n\n3. SAMPLE GAMES WITH SPREADS")
print("-" * 60)

query = """
SELECT
    bl.start_date::date as game_date,
    bl.away_team || ' @ ' || bl.home_team as matchup,
    bl.spread as home_spread,
    bl.away_score || '-' || bl.home_score as score,
    (bl.home_score - bl.away_score) as home_margin,
    (bl.home_score - bl.away_score) + bl.spread as cover_margin,
    CASE
        WHEN (bl.home_score - bl.away_score) + bl.spread >= -8 THEN 'HOME +8 WINS'
        ELSE 'HOME +8 LOSES'
    END as home_teaser_8,
    CASE
        WHEN (bl.home_score - bl.away_score) + bl.spread <= 8 THEN 'AWAY +8 WINS'
        ELSE 'AWAY +8 LOSES'
    END as away_teaser_8
FROM cbb.betting_lines bl
WHERE bl.provider = 'Bovada'
  AND bl.home_score > 0
  AND bl.spread IS NOT NULL
ORDER BY bl.start_date DESC
LIMIT 20
"""
df = pd.read_sql(query, conn)
print(df.to_string())

conn.close()
print("\n" + "=" * 80)
