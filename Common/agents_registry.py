import sys
import os

# Ensure Backtesting package (which contains `ib_backtester`) is importable regardless of CWD
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
_BACKTESTING_DIR = os.path.join(_PROJECT_ROOT, "Backtesting")
if _BACKTESTING_DIR not in sys.path:
    sys.path.insert(0, _BACKTESTING_DIR)

import os
from .agents_loader import load_agent_from_file

from ib_backtester.agents.sample_agent import SmaCrossAgent
from ib_backtester.agents.multisignal_agent import MultiSignalAgent, ExternalDataConfig
from ib_backtester.agents.multi_source_model_agent import MultiSourceModelAgent, MultiSourceConfig


def get_agent_factory():
    """
    Select an agent by BACKTEST_AGENT env var using a readable registry.
    Defaults to 'sma_cross'.
    """
    agent_py = os.environ.get("BACKTEST_AGENT_PY", "").strip()
    if agent_py:
        # Use a Python file that returns/provides a BaseAgent instance
        return lambda: load_agent_from_file(agent_py)

    agent_name = os.environ.get("BACKTEST_AGENT", "sma_cross").strip().lower()

    def make_sma_cross():
        fast = int(os.environ.get("SMA_FAST", "10"))
        slow = int(os.environ.get("SMA_SLOW", "20"))
        trade_size = int(os.environ.get("TRADE_SIZE", "10"))
        return lambda: SmaCrossAgent(fast=fast, slow=slow, trade_size=trade_size)

    def make_multi_signal():
        trade_size = int(os.environ.get("TRADE_SIZE", "10"))
        primary_fast = int(os.environ.get("PRIMARY_FAST", "10"))
        primary_slow = int(os.environ.get("PRIMARY_SLOW", "20"))
        peer_symbol = os.environ.get("PEER_SYMBOL", "SPY")
        peer_timespan = os.environ.get("PEER_TIMESPAN", "day")
        peer_multiplier = int(os.environ.get("PEER_MULTIPLIER", "1"))
        sf1_csv_path = os.environ.get("SF1_CSV_PATH", None)
        peer_mom_window = int(os.environ.get("PEER_MOM_WINDOW", "20"))
        ext = ExternalDataConfig(
            peer_symbol=peer_symbol,
            peer_timespan=peer_timespan,
            peer_multiplier=peer_multiplier,
            sf1_csv_path=sf1_csv_path,
        )
        return lambda: MultiSignalAgent(
            trade_size=trade_size,
            primary_fast=primary_fast,
            primary_slow=primary_slow,
            peer_momentum_window=peer_mom_window,
            external=ext,
        )

    def make_multi_source_model():
        trade_cap = int(os.environ.get("TRADE_CAP_PER_BAR", "10"))
        window_days = int(os.environ.get("WINDOW_DAYS", "14"))
        include_primary = os.environ.get("INCLUDE_PRIMARY_PRICE", "1") == "1"
        massive_specs = [s.strip() for s in os.environ.get("SOURCES_MASSIVE", "").split(";") if s.strip()]
        csv_paths = [s.strip() for s in os.environ.get("SOURCES_CSV", "").split(";") if s.strip()]
        sf1_specs = [s.strip() for s in os.environ.get("SOURCES_SF1", "").split(";") if s.strip()]
        cfg = MultiSourceConfig(
            window_days=window_days,
            include_primary_price=include_primary,
            trade_cap_per_bar=trade_cap,
            massive_specs=massive_specs if massive_specs else None,
            csv_paths=csv_paths if csv_paths else None,
            sf1_specs=sf1_specs if sf1_specs else None,
        )
        return lambda: MultiSourceModelAgent(config=cfg)

    AGENTS = {
        "sma_cross": make_sma_cross,
        "multi_signal": make_multi_signal,
        "multi_source_model": make_multi_source_model,
    }

    if agent_name not in AGENTS:
        raise ValueError(f"Unknown BACKTEST_AGENT '{agent_name}'. Available: {sorted(AGENTS.keys())}")
    return AGENTS[agent_name]()

