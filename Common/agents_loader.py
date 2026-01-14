import importlib.util
import os
from types import ModuleType
from typing import Any

from ib_backtester.engine import BaseAgent


def _import_module_from_path(path: str) -> ModuleType:
    path = os.path.abspath(path)
    mod_name = os.path.splitext(os.path.basename(path))[0]
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

