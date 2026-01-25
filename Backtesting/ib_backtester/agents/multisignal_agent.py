import os
from dataclasses import dataclass
from typing import Optional, Tuple

import pandas as pd

from ..engine import BaseAgent
from Common.massive_client import get_aggregate_bars
from ..types import Action, Contract, Order, OrderType


@dataclass
class ExternalDataConfig:
    """
    Configuration for external data sources used by MultiSignalAgent.

    - peer_symbol: secondary market index or related ETF (e.g., 'SPY')
    - peer_timespan / peer_multiplier: bar size for peer data
    - sf1_csv_path: path to a CSV containing daily SF1-like values for a given ticker.
      Expected columns: ['date','value'] where date is YYYY-MM-DD. You can pre-join
      or engineer any SF1 metric and save it to this simple shape.
    """
    peer_symbol: Optional[str] = "SPY"
    peer_timespan: str = "day"
    peer_multiplier: int = 1
    sf1_csv_path: Optional[str] = None


class MultiSignalAgent(BaseAgent):
    """
    Example multi-signal agent.

    Signals combined:
    1) Primary SMA crossover on the backtested instrument (from env history)
    2) Peer momentum filter from a secondary symbol (e.g., SPY) fetched via Massive/Polygon
    3) SF1 daily feature tilt loaded from a local CSV (date,value) providing fundamental bias

    Trade logic:
    - Enter long when primary signal is bullish AND peer momentum >= 0 AND sf1 tilt >= 0
    - Exit when primary signal turns bearish OR peer momentum < 0 OR sf1 tilt << 0
    """

    def __init__(
        self,
        trade_size: int = 10,
        primary_fast: int = 10,
        primary_slow: int = 20,
        peer_momentum_window: int = 20,
        external: Optional[ExternalDataConfig] = None,
    ) -> None:
        self.trade_size = int(trade_size)
        self.primary_fast = int(primary_fast)
        self.primary_slow = int(primary_slow)
        self.peer_momentum_window = int(peer_momentum_window)
        self.external = external or ExternalDataConfig()
        self.in_position: bool = False

        # Lazy-loaded state
        self._peer_series: Optional[pd.DataFrame] = None  # columns: ['time','close']
        self._sf1_series: Optional[pd.Series] = None      # index: datetime, values: float
        self._loaded_for_range: Optional[Tuple[pd.Timestamp, pd.Timestamp]] = None

    def _maybe_load_external_series(self, history: pd.DataFrame) -> None:
        """
        Lazily fetch peer bars and load SF1 series aligned to the history time window.
        """
        if history.empty or "time" not in history.columns:
            return
        start_dt = pd.to_datetime(history["time"].iloc[0]).normalize()
        end_dt = pd.to_datetime(history["time"].iloc[-1]).normalize()
        req = (start_dt, end_dt)
        if self._loaded_for_range == req:
            return

        # Load peer symbol bars if configured
        if self.external.peer_symbol:
            df = get_aggregate_bars(
                symbol=self.external.peer_symbol,
                start_date=start_dt.strftime("%Y-%m-%d"),
                end_date=end_dt.strftime("%Y-%m-%d"),
                timespan=self.external.peer_timespan,
                multiplier=int(self.external.peer_multiplier),
            )
            if df is not None and not df.empty:
                self._peer_series = df[["time", "close"]].copy()
            else:
                self._peer_series = None

        # Load SF1-like daily series from CSV if provided
        if self.external.sf1_csv_path:
            if os.path.exists(self.external.sf1_csv_path):
                sf1 = pd.read_csv(self.external.sf1_csv_path)
                # Expect columns: date,value
                if "date" in sf1.columns and "value" in sf1.columns:
                    sf1 = sf1.copy()
                    sf1["date"] = pd.to_datetime(sf1["date"])
                    sf1 = sf1[(sf1["date"] >= start_dt) & (sf1["date"] <= end_dt)]
                    sf1 = sf1.sort_values("date")
                    self._sf1_series = pd.Series(sf1["value"].astype(float).values, index=sf1["date"])
                else:
                    self._sf1_series = None
            else:
                self._sf1_series = None

        self._loaded_for_range = req

    def _primary_signal(self, history: pd.DataFrame) -> Optional[int]:
        closes = history["close"].astype(float)
        if len(closes) < max(self.primary_fast, self.primary_slow) + 1:
            return None
        fast = closes.rolling(self.primary_fast).mean()
        slow = closes.rolling(self.primary_slow).mean()
        prev_fast, prev_slow = fast.iloc[-2], slow.iloc[-2]
        curr_fast, curr_slow = fast.iloc[-1], slow.iloc[-1]
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            return +1
        if prev_fast >= prev_slow and curr_fast < curr_slow:
            return -1
        return 0

    def _peer_momentum(self, current_time: pd.Timestamp) -> Optional[float]:
        if self._peer_series is None or self._peer_series.empty:
            return None
        series = self._peer_series.copy()
        series.index = pd.DatetimeIndex(pd.to_datetime(series["time"]))
        series = series.sort_index()
        # Nearest available value <= current_time
        if current_time < series.index[0]:
            return None
        close_now = float(series.loc[:current_time]["close"].iloc[-1])
        past_idx = series.index.get_indexer([current_time - pd.Timedelta(days=self.peer_momentum_window)], method="nearest")[0]
        close_past = float(series["close"].iloc[past_idx])
        if close_past == 0:
            return 0.0
        return (close_now / close_past) - 1.0

    def _sf1_tilt(self, current_time: pd.Timestamp) -> Optional[float]:
        if self._sf1_series is None or self._sf1_series.empty:
            return None
        s = self._sf1_series.sort_index()
        # Hold-last (pad) daily value up to current_time
        s = s.loc[:current_time] if current_time >= s.index[0] else s.iloc[:0]
        if s.empty:
            return None
        # Normalize to z-score over the observed window for a smooth [-, +] tilt
        window = s.iloc[-90:] if len(s) > 90 else s
        val = float(s.iloc[-1])
        mu = float(window.mean())
        std = float(window.std()) if window.std() and not pd.isna(window.std()) else 0.0
        if std == 0.0:
            return 0.0
        z = (val - mu) / std
        # Clamp extreme z to avoid dominating the decision
        return max(min(z, 2.5), -2.5)

    def on_start(self, ib, contract: Contract) -> None:
        self.in_position = False

    def on_bar(self, ib, contract: Contract, history: pd.DataFrame) -> None:
        # Ensure external series are available for the current history window
        self._maybe_load_external_series(history)

        # Compute signals
        primary = self._primary_signal(history)
        current_time = pd.to_datetime(history["time"].iloc[-1])
        peer_mom = self._peer_momentum(current_time)
        sf1_tilt = self._sf1_tilt(current_time)

        # Combine (simple rule-based example)
        # - Long entry: primary bullish AND (peer momentum >= 0 or missing) AND (sf1_tilt >= 0 or missing)
        # - Exit: primary bearish OR (peer momentum < 0) OR (sf1_tilt < -0.5)
        if primary is None:
            return

        enter_long = (primary == +1) and (peer_mom is None or peer_mom >= 0.0) and (sf1_tilt is None or sf1_tilt >= 0.0)
        exit_long = (primary == -1) or (peer_mom is not None and peer_mom < 0.0) or (sf1_tilt is not None and sf1_tilt < -0.5)

        if enter_long and not self.in_position:
            oid = ib.nextOrderId()
            order = Order(action=Action.BUY, totalQuantity=self.trade_size, orderType=OrderType.MKT)
            ib.placeOrder(oid, contract, order)
            self.in_position = True
        elif exit_long and self.in_position:
            oid = ib.nextOrderId()
            order = Order(action=Action.SELL, totalQuantity=self.trade_size, orderType=OrderType.MKT)
            ib.placeOrder(oid, contract, order)
            self.in_position = False

    def on_end(self, ib, contract: Contract) -> None:
        pass

