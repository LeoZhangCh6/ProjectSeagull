"""
Migration script to add last_access_time column to available_signals table.

Run this script to update existing databases with the new tracking column.

Usage:
    python Scripts/migrate_add_last_access_time.py
"""

import os
import sys

# Add project root to path
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from Common.db import get_pg_conn


def migrate():
    """Add last_access_time column to available_signals table."""
    print("=" * 60)
    print("Migration: Add last_access_time to available_signals")
    print("=" * 60)
    
    # Check database connection
    if not (os.environ.get("DATABASE_URL") or os.environ.get("PGHOST")):
        print("ERROR: DATABASE_URL or PGHOST environment variable not set.")
        print("Please configure database connection before running migration.")
        return 1
    
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                # Check if column already exists
                cur.execute(
                    """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'available_signals' 
                    AND column_name = 'last_access_time'
                    """
                )
                
                if cur.fetchone():
                    print("Column 'last_access_time' already exists. No migration needed.")
                    return 0
                
                print("Adding 'last_access_time' column to available_signals table...")
                
                # Add the column
                cur.execute(
                    """
                    ALTER TABLE available_signals 
                    ADD COLUMN last_access_time timestamptz
                    """
                )
                
                conn.commit()
                print("✓ Successfully added last_access_time column")
                
                # Show current signals
                cur.execute("SELECT COUNT(*) FROM available_signals")
                count = cur.fetchone()[0]
                print(f"  {count} signals in table")
                print(f"  last_access_time will be updated automatically when signals are used")
                
                return 0
                
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return 1


if __name__ == "__main__":
    os.environ['MASSIVE_API_KEY'] = "Y2mALom8TLdet7Bc8ktLeQ4355hAdpG6"
    os.environ['NASDAQ_DATA_LINK_API_KEY'] = "s_phvq25xVMyCa6KBXFj"
    os.environ["DATABASE_URL"] = "postgresql://postgres:5369@localhost:5432/postgres"
    sys.exit(migrate())
