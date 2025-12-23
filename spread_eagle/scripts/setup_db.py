import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():
    # Connect to default 'postgres' database to create new db
    # Parse the DATABASE_URL to get user/pass/host, but switch dbname to postgres
    db_url = os.getenv("DATABASE_URL")
    # Parse the URL manually to get credentials
    # Format: postgresql://user:pass@host:port/dbname
    from urllib.parse import urlparse
    result = urlparse(db_url)
    username = result.username
    password = result.password
    host = result.hostname
    port = result.port
    
    try:
        # Connect to default 'postgres' database to create new db
        conn = psycopg2.connect(
            dbname="postgres",
            user=username,
            password=password,
            host=host,
            port=port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'spread_eagle'")
        exists = cur.fetchone()
        if not exists:
            print("Creating database spread_eagle...")
            cur.execute('CREATE DATABASE spread_eagle')
        else:
            print("Database spread_eagle already exists.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Failed to create database: {e}")
        print("Please ensure your postgres credentials in .env are correct and the server is running.")

if __name__ == "__main__":
    create_database()
