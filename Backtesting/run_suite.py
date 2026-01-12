import os

import pandas as pd

from ib_backtester.suite import (
    BacktestSuite,
    load_allowlist_csv,
    load_test_types_csv,
)
from ib_backtester.agents.sample_agent import SmaCrossAgent
from ib_backtester.agents.multisignal_agent import MultiSignalAgent, ExternalDataConfig


def _get_agent_factory() -> callable:
    """
    Selects an agent by BACKTEST_AGENT env var using a readable registry.
    Defaults to 'sma_cross'.

    Env overrides for 'sma_cross':
      SMA_FAST, SMA_SLOW, TRADE_SIZE

    Env overrides for 'multi_signal':
      TRADE_SIZE, PRIMARY_FAST, PRIMARY_SLOW, PEER_SYMBOL, PEER_TIMESPAN, PEER_MULTIPLIER, SF1_CSV_PATH, PEER_MOM_WINDOW
    """
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

    AGENTS = {
        "sma_cross": make_sma_cross,
        "multi_signal": make_multi_signal,
    }

    if agent_name not in AGENTS:
        raise ValueError(f"Unknown BACKTEST_AGENT '{agent_name}'. Available: {sorted(AGENTS.keys())}")
    return AGENTS[agent_name]()


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
        agent_factory = _get_agent_factory()
        suite = BacktestSuite(
            allowlist=allowlist,
            agent_factory=agent_factory,
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
    
    
    
