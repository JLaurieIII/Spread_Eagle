"""
Quick schema setup script.

Run DDL to create cbb schema and all tables.
"""
from pathlib import Path
import psycopg2

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from spread_eagle.config.settings import settings


def main():
    ddl_path = Path(__file__).parent.parent.parent.parent / "data" / "cbb" / "ddl" / "create_tables.sql"

    if not ddl_path.exists():
        print(f"DDL file not found: {ddl_path}")
        return

    print(f"Connecting to: {settings.db_host}:{settings.db_port}/{settings.db_name}")

    conn = psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        connect_timeout=30,
    )

    ddl = ddl_path.read_text()
    cur = conn.cursor()
    cur.execute(ddl)
    conn.commit()
    cur.close()
    conn.close()

    print("Done! Schema and tables created.")


if __name__ == "__main__":
    main()
