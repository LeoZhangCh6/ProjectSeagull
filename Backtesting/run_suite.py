import os
import sys

# region agent log
try:
    _dbg_log_path = r"c:\Users\Tianyi Zhang\Desktop\Project Highball\ProjectSeagull\.cursor\debug.log"
    _here = os.path.dirname(os.path.abspath(__file__))
    _project_root = os.path.dirname(_here)
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)
    with open(_dbg_log_path, "a", encoding="utf-8") as _f:
        import json, time
        _f.write(json.dumps({
            "sessionId": "debug-session",
            "runId": "pre-fix",
            "hypothesisId": "H1",
            "location": "Backtesting/run_suite.py:bootstrap",
            "message": "Bootstrap sys.path and Common visibility",
            "data": {
                "cwd": os.getcwd(),
                "here": _here,
                "project_root": _project_root,
                "common_exists": os.path.isdir(os.path.join(_project_root, "Common")),
                "sys_path_head": sys.path[:5],
            },
            "timestamp": int(time.time() * 1000)
        }) + "\n")
except Exception:
    pass
# endregion

import pandas as pd

from ib_backtester.suite import (
    BacktestSuite,
    load_test_definitions_db,
)
from ib_backtester.agents.sample_agent import SmaCrossAgent
from ib_backtester.agents.multisignal_agent import MultiSignalAgent, ExternalDataConfig
from ib_backtester.agents.multi_source_model_agent import MultiSourceModelAgent, MultiSourceConfig
from Common.reporting import generate_test_report
from Common.agents_registry import get_agent_factory
from Common.agents_loader import get_agent_factory_from_registry


