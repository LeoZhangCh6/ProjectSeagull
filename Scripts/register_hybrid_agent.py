"""
Quick setup script to register the hybrid encoder-decoder agent.

Adds the agent to the agents_registry table so it can be used in backtests.

Usage:
    python Scripts/register_hybrid_agent.py
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
    print("Register Hybrid Encoder-Decoder Agent")
    print("="*60)
    
    if not (os.environ.get("DATABASE_URL") or os.environ.get("PGHOST")):
        print("ERROR: DATABASE_URL or PGHOST not set")
        return 1
    
    agent_name = "hybrid_encoder_decoder"
    agent_path = "Agents/instances/hybrid_encoder_decoder_agent.py"
    description = "Hybrid agent with encoder-decoder architecture and decision logging"
    
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO agents_registry (name, path, description, enabled)
                    VALUES (%s, %s, %s, true)
                    ON CONFLICT (name) DO UPDATE
                    SET path = EXCLUDED.path,
                        description = EXCLUDED.description,
                        enabled = EXCLUDED.enabled
                    """,
                    (agent_name, agent_path, description)
                )
            conn.commit()
        
        print(f"\n✓ Successfully registered agent: {agent_name}")
        print(f"  Path: {agent_path}")
        print(f"  Description: {description}")
        print("\nNext steps:")
        print("  1. Create test definition in GUI (Test Definitions tab)")
        print("  2. Assign agent to test in GUI (Jobs tab)")
        print("  3. Run: set BACKTEST_TEST_NAMES=your_test && python Backtesting/run_suite.py")
        print("  4. Visualize: python Scripts/visualize_agent.py logs/hybrid_agent_decisions.json")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    os.environ['MASSIVE_API_KEY'] = "Y2mALom8TLdet7Bc8ktLeQ4355hAdpG6"
    os.environ['NASDAQ_DATA_LINK_API_KEY'] = "s_phvq25xVMyCa6KBXFj"
    os.environ["DATABASE_URL"] = "postgresql://postgres:5369@localhost:5432/postgres"
    sys.exit(main())
