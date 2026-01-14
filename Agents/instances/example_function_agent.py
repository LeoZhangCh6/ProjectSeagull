from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from Common.agent_api import SnapshotSpec, build_snapshot_tensor
from ib_backtester.engine import BaseAgent
from ib_backtester.types import Action, Order, OrderType


@dataclass
class Config:
    window_days: int = 14
    trade_cap_per_bar: int = 5
    include_primary_price: bool = True
    # Example sources
    massive_specs = ["SPY:day:1"]
    csv_paths = []
    sf1_specs = []


class ExampleFunctionAgent(BaseAgent):
    """
    Demonstrates an instance-only agent file that uses the API helpers.
    It builds a daily snapshot tensor and outputs an integer delta using a simple linear rule.
    """
    def __init__(self, cfg: Optional[Config] = None) -> None:
        self.cfg = cfg or Config()
        self._last_snapshot_day: Optional[pd.Timestamp] = None
        self._snapshot_tensor: Optional[np.ndarray] = None

    def _ensure_snapshot(self, history: pd.DataFrame) -> None:
        now = pd.to_datetime(history["time"].iloc[-1])
        day = now.normalize()
        if self._last_snapshot_day is not None and self._last_snapshot_day == day:
            return
        spec = SnapshotSpec(
            window_days=int(self.cfg.window_days),
            include_primary_price=bool(self.cfg.include_primary_price),
            massive_specs=self.cfg.massive_specs,
            csv_paths=self.cfg.csv_paths,
            sf1_specs=self.cfg.sf1_specs,
        )
        mat, _names, _index = build_snapshot_tensor(history, now, spec)
        self._snapshot_tensor = mat
        self._last_snapshot_day = day

    def on_start(self, ib, contract) -> None:
        pass

    def on_bar(self, ib, contract, history: pd.DataFrame) -> None:
        if history.empty:
            return
        self._ensure_snapshot(history)
        price = float(history["close"].astype(float).iloc[-1])
        state = ib.get_portfolio_state()
        # Simple linear rule on last row features if available
        qty = 0
        if self._snapshot_tensor is not None and self._snapshot_tensor.size > 0:
            last_feat = self._snapshot_tensor[-1]
            signal = float(np.nan_to_num(last_feat).sum())
            qty = int(np.clip(round(signal % (self.cfg.trade_cap_per_bar + 1)), -self.cfg.trade_cap_per_bar, self.cfg.trade_cap_per_bar))
        # Risk guardrails
        if qty > 0:
            max_afford = int(state["cash"] // max(price, 1e-9)) if price > 0 else 0
            qty = max(0, min(qty, max_afford))
        elif qty < 0:
            qty = -min(abs(qty), int(state["position"]))
        if qty == 0:
            return
        oid = ib.nextOrderId()
        if qty > 0:
            ib.placeOrder(oid, contract, Order(action=Action.BUY, totalQuantity=int(qty), orderType=OrderType.MKT))
        else:
            ib.placeOrder(oid, contract, Order(action=Action.SELL, totalQuantity=int(-qty), orderType=OrderType.MKT))

    def on_end(self, ib, contract) -> None:
        pass


def create_agent() -> BaseAgent:
    return ExampleFunctionAgent()

