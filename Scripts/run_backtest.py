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
            "location": "Scripts/run_backtest.py:bootstrap",
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

from Backtesting.ib_backtester.suite import (
    BacktestSuite,
    load_test_definitions_db,
    load_test_jobs_db,
)
from Backtesting.ib_backtester.agents.sample_agent import SmaCrossAgent
from Backtesting.ib_backtester.agents.multisignal_agent import MultiSignalAgent, ExternalDataConfig
from Backtesting.ib_backtester.agents.multi_source_model_agent import MultiSourceModelAgent, MultiSourceConfig
from Common.reporting import generate_test_report
from Common.agents_registry import get_agent_factory
from Common.agents_loader import get_agent_factory_from_registry


def main():
    
    # Config
    base_dir = os.path.dirname(__file__)
    
    select_names = os.environ.get("BACKTEST_TEST_NAMES", "")
    selected = {s.strip() for s in select_names.split(",") if s.strip()} if select_names else None

    # Always load jobs and test definitions from Postgres (optionally filtered by BACKTEST_TEST_NAMES)
    try:
        sel_list = sorted(selected) if selected else None
        jobs = load_test_jobs_db(sel_list)
        if selected and not jobs:
            raise ValueError(f"No matching test jobs found for names: {sel_list}")
        test_types = load_test_definitions_db(sel_list)
        defs_by_name = {t.name: t for t in test_types}
    except Exception as e:
        raise RuntimeError("Failed to load jobs/definitions from Postgres. Ensure DATABASE_URL or PG* env vars are set and the DB is initialized (Scripts/init_db.py).") from e

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

    # Iterate over (test_name, agent_name) jobs; group by test_name
    for (test_name, agent_name_from_job) in jobs:
        cfg = defs_by_name.get(test_name)
        if not cfg:
            print(f"Skipping job ({test_name}, {agent_name_from_job}) missing test definition.")
            continue
        # Propagate testbench seed to agents (used for model RNG initialization)
        try:
            if cfg.seed is not None:
                os.environ["TESTBENCH_RANDOM_SEED"] = str(int(cfg.seed))
            else:
                if "TESTBENCH_RANDOM_SEED" in os.environ:
                    del os.environ["TESTBENCH_RANDOM_SEED"]
        except Exception:
            pass

        # Agent selection: from registry DB by agent_name in job
        try:
            from Common.agents_loader import get_agent_factory_from_registry_db
            agent_factory = get_agent_factory_from_registry_db(agent_name_from_job)
        except Exception as _:
            print(f"Skipping job ({test_name}, {agent_name_from_job}) – agent not found in registry.")
            continue
        # Probe an instance to describe agent for the report
        agent_probe = agent_factory()
        agent_name = agent_name_from_job or type(agent_probe).__name__
        agent_info = {}


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
        
        results_df = results_df.assign(test_name=test_name, agent=agent_name)
        print(f"Results for job test='{test_name}', agent='{agent_name}':")
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
    os.environ["DATABASE_URL"] = "postgresql://postgres:5369@localhost:5432/postgres"
    main()
    
    
    
