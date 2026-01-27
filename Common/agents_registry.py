"""
Legacy agents_registry module.

Agent loading is now handled via:
  - get_agent_factory_from_registry_db() in agents_loader.py (loads from DB)
  - get_agent_factory_from_registry() in agents_loader.py (loads from CSV)

All agents should be stored in Agents/instances/ and registered in the database.
"""
import sys
import os

# Ensure Backtesting package (which contains `ib_backtester`) is importable regardless of CWD
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
_BACKTESTING_DIR = os.path.join(_PROJECT_ROOT, "Backtesting")
if _BACKTESTING_DIR not in sys.path:
    sys.path.insert(0, _BACKTESTING_DIR)

from .agents_loader import load_agent_from_file, get_agent_factory_from_registry_db


def get_agent_factory(agent_name: str = None):
    """
    Get agent factory by name from the database registry.
    
    Args:
        agent_name: Name of agent in agents_registry table.
                    If None, uses BACKTEST_AGENT_PY env var for file path fallback.
    
    Returns:
        Callable that creates a BaseAgent instance.
    """
    # Legacy: support loading from file path via env var
    agent_py = os.environ.get("BACKTEST_AGENT_PY", "").strip()
    if agent_py:
        return lambda: load_agent_from_file(agent_py)
    
    if agent_name is None:
        raise ValueError("agent_name is required (or set BACKTEST_AGENT_PY env var)")
    
    return get_agent_factory_from_registry_db(agent_name)

