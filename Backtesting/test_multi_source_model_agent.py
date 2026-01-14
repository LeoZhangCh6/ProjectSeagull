import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from ib_backtester.engine import IBBacktestEnv
from ib_backtester.agents.multi_source_model_agent import MultiSourceModelAgent, MultiSourceConfig


def _make_synthetic_primary(symbol: str = "TEST", start_date: str = "2023-01-01", days: int = 30) -> pd.DataFrame:
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    rows = []
    price = 100.0
    rng = np.random.default_rng(123)
    for i in range(days):
        dt = start_dt + timedelta(days=i)
        ts_ms = int(pd.Timestamp(dt).timestamp() * 1000)
        # Random walk daily bar
        ret = rng.normal(0, 0.005)
        open_px = price
        close_px = price * (1.0 + ret)
        high_px = max(open_px, close_px) * (1.0 + abs(rng.normal(0, 0.002)))
        low_px = min(open_px, close_px) * (1.0 - abs(rng.normal(0, 0.002)))
        vol = int(1e6 * (1.0 + rng.normal(0, 0.1)))
        rows.append({
            "symbol": symbol,
            "timestamp": ts_ms,
            "time": pd.Timestamp(dt),
            "timespan": "day",
            "open": float(open_px),
            "high": float(high_px),
            "low": float(low_px),
            "close": float(close_px),
            "volume": int(max(vol, 0)),
            "vwap": float((open_px + close_px) / 2.0),
            "transactions": int(1000 + rng.integers(0, 100)),
            "otc": False,
        })
        price = close_px
    return pd.DataFrame(rows)


def run_smoke_test():
    # Build synthetic primary data to avoid external API dependency
    df = _make_synthetic_primary(symbol="TEST", start_date="2023-01-01", days=30)
    env = IBBacktestEnv(
        data=df,
        initial_cash=100000.0,
        commission_rate=0.0005,
    )

    # Prepare CSV sources (relative paths)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    econ_csv = os.path.join(base_dir, "data", "test_econ1.csv")
    sf1_csv = os.path.join(base_dir, "data", "test_sf1_metric.csv")

    cfg = MultiSourceConfig(
        window_days=14,
        include_primary_price=True,
        trade_cap_per_bar=5,
        random_seed=42,
        massive_specs=None,  # keep None to avoid live API during test
        csv_paths=[econ_csv, sf1_csv],
        sf1_specs=None,
    )
    agent = MultiSourceModelAgent(config=cfg)

    # Use a short warmup and trading period inside the available data
    curve = env.run(agent, warmup_days=7, trading_days=7)
    print("Smoke test completed.")
    print(f"Bars processed: {len(curve)}")
    if not curve.empty:
        print(f"Final equity: {float(curve['equity'].iloc[-1]):.2f}")

    # Basic assertions for a working test
    assert isinstance(curve, pd.DataFrame)
    assert len(curve) > 0
    assert "equity" in curve.columns


if __name__ == "__main__":
    run_smoke_test()

