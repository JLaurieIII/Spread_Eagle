"""
Explore raw CBB data to understand what we're working with.
"""
import psycopg2
import pandas as pd

DB_CONFIG = {
    "host": "spread-eagle-db.cbwyw8ky62xm.us-east-2.rds.amazonaws.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "Sport4788!",
}

conn = psycopg2.connect(**DB_CONFIG)

print("=" * 80)
print("RAW CBB DATA EXPLORATION")
print("=" * 80)

# 1. Check game_team_stats columns
cur = conn.cursor()
cur.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'cbb' AND table_name = 'game_team_stats'
    ORDER BY ordinal_position
""")
cols = [r[0] for r in cur.fetchall()]
print(f"\n1. RAW GAME_TEAM_STATS COLUMNS ({len(cols)} columns):")
print("-" * 60)
for c in cols:
    print(f"   {c}")

# 2. Sample data from game_team_stats
print("\n\n2. SAMPLE GAME_TEAM_STATS DATA (1 game):")
print("-" * 60)
query = """
SELECT * FROM cbb.game_team_stats
WHERE game_id = (SELECT game_id FROM cbb.game_team_stats LIMIT 1)
LIMIT 2
"""
df = pd.read_sql(query, conn)
# Show as key-value for readability
for col in df.columns:
    vals = df[col].tolist()
    print(f"   {col}: {vals}")

# 3. Count of games by season
print("\n\n3. GAMES BY SEASON:")
print("-" * 60)
query = """
SELECT season, COUNT(DISTINCT game_id) as games
FROM cbb.game_team_stats
GROUP BY season
ORDER BY season
"""
df = pd.read_sql(query, conn)
for _, row in df.iterrows():
    print(f"   Season {row['season']}: {row['games']} games")

# 4. Check betting_lines
print("\n\n4. BETTING LINES SAMPLE:")
print("-" * 60)
cur.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'cbb' AND table_name = 'betting_lines'
    ORDER BY ordinal_position
""")
cols = [r[0] for r in cur.fetchall()]
print(f"   Columns: {cols}")

query = """
SELECT provider, COUNT(*) as cnt,
       AVG(over_under) as avg_total,
       MIN(over_under) as min_total,
       MAX(over_under) as max_total
FROM cbb.betting_lines
WHERE over_under IS NOT NULL
GROUP BY provider
"""
df = pd.read_sql(query, conn)
print("\n   Lines by Provider:")
for _, row in df.iterrows():
    print(f"   {row['provider']}: {row['cnt']} lines, avg total={row['avg_total']:.1f}")

# 5. Data quality check - how many games have both stats and lines?
print("\n\n5. DATA QUALITY - GAMES WITH STATS + LINES:")
print("-" * 60)
query = """
SELECT
    COUNT(DISTINCT gts.game_id) as games_with_stats,
    COUNT(DISTINCT bl.game_id) as games_with_lines,
    COUNT(DISTINCT CASE WHEN gts.game_id = bl.game_id THEN gts.game_id END) as games_with_both
FROM cbb.game_team_stats gts
FULL OUTER JOIN cbb.betting_lines bl ON gts.game_id = bl.game_id
"""
df = pd.read_sql(query, conn)
print(f"   Games with team stats: {df['games_with_stats'].iloc[0]}")
print(f"   Games with betting lines: {df['games_with_lines'].iloc[0]}")
print(f"   Games with BOTH: {df['games_with_both'].iloc[0]}")

conn.close()
print("\n" + "=" * 80)
