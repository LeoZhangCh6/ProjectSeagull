import os

from ib_backtester.suite import BacktestSuite, load_allowlist_csv
from ib_backtester.agents.sample_agent import SmaCrossAgent


def main():
    
    # Config
    base_dir = os.path.dirname(__file__)
    allowlist_path = os.environ.get("BACKTEST_ALLOWLIST", os.path.join(base_dir, "config", "allowlist.csv"))
    trials = int(os.environ.get("BACKTEST_TRIALS", "3"))
    num_symbols = int(os.environ.get("BACKTEST_NUM_SYMBOLS", "2"))
    windows_per_symbol = int(os.environ.get("BACKTEST_WINDOWS_PER_SYMBOL", "1"))
    seed = int(os.environ.get("BACKTEST_SEED", "42"))
    record_curves = os.environ.get("BACKTEST_RECORD_CURVES", "0") == "1"
    plot_dir = os.environ.get("BACKTEST_PLOT_DIR", None)
    warmup_days = int(os.environ.get("BACKTEST_WARMUP_DAYS", "14"))
    trading_days = int(os.environ.get("BACKTEST_TRADING_DAYS", "14"))

    allowlist = load_allowlist_csv(allowlist_path)
    suite = BacktestSuite(
        allowlist=allowlist,
        agent_factory=lambda: SmaCrossAgent(fast=10, slow=20, trade_size=10),
        initial_cash=100000.0,
        commission_rate=0.0005,
        seed=seed,
    )

    results_df, curves = suite.run(
        trials=trials,
        num_symbols=num_symbols,
        windows_per_symbol=windows_per_symbol,
        record_equity_curves=record_curves,
        plot_dir=plot_dir,
        warmup_days=warmup_days,
        trading_days=trading_days,
    )
    print("Aggregate results:")
    print(results_df)

    out_csv = os.environ.get("BACKTEST_RESULTS_OUT", None)
    if out_csv:
        results_df.to_csv(out_csv, index=False)
        print(f"Saved results to: {out_csv}")

if __name__ == "__main__":

    # Requires MASSIVE_API_KEY or POLYGON_API_KEY in environment
    os.environ['MASSIVE_API_KEY'] = "Y2mALom8TLdet7Bc8ktLeQ4355hAdpG6"
    os.environ['BACKTEST_PLOT_DIR'] = r"C:\Users\Tianyi Zhang\OneDrive\Desktop\delete me"
    main()

    
    
