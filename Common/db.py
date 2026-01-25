import os
from typing import Optional

import psycopg2


def get_pg_conn(
    dsn: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    database: Optional[str] = None,
):
    """
    Create a psycopg2 connection from either a DSN (DATABASE_URL) or discrete env vars.
    Env precedence: DSN (DATABASE_URL), then PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE.
    """
    dsn = dsn or os.environ.get("DATABASE_URL")
    if dsn:
        return psycopg2.connect(dsn)
    host = host or os.environ.get("PGHOST", "127.0.0.1")
    port = port or os.environ.get("PGPORT", "5432")
    user = user or os.environ.get("PGUSER", os.environ.get("USER") or os.environ.get("USERNAME"))
    password = password or os.environ.get("PGPASSWORD")
    database = database or os.environ.get("PGDATABASE", "postgres")
    return psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=database,
    )

