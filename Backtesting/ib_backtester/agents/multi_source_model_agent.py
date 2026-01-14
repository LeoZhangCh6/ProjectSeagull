import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from ..engine import BaseAgent
from ..massive_client import get_aggregate_bars
from ..types import Action, Contract, Order, OrderType
from ..sharadar_client import get_sf1_series


@dataclass
class MultiSourceConfig:
    window_days: int = 14
    include_primary_price: bool = True
    trade_cap_per_bar: int = 10
    massive_specs: Optional[List[str]] = None  # e.g., ["SPY:day:1", "QQQ:day:1"]
    csv_paths: Optional[List[str]] = None      # list of CSVs with columns: date,value
    sf1_specs: Optional[List[str]] = None      # e.g., ["AAPL:ARQ:revenue","AAPL:MRQ:assets"]


class MultiSourceModelAgent(BaseAgent):
    """
    Agent that aggregates an arbitrary number of signals at different frequencies.
    At the start of each day it:
      - collects the last N days of data (default 14) from configured sources,
      - synchronizes via linear interpolation to the primary history index,
      - packages a 2D tensor [time, features] and flattens for a simple linear model,
      - combines with current portfolio state to produce an integer share delta.
    """

    def __init__(self, config: Optional[MultiSourceConfig] = None) -> None:
        self.config = config or MultiSourceConfig()
        self._last_snapshot_date: Optional[pd.Timestamp] = None
        self._snapshot_tensor: Optional[np.ndarray] = None
        self._feature_names: List[str] = []
        self._weights: Optional[np.ndarray] = None
        self._bias: float = 0.0
        # Seed from testbench if provided (TESTBENCH_RANDOM_SEED); otherwise random
        _seed_env = os.environ.get("TESTBENCH_RANDOM_SEED", "").strip()
        if _seed_env != "":
            try:
                self._rng = np.random.default_rng(int(_seed_env))
            except Exception:
                self._rng = np.random.default_rng()
        else:
            self._rng = np.random.default_rng()

    def _parse_massive_specs(self) -> List[Tuple[str, str, int]]:
        specs = self.config.massive_specs or []
        parsed: List[Tuple[str, str, int]] = []
        for raw in specs:
            parts = [p.strip() for p in str(raw).split(":")]
            if len(parts) == 0 or parts[0] == "":
                continue
            symbol = parts[0]
            timespan = parts[1] if len(parts) > 1 and parts[1] else "day"
            try:
                multiplier = int(parts[2]) if len(parts) > 2 and parts[2] else 1
            except Exception:
                multiplier = 1
            parsed.append((symbol, timespan, multiplier))
        return parsed

    def _parse_sf1_specs(self) -> List[Tuple[str, str, str]]:
        specs = self.config.sf1_specs or []
        parsed: List[Tuple[str, str, str]] = []
        for raw in specs:
            parts = [p.strip() for p in str(raw).split(":")]
            if len(parts) < 3:
                # Expect TICKER:DIMENSION:COLUMN
                continue
            symbol, dimension, column = parts[0], parts[1], parts[2]
            if not symbol or not dimension or not column:
                continue
            parsed.append((symbol, dimension, column))
        return parsed

    def _load_massive_series(self, start_dt: pd.Timestamp, end_dt: pd.Timestamp) -> List[pd.Series]:
        series_list: List[pd.Series] = []
        for symbol, timespan, multiplier in self._parse_massive_specs():
            df = get_aggregate_bars(
                symbol=symbol,
                start_date=start_dt.strftime("%Y-%m-%d"),
                end_date=end_dt.strftime("%Y-%m-%d"),
                timespan=timespan,
                multiplier=int(multiplier),
            )
            if df is None or df.empty:
                continue
            s = pd.Series(df["close"].astype(float).values, index=pd.DatetimeIndex(pd.to_datetime(df["time"])))
            s.name = f"massive:{symbol}:{timespan}x{multiplier}"
            series_list.append(s)
        return series_list

    def _load_sf1_series(self, start_dt: pd.Timestamp, end_dt: pd.Timestamp) -> List[pd.Series]:
        series_list: List[pd.Series] = []
        for symbol, dimension, column in self._parse_sf1_specs():
            s = get_sf1_series(
                symbol=symbol,
                column=column,
                dimension=dimension,
                start_date=start_dt.strftime("%Y-%m-%d"),
                end_date=end_dt.strftime("%Y-%m-%d"),
                api_key=None,
            )
            if s is None or s.empty:
                continue
            s = s.sort_index()
            series_list.append(s)
        return series_list

    def _load_csv_series(self, start_dt: pd.Timestamp, end_dt: pd.Timestamp) -> List[pd.Series]:
        series_list: List[pd.Series] = []
        for path in (self.config.csv_paths or []):
            if not path:
                continue
            if not os.path.exists(path):
                continue
            df = pd.read_csv(path)
            if "date" not in df.columns or "value" not in df.columns:
                continue
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"])
            df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)]
            df = df.sort_values("date")
            if df.empty:
                continue
            s = pd.Series(df["value"].astype(float).values, index=pd.DatetimeIndex(df["date"]))
            s.name = f"csv:{os.path.basename(path)}"
            series_list.append(s)
        return series_list

    def _build_snapshot_tensor(self, history: pd.DataFrame, now_dt: pd.Timestamp) -> None:
        if history.empty or "time" not in history.columns:
            self._snapshot_tensor = None
            self._feature_names = []
            return
        window_days = int(self.config.window_days)
        start_dt = (now_dt.normalize() - pd.Timedelta(days=window_days))
        end_dt = now_dt

        base = history.copy()
        base["time"] = pd.to_datetime(base["time"])
        base = base[(base["time"] >= start_dt) & (base["time"] <= end_dt)]
        if base.empty:
            self._snapshot_tensor = None
            self._feature_names = []
            return
        base_index = pd.DatetimeIndex(base["time"])

        features: List[pd.Series] = []
        names: List[str] = []

        if self.config.include_primary_price and "close" in base.columns:
            s = pd.Series(base["close"].astype(float).values, index=base_index)
            s.name = "primary:close"
            features.append(s)
            names.append(s.name)

        for s in self._load_massive_series(start_dt, end_dt):
            s = s.sort_index().reindex(base_index, method=None)
            s = s.interpolate(method="time", limit_direction="both")
            features.append(s)
            names.append(s.name)

        for s in self._load_sf1_series(start_dt, end_dt):
            s = s.sort_index().reindex(base_index, method=None)
            s = s.interpolate(method="time", limit_direction="both")
            features.append(s)
            names.append(s.name)

        for s in self._load_csv_series(start_dt, end_dt):
            s = s.sort_index().reindex(base_index, method=None)
            s = s.interpolate(method="time", limit_direction="both")
            features.append(s)
            names.append(s.name)

        if not features:
            self._snapshot_tensor = None
            self._feature_names = []
            return

        mat = np.column_stack([f.astype(float).values for f in features])
        self._snapshot_tensor = mat
        self._feature_names = names

        # Initialize or resize linear model weights to match flattened length
        flat_dim = self._snapshot_tensor.size
        if self._weights is None or self._weights.shape[0] != (flat_dim + 1 + 4):
            # +1 for current price, +4 for [cash, position, avg_cost, equity]
            self._weights = self._rng.normal(loc=0.0, scale=0.01, size=flat_dim + 1 + 4)
            self._bias = float(self._rng.normal(loc=0.0, scale=0.01))

    def _ensure_daily_snapshot(self, history: pd.DataFrame) -> None:
        now_dt = pd.to_datetime(history["time"].iloc[-1])
        current_day = now_dt.normalize()
        if self._last_snapshot_date is None or current_day != self._last_snapshot_date:
            self._build_snapshot_tensor(history, now_dt)
            self._last_snapshot_date = current_day

    def _predict_shares_delta(self, price_now: float, state: dict) -> int:
        if self._snapshot_tensor is None or self._weights is None:
            return 0
        flat = self._snapshot_tensor.reshape(-1).astype(float)
        state_vec = np.array([
            float(state.get("cash", 0.0)),
            float(state.get("position", 0.0)),
            float(state.get("avg_cost", 0.0)),
            float(state.get("equity", 0.0)),
        ], dtype=float)
        x = np.concatenate([flat, np.array([price_now], dtype=float), state_vec])
        raw = float(np.dot(self._weights, x) + self._bias)
        qty = int(np.clip(np.rint(raw), -self.config.trade_cap_per_bar, self.config.trade_cap_per_bar))
        # Risk control: cap by affordability/position
        max_afford = int(state.get("cash", 0.0) // max(price_now, 1e-9)) if price_now > 0 else 0
        if qty > 0:
            qty = max(0, min(qty, max_afford))
        elif qty < 0:
            qty = -min(abs(qty), int(state.get("position", 0)))
        return qty

    def on_start(self, ib, contract: Contract) -> None:
        self._last_snapshot_date = None
        self._snapshot_tensor = None

    def on_bar(self, ib, contract: Contract, history: pd.DataFrame) -> None:
        if history.empty:
            return
        self._ensure_daily_snapshot(history)

        state = ib.get_portfolio_state()
        price_now = float(history["close"].astype(float).iloc[-1])
        qty = self._predict_shares_delta(price_now, state)
        if qty == 0:
            return
        if qty > 0:
            oid = ib.nextOrderId()
            ib.placeOrder(oid, contract, Order(action=Action.BUY, totalQuantity=int(qty), orderType=OrderType.MKT))
        else:
            oid = ib.nextOrderId()
            ib.placeOrder(oid, contract, Order(action=Action.SELL, totalQuantity=int(-qty), orderType=OrderType.MKT))

    def on_end(self, ib, contract: Contract) -> None:
        pass

