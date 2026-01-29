#!/usr/bin/env python3
"""Migration: Add visual_agent_designs table for the Visual Agent Designer feature."""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load .env file from backend folder
from dotenv import load_dotenv
env_path = os.path.join(project_root, "backend", ".env")
load_dotenv(env_path)

from Common.db import get_pg_conn


def migrate():
    """Create the visual_agent_designs table."""
    
    sql = """
    -- Visual Agent Designs table for storing node-based agent diagrams
    CREATE TABLE IF NOT EXISTS visual_agent_designs (
        id              SERIAL PRIMARY KEY,
        name            TEXT NOT NULL UNIQUE,
        description     TEXT,
        -- The ReactFlow graph data (nodes, edges, viewport)
        graph_json      JSONB NOT NULL DEFAULT '{"nodes": [], "edges": [], "viewport": {"x": 0, "y": 0, "zoom": 1}}',
        -- Agent configuration
        symbol          TEXT NOT NULL DEFAULT 'AAPL',
        primary_timespan TEXT NOT NULL DEFAULT 'day',
        primary_multiplier INTEGER NOT NULL DEFAULT 1,
        -- Generated Python code (cached)
        generated_code  TEXT,
        -- Link to registered agent (if deployed)
        agent_name      TEXT REFERENCES agents_registry(name) ON DELETE SET NULL,
        -- Timestamps
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    
    -- Index for quick lookups
    CREATE INDEX IF NOT EXISTS idx_visual_agent_designs_name ON visual_agent_designs(name);
    CREATE INDEX IF NOT EXISTS idx_visual_agent_designs_agent ON visual_agent_designs(agent_name);
    
    -- Trigger to auto-update updated_at
    CREATE OR REPLACE FUNCTION update_visual_design_timestamp()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    
    DROP TRIGGER IF EXISTS visual_design_updated ON visual_agent_designs;
    CREATE TRIGGER visual_design_updated
        BEFORE UPDATE ON visual_agent_designs
        FOR EACH ROW
        EXECUTE FUNCTION update_visual_design_timestamp();
    """
    
    print("Creating visual_agent_designs table...")
    
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    
    print("Migration complete!")


if __name__ == "__main__":
    migrate()
