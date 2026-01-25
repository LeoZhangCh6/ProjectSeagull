import importlib.util
import os
import sys
from types import ModuleType
from typing import Any

from ib_backtester.engine import BaseAgent
from .db import get_pg_conn


def load_agents_registry_csv(path: str) -> dict:
    """
    CSV columns:
      name,path,description,enabled
    """
    import csv
    if not os.path.exists(path):
        raise FileNotFoundError(f"Agents registry not found: {path}")
    out = {}
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        required = {"name", "path"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns in agents registry: {missing}")
        for row in reader:
            if not any(((v or "").strip() for v in row.values())):
                continue
            name = (row.get("name") or "").strip()
            pathv = (row.get("path") or "").strip()
            enabled = (row.get("enabled") or "1").strip().lower() in {"1", "true", "t", "yes", "y"}
            if name and pathv and enabled:
                out[name] = pathv
    if not out:
        raise ValueError("Agents registry has no usable rows.")
    return out


def get_agent_factory_from_registry(agent_name: str, registry_path: str):
    reg = load_agents_registry_csv(registry_path)
    path = reg.get(agent_name)
    if path is None:
        raise KeyError(f"Agent '{agent_name}' not found in registry: {registry_path}")
    abspath = os.path.abspath(path if os.path.isabs(path) else os.path.join(os.path.dirname(registry_path), path))
    return lambda: load_agent_from_file(abspath)


def get_agent_factory_from_registry_db(agent_name: str):
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT path FROM agents_registry
                WHERE name = %s AND enabled = TRUE
                """,
                (agent_name,),
            )
            row = cur.fetchone()
            if not row:
                raise KeyError(f"Agent '{agent_name}' not found in agents_registry table.")
            path = row[0]
            abspath = os.path.abspath(path)
            return lambda: load_agent_from_file(abspath)


def _import_module_from_path(path: str) -> ModuleType:
    path = os.path.abspath(path)
    mod_name = os.path.splitext(os.path.basename(path))[0]
    # region agent log
    try:
        _dbg_log_path = r"c:\Users\Tianyi Zhang\Desktop\Project Highball\ProjectSeagull\.cursor\debug.log"
        # Heuristic project root: ../../.. from the agent file path (Agents/instances/<file>.py)
        _agents_instances_dir = os.path.dirname(path)
        _agents_dir = os.path.dirname(_agents_instances_dir)
        _project_root = os.path.dirname(_agents_dir)
        if _project_root not in sys.path:
            sys.path.insert(0, _project_root)
        _backtesting_dir = os.path.join(_project_root, "Backtesting")
        if _backtesting_dir not in sys.path:
            sys.path.insert(0, _backtesting_dir)
        with open(_dbg_log_path, "a", encoding="utf-8") as _f:
            import json, time
            _f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "pre-fix",
                "hypothesisId": "H2",
                "location": "Common/agents_loader.py:_import_module_from_path",
                "message": "Inserted project/backtesting dirs to sys.path for agent import",
                "data": {
                    "agent_path": path,
                    "project_root": _project_root,
                    "backtesting_dir": _backtesting_dir,
                    "sys_path_head": sys.path[:5],
                },
                "timestamp": int(time.time() * 1000)
            }) + "\n")
    except Exception:
        pass
    # endregion
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_agent_from_file(path: str) -> BaseAgent:
    """
    Loads a Python module and returns a BaseAgent instance.
    The module must expose either:
      - create_agent() -> BaseAgent
      - AGENT: BaseAgent
    """
    module = _import_module_from_path(path)
    if hasattr(module, "create_agent") and callable(getattr(module, "create_agent")):
        agent = module.create_agent()
        if not isinstance(agent, BaseAgent):
            raise TypeError("create_agent() must return a BaseAgent instance.")
        return agent
    if hasattr(module, "AGENT"):
        agent = getattr(module, "AGENT")
        if not isinstance(agent, BaseAgent):
            raise TypeError("AGENT must be a BaseAgent instance.")
        return agent
    raise AttributeError("Module must define 'create_agent()' or 'AGENT'.")

