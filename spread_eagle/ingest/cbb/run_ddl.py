"""
Run DDL against PostgreSQL RDS.

Usage:
    python -m spread_eagle.ingest.cbb.run_ddl
"""
from __future__ import annotations

from pathlib import Path

import psycopg2

from spread_eagle.config import settings


def main():
    print("=" * 60)
    print("  RUN DDL ON RDS")
    print("=" * 60)

    ddl_path = Path("data/cbb/ddl/create_tables.sql")

    if not ddl_path.exists():
        print(f"  ERROR: {ddl_path} not found")
        print("  Run: python -m spread_eagle.ingest.cbb.generate_ddl")
        return

    # Read DDL
    ddl = ddl_path.read_text()
    print(f"  Loaded: {ddl_path}")
    print(f"  DDL size: {len(ddl):,} chars")

    # Connect to RDS
    print("\n  Connecting to RDS...")
    conn = psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        connect_timeout=30,
    )
    conn.autocommit = True
    cur = conn.cursor()

    print("  Connected!")

    # Execute DDL
    print("\n  Executing DDL...")

    # Split by semicolon and execute each statement
    statements = [s.strip() for s in ddl.split(";") if s.strip() and not s.strip().startswith("--")]

    for i, stmt in enumerate(statements):
        if not stmt:
            continue
        try:
            cur.execute(stmt)
            # Extract table name for progress
            if "CREATE TABLE" in stmt:
                table_name = stmt.split("CREATE TABLE IF NOT EXISTS")[1].split("(")[0].strip()
                print(f"    Created: {table_name}")
            elif "CREATE SCHEMA" in stmt:
                print(f"    Created schema: cbb")
        except Exception as e:
            print(f"    ERROR on statement {i}: {e}")

    print("\n  DDL execution complete!")

    # Verify tables
    print("\n  Verifying tables...")
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'cbb'
        ORDER BY table_name
    """)
    tables = [r[0] for r in cur.fetchall()]
    print(f"  Tables in cbb schema: {len(tables)}")
    for t in tables:
        print(f"    - {t}")

    cur.close()
    conn.close()

    print("\n  DONE!")


if __name__ == "__main__":
    main()
