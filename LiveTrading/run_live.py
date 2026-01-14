import os
from datetime import datetime

import pandas as pd

from Common.agents_registry import get_agent_factory
from Common.reporting import generate_test_report
from ib_backtester.types import Contract


def main():
    """
    Skeleton live runner:
    - Select agent via shared registry (BACKTEST_AGENT and env overrides).
    - In a real system, subscribe to live feeds and IBKR order APIs.
    - Here we just demonstrate report generation at the end of a (mock) session.
    """
    agent_factory = get_agent_factory()
    agent = agent_factory()

    # Mock session summary DataFrame (replace with actual PnL/equity log)
    results = pd.DataFrame([{
        "trial": 0,
        "symbol": os.environ.get("LIVE_SYMBOL", "AAPL"),
        "start_date": os.environ.get("LIVE_START_DATE", ""),
        "end_date": os.environ.get("LIVE_END_DATE", ""),
        "timespan": os.environ.get("LIVE_TIMESPAN", "minute"),
        "multiplier": int(os.environ.get("LIVE_MULTIPLIER", "1")),
        "final_equity": float(os.environ.get("LIVE_FINAL_EQUITY", "100000")),
        "total_return": float(os.environ.get("LIVE_TOTAL_RETURN", "0.0")),
        "max_drawdown": float(os.environ.get("LIVE_MAX_DRAWDOWN", "0.0")),
        "sharpe": float(os.environ.get("LIVE_SHARPE", "0.0")),
    }])

    plot_dir = os.environ.get("LIVE_REPORT_DIR", None)
    test_name = os.environ.get("LIVE_TEST_NAME", f"live_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    agent_name = type(agent).__name__
    agent_info = {"type": agent_name}

    # Write a unified report using the same generator as backtests
    generate_test_report(plot_dir, test_name, agent_name, agent_info, results_df=results, curves=None)
    if plot_dir:
        print(f"Live report written to: {plot_dir}")
    else:
        print("LIVE_REPORT_DIR not set; report not written.")


if __name__ == "__main__":
    main()

