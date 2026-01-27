"""
Migration: Add code storage to agents_registry table

This migration adds a 'code' column to store the actual Python agent code in the database.
After this migration, agents will be loaded from the database rather than from files.

Usage:
    python Scripts/migrate_add_agent_code_storage.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from Common.db import get_pg_conn


def migrate():
    """Add code storage column to agents_registry table."""
    print("="*60)
    print("Migration: Add Agent Code Storage")
    print("="*60)
    
    if not (os.environ.get("DATABASE_URL") or os.environ.get("PGHOST")):
        print("ERROR: DATABASE_URL or PGHOST environment variable not set.")
        return 1
    
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                # Check if column already exists
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'agents_registry' 
                    AND column_name = 'code'
                """)
                
                if cur.fetchone():
                    print("Column 'code' already exists. No migration needed.")
                    return 0
                
                print("Adding 'code' column to agents_registry table...")
                
                # Add code column (TEXT type for Python source code)
                cur.execute("""
                    ALTER TABLE agents_registry 
                    ADD COLUMN code TEXT
                """)
                
                # Update path column comment to indicate it's now a reference
                cur.execute("""
                    COMMENT ON COLUMN agents_registry.path IS 
                    'Reference path for local file (legacy). Agent code is now stored in the code column.'
                """)
                
                conn.commit()
                
                print("✓ Successfully added code storage column")
                print("\nNext steps:")
                print("  1. Existing agents need to be re-registered to upload their code")
                print("  2. Use Agent Builder GUI to register/re-register agents")
                print("  3. Code will be loaded from database during execution")
                
                return 0
                
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        return 1


if __name__ == "__main__":
    os.environ['MASSIVE_API_KEY'] = "Y2mALom8TLdet7Bc8ktLeQ4355hAdpG6"
    os.environ['NASDAQ_DATA_LINK_API_KEY'] = "s_phvq25xVMyCa6KBXFj"
    os.environ["DATABASE_URL"] = "postgresql://postgres:5369@localhost:5432/postgres"
    sys.exit(migrate())
