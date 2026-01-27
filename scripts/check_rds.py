"""Compare local vs RDS data."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import psycopg2

# Check LOCAL
print("=== LOCAL POSTGRES ===")
conn = psycopg2.connect(
    host='localhost', port=5432, database='spread_eagle',
    user='postgres', password='Sport4788!'
)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM cbb.games")
print(f"Total games: {cur.fetchone()[0]}")
cur.execute("SELECT MAX(start_date) FROM cbb.games")
print(f"Latest: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM cbb.games WHERE start_date::date = '2026-01-27'")
print(f"Games for Jan 27 2026: {cur.fetchone()[0]}")
conn.close()

# Check RDS
print("\n=== RDS ===")
conn = psycopg2.connect(
    host='spread-eagle-db.cbwyw8ky62xm.us-east-2.rds.amazonaws.com',
    port=5432, database='postgres', user='postgres', password='Sport4788!',
    sslmode='require'
)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM cbb.games")
print(f"Total games: {cur.fetchone()[0]}")
cur.execute("SELECT MAX(start_date) FROM cbb.games")
print(f"Latest: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM cbb.games WHERE start_date::date = '2026-01-27'")
print(f"Games for Jan 27 2026: {cur.fetchone()[0]}")
conn.close()
