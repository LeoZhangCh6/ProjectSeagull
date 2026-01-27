"""
Quick diagnostic script to check agents_registry table status.

Usage:
    python Common/check_agents_registry.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from Common.db import get_pg_conn


def main():
    print("="*60)
    print("Agents Registry Diagnostic")
    print("="*60)
    
    if not (os.environ.get("DATABASE_URL") or os.environ.get("PGHOST")):
        print("\n[X] ERROR: DATABASE_URL or PGHOST not set")
        print("Set database connection first.")
        return 1
    
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                # Check if table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'agents_registry'
                    )
                """)
                
                if not cur.fetchone()[0]:
                    print("\n[X] agents_registry table does not exist")
                    print("Run: python Scripts/init_db.py")
                    return 1
                
                # Check if code column exists
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'agents_registry' 
                    AND column_name = 'code'
                """)
                
                has_code_column = cur.fetchone() is not None
                
                # Get all agents
                cur.execute("""
                    SELECT 
                        name,
                        path,
                        CASE 
                            WHEN code IS NULL THEN 'No code'
                            WHEN LENGTH(code) = 0 THEN 'Empty code'
                            ELSE LENGTH(code) || ' chars'
                        END as code_status,
                        enabled,
                        description
                    FROM agents_registry
                    ORDER BY name
                """)
                
                agents = cur.fetchall()
                
                print(f"\n[OK] Database connected")
                print(f"[OK] agents_registry table exists")
                print(f"{'[OK]' if has_code_column else '[X]'} code column {'exists' if has_code_column else 'missing (run migration)'}")
                print(f"\nRegistered agents: {len(agents)}")
                print("-"*60)
                
                if not agents:
                    print("\n[!] No agents registered!")
                    print("\nAction required:")
                    print("  python Scripts/init_db.py")
                    return 1
                
                # Display agents
                print(f"\n{'Name':<30} {'Path':<25} {'Code Status':<15} {'Enabled'}")
                print("-"*90)
                
                for name, path, code_status, enabled, desc in agents:
                    enabled_str = "[OK]" if enabled else "[X]"
                    print(f"{name:<30} {path:<25} {code_status:<15} {enabled_str}")
                
                # Check test_jobs
                print("\n" + "="*60)
                print("Test Jobs")
                print("="*60)
                
                cur.execute("""
                    SELECT 
                        test_name,
                        agent_name,
                        CASE 
                            WHEN EXISTS (
                                SELECT 1 FROM agents_registry 
                                WHERE name = test_jobs.agent_name
                            ) THEN 'Found'
                            ELSE 'MISSING'
                        END as agent_status
                    FROM test_jobs
                    ORDER BY test_name, agent_name
                """)
                
                jobs = cur.fetchall()
                
                if not jobs:
                    print("\n[!] No test jobs defined")
                else:
                    print(f"\n{'Test Name':<20} {'Agent Name':<30} {'Status'}")
                    print("-"*60)
                    
                    issues = 0
                    for test_name, agent_name, agent_status in jobs:
                        status_str = "[OK]" if agent_status == 'Found' else "[X] MISSING"
                        print(f"{test_name:<20} {agent_name:<30} {status_str}")
                        if agent_status == 'MISSING':
                            issues += 1
                    
                    if issues > 0:
                        print(f"\n[!] {issues} job(s) reference missing agents!")
                        print("\nAction required:")
                        print("  python Scripts/init_db.py")
                        return 1
                
                print("\n" + "="*60)
                print("[OK] All checks passed!")
                print("="*60)
                return 0
                
    except Exception as e:
        print(f"\n[X] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    os.environ['DATABASE_URL'] = "postgresql://postgres:5369@localhost:5432/postgres"
    sys.exit(main())
