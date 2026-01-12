import os

import pandas as pd

from ib_backtester.suite import (
    BacktestSuite,
    load_allowlist_csv,
    load_test_types_csv,
)
from ib_backtester.agents.sample_agent import SmaCrossAgent


def main():
    
    # Config
    base_dir = os.path.dirname(__file__)
    allowlist_path = os.environ.get("BACKTEST_ALLOWLIST", os.path.join(base_dir, "config", "allowlist.csv"))
    tests_csv_path = os.environ.get("BACKTEST_TESTS_CSV", os.path.join(base_dir, "config", "test_types.csv"))
    select_names = os.environ.get("BACKTEST_TEST_NAMES", "")
    selected = {s.strip() for s in select_names.split(",") if s.strip()} if select_names else None

    allowlist = load_allowlist_csv(allowlist_path)
    test_types = load_test_types_csv(tests_csv_path)
    if selected is not None:
        test_types = [t for t in test_types if t.name in selected]
        if not test_types:
            raise ValueError(f"No matching test types found in '{tests_csv_path}' for names: {sorted(selected)}")

    all_results = []
    all_curves = {}

    for cfg in test_types:
        suite = BacktestSuite(
            allowlist=allowlist,
            agent_factory=lambda: SmaCrossAgent(fast=10, slow=20, trade_size=10),
            initial_cash=100000.0,
            commission_rate=0.0005,
            seed=cfg.seed,
        )

        results_df, curves = suite.run_within_overall_range(
            trials=cfg.trials,
            num_symbols=cfg.num_symbols,
            windows_per_symbol=cfg.windows_per_symbol,
            overall_start_date=cfg.overall_start_date,
            overall_end_date=cfg.overall_end_date,
            record_equity_curves=cfg.record_curves,
            plot_dir=cfg.plot_dir,
            warmup_days=cfg.warmup_days,
            trading_days=cfg.trading_days,
        )
        
        results_df = results_df.assign(test_name=cfg.name)
        print(f"Results for test '{cfg.name}':")
        print(results_df)

        all_results.append(results_df)
        if curves:
            all_curves.update({f"{cfg.name}_{k}": v for k, v in curves.items()})

    aggregate = pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()
    print("Aggregate results:")
    print(aggregate)

    out_csv = os.environ.get("BACKTEST_RESULTS_OUT", None)
    if out_csv:
        aggregate.to_csv(out_csv, index=False)
        print(f"Saved results to: {out_csv}")

if __name__ == "__main__":

    # Requires MASSIVE_API_KEY or POLYGON_API_KEY in environment
    os.environ['MASSIVE_API_KEY'] = "Y2mALom8TLdet7Bc8ktLeQ4355hAdpG6"
    main()
    
    
    
