"""
Agent Loader - Load agents from PostgreSQL database

This module provides functionality to load agent code from the database
and execute it at runtime for backtesting and live trading.

The agent code is stored in the agents_registry table and is loaded
dynamically when needed, eliminating the need for file-based agent storage.
"""

import os
import sys
import tempfile
import importlib.util
from typing import Optional

from Common.db import get_pg_conn


def load_agent_from_db(agent_name: str):
    """
    Load an agent's Python code from the database and return the module.
    
    Args:
        agent_name: Name of the agent in agents_registry
    
    Returns:
        Module object containing the agent code
    
    Raises:
        ValueError: If agent not found or code is missing
        Exception: If code cannot be compiled or executed
    """
    # Get agent code from database
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT code, path FROM agents_registry WHERE name = %s AND enabled = true",
                (agent_name,)
            )
            result = cur.fetchone()
    
    if not result:
        raise ValueError(f"Agent '{agent_name}' not found in database or is disabled")
    
    code, path = result
    
    if not code:
        # Legacy fallback: try to load from file
        if path and not path.startswith('db://'):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(project_root, path)
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
            else:
                raise ValueError(
                    f"Agent '{agent_name}' has no code in database and file not found: {file_path}\n"
                    f"Please re-register this agent to upload code to database."
                )
        else:
            raise ValueError(
                f"Agent '{agent_name}' has no code in database.\n"
                f"Please re-register this agent to upload code."
            )
    
    # Create a temporary module to execute the code
    module_name = f"dynamic_agent_{agent_name}"
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    module = importlib.util.module_from_spec(spec)
    
    # Add module to sys.modules so imports work
    sys.modules[module_name] = module
    
    try:
        # Execute the code in the module's namespace
        exec(code, module.__dict__)
    except Exception as e:
        # Clean up on failure
        del sys.modules[module_name]
        raise Exception(f"Failed to execute agent '{agent_name}' code: {e}")
    
    return module


def load_agent_factory(agent_name: str):
    """
    Load an agent from database and return its create_agent() factory function.
    
    This is the main function used by the backtesting and live trading systems.
    
    Args:
        agent_name: Name of the agent in agents_registry
    
    Returns:
        The create_agent() function from the agent module
    
    Raises:
        ValueError: If agent not found or create_agent() not defined
        Exception: If code cannot be loaded or executed
    
    Example:
        >>> factory = load_agent_factory('my_agent')
        >>> agent_instance = factory()
        >>> # Now use agent_instance in backtesting/trading
    """
    module = load_agent_from_db(agent_name)
    
    if not hasattr(module, 'create_agent'):
        raise ValueError(
            f"Agent '{agent_name}' code does not define a create_agent() function.\n"
            f"Please ensure the agent follows the required structure."
        )
    
    return module.create_agent


def get_agent_code(agent_name: str) -> Optional[str]:
    """
    Get the raw Python code for an agent from the database.
    
    Args:
        agent_name: Name of the agent in agents_registry
    
    Returns:
        Python source code as string, or None if not found
    """
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT code FROM agents_registry WHERE name = %s",
                    (agent_name,)
                )
                result = cur.fetchone()
                return result[0] if result else None
    except Exception:
        return None


def update_agent_code(agent_name: str, code: str) -> bool:
    """
    Update an agent's code in the database.
    
    Args:
        agent_name: Name of the agent in agents_registry
        code: New Python source code
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE agents_registry SET code = %s WHERE name = %s",
                    (code, agent_name)
                )
            conn.commit()
        return True
    except Exception as e:
        print(f"Error updating agent code: {e}")
        return False


def list_available_agents():
    """
    List all enabled agents in the database.
    
    Returns:
        List of tuples: (name, path, has_code)
    """
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT name, path, (code IS NOT NULL) as has_code
                    FROM agents_registry
                    WHERE enabled = true
                    ORDER BY name
                """)
                return cur.fetchall()
    except Exception:
        return []