def main():
    
    # Config
    base_dir = os.path.dirname(__file__)
    
    select_names = os.environ.get("BACKTEST_TEST_NAMES", "")
    selected = {s.strip() for s in select_names.split(",") if s.strip()} if select_names else None

    # Always load test definitions from Postgres (optionally filtered by BACKTEST_TEST_NAMES)
    try:
        sel_list = sorted(selected) if selected else None
        test_types = load_test_definitions_db(sel_list)
        if selected and not test_types:
            raise ValueError(f"No matching test definitions found for names: {sel_list}")
    except Exception as e:
        raise RuntimeError("Failed to load test definitions from Postgres. Ensure DATABASE_URL or PG* env vars are set and the DB is initialized (Scripts/init_db.py).") from e

    all_results = []
    all_curves = {}

    # Optional: load agent instance overrides from JSON file and set env vars accordingly
    agent_config_path = os.environ.get("BACKTEST_AGENT_CONFIG", "").strip()
    if agent_config_path:
        try:
            import json
            with open(agent_config_path, "r", encoding="utf-8") as f:
                overrides = json.load(f)
            for k, v in overrides.items():
                os.environ[str(k)] = str(v)
        except Exception:
            pass

    for cfg in test_types:
        # Propagate testbench seed to agents (used for model RNG initialization)
        try:
            if cfg.seed is not None:
                os.environ["TESTBENCH_RANDOM_SEED"] = str(int(cfg.seed))
            else:
                if "TESTBENCH_RANDOM_SEED" in os.environ:
                    del os.environ["TESTBENCH_RANDOM_SEED"]
        except Exception:
            pass

        # Agent selection via env registry
        agent_factory = get_agent_factory()
        # Probe an instance to describe agent for the report
        agent_probe = agent_factory()
        agent_name = type(agent_probe).__name__
        agent_info = {}
        try:
            if isinstance(agent_probe, SmaCrossAgent):
                agent_info = {
                    "type": "SmaCrossAgent",
                    "params": {
                        "fast": getattr(agent_probe, "fast", None),
                        "slow": getattr(agent_probe, "slow", None),
                        "trade_size": getattr(agent_probe, "trade_size", None),
                    },
                    "signals": ["primary_close_SMA_fast", "primary_close_SMA_slow"],
                }
            elif isinstance(agent_probe, MultiSignalAgent):
                ext = getattr(agent_probe, "external", None)
                agent_info = {
                    "type": "MultiSignalAgent",
                    "params": {
                        "primary_fast": getattr(agent_probe, "primary_fast", None),
                        "primary_slow": getattr(agent_probe, "primary_slow", None),
                        "peer_momentum_window": getattr(agent_probe, "peer_momentum_window", None),
                        "trade_size": getattr(agent_probe, "trade_size", None),
                    },
                    "sources": {
                        "peer_symbol": getattr(ext, "peer_symbol", None) if ext else None,
                        "peer_timespan": getattr(ext, "peer_timespan", None) if ext else None,
                        "peer_multiplier": getattr(ext, "peer_multiplier", None) if ext else None,
                        "sf1_csv_path": getattr(ext, "sf1_csv_path", None) if ext else None,
                    },
                }
            elif isinstance(agent_probe, MultiSourceModelAgent):
                cfg_obj = getattr(agent_probe, "config", None)
                agent_info = {
                    "type": "MultiSourceModelAgent",
                    "config": {
                        "window_days": getattr(cfg_obj, "window_days", None) if cfg_obj else None,
                        "include_primary_price": getattr(cfg_obj, "include_primary_price", None) if cfg_obj else None,
                        "trade_cap_per_bar": getattr(cfg_obj, "trade_cap_per_bar", None) if cfg_obj else None,
                        "massive_specs": getattr(cfg_obj, "massive_specs", None) if cfg_obj else None,
                        "sf1_specs": getattr(cfg_obj, "sf1_specs", None) if cfg_obj else None,
                        "csv_paths": getattr(cfg_obj, "csv_paths", None) if cfg_obj else None,
                    },
                }

            # Include declared registry signals if present on any agent instance
            if hasattr(agent_probe, "used_signal_ids"):
                try:
                    agent_info["used_signal_ids"] = list(getattr(agent_probe, "used_signal_ids"))
                except Exception:
                    pass

        except Exception:
            agent_info = {"type": agent_name}

        # Resolve test scope per test (DB) or reuse CSV scope (non-DB)
        overall_start_for_run = cfg.overall_start_date
        overall_end_for_run = cfg.overall_end_date

        suite = BacktestSuite(
            agent_factory=agent_factory,
            initial_cash=100000.0,
            commission_rate=0.0005,
            seed=cfg.seed,
        )

        # Resolve single trading symbol and data freq from agent (fallback to env)
        symbol = getattr(agent_probe, "symbol", None)
        if symbol is None and hasattr(agent_probe, "get_symbol") and callable(getattr(agent_probe, "get_symbol")):
            try:
                symbol = agent_probe.get_symbol()
            except Exception:
                symbol = None
        if symbol is None:
            symbol = os.environ.get("BACKTEST_SYMBOL", None)
        if not symbol:
            raise ValueError("Agent must define a trading symbol (attribute 'symbol' or get_symbol()), or set BACKTEST_SYMBOL.")
        timespan = getattr(agent_probe, "primary_timespan", os.environ.get("BACKTEST_TIMESPAN", "minute"))
        multiplier = int(getattr(agent_probe, "primary_multiplier", int(os.environ.get("BACKTEST_MULTIPLIER", "1"))))

        # Determine windows_per_symbol from env (default 1)
        windows_per_symbol = int(os.environ.get("BACKTEST_WINDOWS_PER_SYMBOL", "1"))

        results_df, curves = suite.run_within_overall_range(
            trials=cfg.trials,
            symbol=str(symbol),
            timespan=str(timespan),
            multiplier=int(multiplier),
            windows_per_symbol=windows_per_symbol,
            overall_start_date=overall_start_for_run,
            overall_end_date=overall_end_for_run,
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

        # Write per-test markdown report next to plots (if plot_dir provided)
        try:
            report_path = generate_test_report(cfg.plot_dir, cfg.name, agent_name, agent_info, results_df, curves)
            if cfg.plot_dir:
                print(f"[{cfg.name}] Outputs saved to: {cfg.plot_dir}")
                if report_path:
                    print(f"[{cfg.name}] Test report: {report_path}")
        except Exception:
            pass

    aggregate = pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()
    print("Aggregate results:")
    print(aggregate)

    out_csv = os.environ.get("BACKTEST_RESULTS_OUT", None)
    if out_csv:
        aggregate.to_csv(out_csv, index=False)
        print(f"Saved results to: {out_csv}")
    else:
        print("Set BACKTEST_RESULTS_OUT to save the aggregate results CSV.")

if __name__ == "__main__":

    # Requires MASSIVE_API_KEY or POLYGON_API_KEY in environment
    os.environ['MASSIVE_API_KEY'] = "Y2mALom8TLdet7Bc8ktLeQ4355hAdpG6"
    os.environ['NASDAQ_DATA_LINK_API_KEY'] = "s_phvq25xVMyCa6KBXFj"
    main()
    
    
    
