"""
Test database connection using credentials from Secrets Manager.
"""
import json
import boto3
import psycopg2

def get_db_credentials():
    """Fetch database credentials from Secrets Manager."""
    client = boto3.client('secretsmanager', region_name='us-east-2')
    secret = client.get_secret_value(SecretId='spread-eagle/db')
    return json.loads(secret['SecretString'])

def test_connection():
    """Test PostgreSQL connection."""
    print("Fetching credentials from Secrets Manager...")
    creds = get_db_credentials()

    print(f"Host: {creds['host']}")
    print(f"Port: {creds['port']}")
    print(f"Database: {creds['database']}")
    print(f"Username: {creds['username']}")
    print("Password: ******* (hidden)")

    print("\nConnecting to PostgreSQL...")

    conn = psycopg2.connect(
        host=creds['host'],
        port=creds['port'],
        database=creds['database'],
        user=creds['username'],
        password=creds['password'],
        connect_timeout=10
    )

    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"\n✅ SUCCESS! Connected to:\n{version}")

    # Create schemas for future use
    print("\nCreating schemas (raw, staging, analytics)...")
    cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    cur.execute("CREATE SCHEMA IF NOT EXISTS staging;")
    cur.execute("CREATE SCHEMA IF NOT EXISTS analytics;")
    conn.commit()
    print("✅ Schemas created!")

    cur.close()
    conn.close()
    print("\nConnection closed. Database is ready!")

if __name__ == "__main__":
    test_connection()
