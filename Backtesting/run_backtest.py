import os

from ib_backtester.engine import IBBacktestEnv
from ib_backtester.agents.sample_agent import SmaCrossAgent
from ib_backtester.plotting import plot_candles_with_trades


def main():
    symbol = os.environ.get("BACKTEST_SYMBOL", "AAPL")
    start_date = os.environ.get("BACKTEST_START", "2023-01-01")
    end_date = os.environ.get("BACKTEST_END", "2023-03-31")
    timespan = os.environ.get("BACKTEST_TIMESPAN", "minute")
    multiplier = int(os.environ.get("BACKTEST_MULTIPLIER", "5"))
    warmup_days = int(os.environ.get("BACKTEST_WARMUP_DAYS", "14"))
    trading_days = int(os.environ.get("BACKTEST_TRADING_DAYS", "14"))

    env = IBBacktestEnv(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        timespan=timespan,
        multiplier=multiplier,
        initial_cash=100000.0,
        commission_rate=0.0005,
    )

    agent = SmaCrossAgent(fast=10, slow=20, trade_size=10)
    equity_curve = env.run(agent, warmup_days=warmup_days, trading_days=trading_days)

    print("Summary:")
    print(f"  Final cash: {env.broker.cash:,.2f}")
    if not equity_curve.empty:
        print(f"  Final equity: {equity_curve['equity'].iloc[-1]:,.2f}")
        print(f"  Bars processed: {len(equity_curve)}")

    out_path = os.environ.get("BACKTEST_OUTPUT", None)
    if out_path:
        equity_curve.to_csv(out_path, index=False)
        print(f"Saved equity curve to: {out_path}")

    # Optional plotting
    plot_out = os.environ.get("BACKTEST_PLOT_OUT", None)
    if plot_out:
        plot_start_dt = str(env.data.loc[0, "time"]) if not env.data.empty else start_date
        plot_end_dt = ""
        if getattr(env, "trading_end_timestamp", None) is not None:
            import pandas as pd
            plot_end_dt = pd.to_datetime(env.trading_end_timestamp, unit="ms").strftime("%Y-%m-%d %H:%M")
        else:
            plot_end_dt = end_date
        title = f"{symbol} {plot_start_dt} to {plot_end_dt} (warmup {warmup_days}d, trade {trading_days}d) ({timespan} x{multiplier})"
        plot_candles_with_trades(
            env.data,
            env.broker.trades,
            title=title,
            save_path=plot_out,
            show=False,
            trading_start_timestamp=env.trading_start_timestamp,
            trading_end_timestamp=env.trading_end_timestamp,
            equity_curve=equity_curve,
        )
        print(f"Saved plot to: {plot_out}")


if __name__ == "__main__":
    # Requires MASSIVE_API_KEY or POLYGON_API_KEY in environment

    os.environ['MASSIVE_API_KEY'] = "Y2mALom8TLdet7Bc8ktLeQ4355hAdpG6"
    main()


