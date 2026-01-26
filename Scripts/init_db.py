import os
import sys
import glob

import psycopg2


def register_all_agent_files(conn, root):
    """
    Scan Agents/instances/*.py and register all agents with their code in the database.
    """
    agents_dir = os.path.join(root, "Agents", "instances")
    
    if not os.path.exists(agents_dir):
        print(f"Warning: Agents directory not found: {agents_dir}")
        return 0
    
    # Find all .py files in Agents/instances/
    agent_files = glob.glob(os.path.join(agents_dir, "*.py"))
    
    if not agent_files:
        print(f"No agent files found in {agents_dir}")
        return 0
    
    print(f"\nRegistering {len(agent_files)} agent files from {agents_dir}...")
    registered_count = 0
    skipped_count = 0
    
    with conn.cursor() as cur:
        for filepath in agent_files:
            filename = os.path.basename(filepath)
            agent_name = os.path.splitext(filename)[0]
            
            # Skip __init__.py and other special files
            if filename.startswith('_'):
                print(f"  Skipping: {filename} (special file)")
                skipped_count += 1
                continue
            
            try:
                # Read agent code
                with open(filepath, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                # Create database path reference
                db_path = f"db://agents/{agent_name}"
                
                # Insert into database
                cur.execute(
                    """
                    INSERT INTO agents_registry (name, path, code, description, enabled)
                    VALUES (%s, %s, %s, %s, true)
                    ON CONFLICT (name) DO UPDATE
                    SET path = EXCLUDED.path,
                        code = EXCLUDED.code,
                        description = EXCLUDED.description,
                        enabled = EXCLUDED.enabled
                    """,
                    (agent_name, db_path, code, f"Auto-registered from {filename}")
                )
                
                print(f"  [OK] Registered: {agent_name} (db://agents/{agent_name})")
                registered_count += 1
                
            except Exception as e:
                print(f"  [X] Error registering {filename}: {e}")
                skipped_count += 1
    
    conn.commit()
    
    print(f"\nAgent registration complete:")
    print(f"  Registered: {registered_count}")
    print(f"  Skipped: {skipped_count}")
    
    return registered_count


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

    print("="*60)
    print("ProjectSeagull Database Initialization")
    print("="*60)
    print(f"\nConnecting to Postgres...")
    
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()
    
    with psycopg2.connect(dsn) as conn:
        # Step 1: Run SQL initialization
        print("Running SQL initialization script...")
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print("[OK] Database schema and default data created")
        
        # Step 2: Register all agent files
        register_all_agent_files(conn, root)
    
    print("\n" + "="*60)
    print("Database initialized successfully!")
    print("="*60)


if __name__ == "__main__":
    os.environ["DATABASE_URL"] = "postgresql://postgres:5369@localhost:5432/postgres"
    main()

