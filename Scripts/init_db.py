import os
import sys

import psycopg2


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    sql_path = os.path.join(root, "db", "initialize.sql")
    if not os.path.exists(sql_path):
        print(f"SQL file not found: {sql_path}")
        sys.exit(1)

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        host = os.environ.get("PGHOST", "127.0.0.1")
        port = os.environ.get("PGPORT", "5432")
        user = os.environ.get("PGUSER") or os.environ.get("USER") or os.environ.get("USERNAME")
        password = os.environ.get("PGPASSWORD", "")
        database = os.environ.get("PGDATABASE", "postgres")
        if not user:
            print("Set DATABASE_URL or PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE environment variables.")
            sys.exit(1)
        dsn = f"host={host} port={port} user={user} password={password} dbname={database}"

    print(f"Connecting to Postgres with DSN/env ...")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    print("Database initialized and seeded successfully.")


if __name__ == "__main__":
    os.environ["DATABASE_URL"] = "postgresql://postgres:5369@localhost:5432/postgres"
    main()

