"""
DEBUG version: Load CSV files to PostgreSQL with verbose logging.
Run locally in VS Code to diagnose connection, permissions, schemas, and tables.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
from psycopg2 import sql


# ============================
# 🔧 FINAL CORRECT CONNECTION CONFIG
# ============================
DB_CONFIG = {
    "host": "spread-eagle-db.cluster-cbwyw8ky62xm.us-east-2.rds.amazonaws.com",
    "port": 5432,

    # ✅ DATABASE THAT ACTUALLY CONTAINS THE TABLE
    "dbname": "postgres",

    "user": "postgres",
    "password": "Sport4788!",
    "connect_timeout": 10,
}


def debug_print(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def get_connection():
    debug_print("CONNECTING TO POSTGRES")
    print("Connection parameters:")
    for k, v in DB_CONFIG.items():
        if k == "password":
            print(f"  {k}: ********")
        else:
            print(f"  {k}: {v}")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        print("✅ Connection established")
        return conn
    except Exception as e:
        print("❌ CONNECTION FAILED")
        print(type(e).__name__, e)
        sys.exit(1)


def inspect_connection(conn):
    debug_print("INSPECTING CONNECTION")
    cur = conn.cursor()

    cur.execute("""
        SELECT
            current_database(),
            current_user,
            inet_server_addr(),
            inet_server_port();
    """)
    db, user, host, port = cur.fetchone()

    print(f"Connected DB   : {db}")
    print(f"Connected User : {user}")
    print(f"Server Host    : {host}")
    print(f"Server Port    : {port}")

    print("\nVisible databases:")
    cur.execute("SELECT datname FROM pg_database ORDER BY datname;")
    for row in cur.fetchall():
        print(" -", row[0])

    print("\nVisible schemas:")
    cur.execute("""
        SELECT schema_name
        FROM information_schema.schemata
        ORDER BY schema_name;
    """)
    for row in cur.fetchall():
        print(" -", row[0])

    cur.close()


def inspect_table(conn, schema: str, table: str):
    debug_print(f"INSPECTING TABLE {schema}.{table}")
    cur = conn.cursor()

    cur.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_name = %s
        );
    """, (schema, table))

    exists = cur.fetchone()[0]
    print(f"Table exists: {exists}")

    if not exists:
        cur.close()
        return False

    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = %s
        ORDER BY ordinal_position;
    """, (schema, table))

    cols = cur.fetchall()
    print(f"Columns ({len(cols)}):")
    for name, dtype in cols:
        print(f" - {name} ({dtype})")

    cur.close()
    return True


def to_python_type(val):
    if val is None:
        return None
    if isinstance(val, float) and np.isnan(val):
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return float(val)
    if isinstance(val, np.bool_):
        return bool(val)
    return val


def normalize_column_name(col: str) -> str:
    return col.lower().replace("__", "_")


def load_csv_to_table(conn, csv_path: Path, schema: str, table: str):
    debug_print(f"LOADING CSV {csv_path.name}")

    if not csv_path.exists():
        print("❌ CSV not found:", csv_path)
        return

    df = pd.read_csv(csv_path)
    print(f"Rows in CSV: {len(df)}")

    df.columns = [normalize_column_name(c) for c in df.columns]
    print("CSV columns:", list(df.columns))

    cur = conn.cursor()

    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = %s;
    """, (schema, table))

    db_columns = {r[0] for r in cur.fetchall()}
    print("DB columns:", list(db_columns))

    common = [c for c in df.columns if c in db_columns]
    print("Common columns:", common)

    if not common:
        raise RuntimeError("NO MATCHING COLUMNS BETWEEN CSV AND TABLE")

    insert_sql = sql.SQL(
        "INSERT INTO {}.{} ({}) VALUES ({})"
    ).format(
        sql.Identifier(schema),
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, common)),
        sql.SQL(", ").join(sql.Placeholder() * len(common))
    )

    print("Insert SQL:")
    print(insert_sql.as_string(conn))

    rows = [
        tuple(to_python_type(v) for v in row)
        for row in df[common].itertuples(index=False, name=None)
    ]

    try:
        cur.executemany(insert_sql, rows)
        conn.commit()
        print(f"✅ Inserted {len(rows)} rows")
    except Exception as e:
        conn.rollback()
        print("❌ INSERT FAILED")
        print(type(e).__name__, e)
        raise
    finally:
        cur.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--table", required=True)
    args = parser.parse_args()

    conn = get_connection()
    inspect_connection(conn)

    if not inspect_table(conn, args.schema, args.table):
        print("❌ Table does not exist or is not visible")
        sys.exit(1)

    load_csv_to_table(conn, Path(args.csv), args.schema, args.table)

    conn.close()
    print("\nDONE")


if __name__ == "__main__":
    main()
