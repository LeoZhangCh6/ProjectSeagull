"""Job manager for concurrent simulation execution."""

from typing import Dict, Any

# Global storage for simulation sessions
simulation_sessions: Dict[str, Dict[str, Any]] = {}
