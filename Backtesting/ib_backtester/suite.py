from __future__ import annotations

import csv
import os
import random
from dataclasses import dataclass
from math import sqrt
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from .engine import BaseAgent, IBBacktestEnv
from .plotting import plot_candles_with_trades
try:
    from Common import db as _db
except Exception:
    _db = None  # type: ignore


@dataclass(frozen=True)
class ScopeWindow:
    symbol: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    timespan: str = "minute"
    multiplier: int = 1


@dataclass(frozen=True)
class TestDefinition:
    name: str
    trials: int
    overall_start_date: str
    overall_end_date: str
    seed: Optional[int] = None
    record_curves: bool = False
    plot_dir: Optional[str] = None
    warmup_days: int = 14
    trading_days: int = 14


def _parse_bool(value: str) -> bool:
    v = (value or "").strip().lower()
    return v in {"1", "true", "t", "yes", "y"}


def load_test_definitions_csv(path: str) -> List[TestDefinition]:
    """
    CSV columns:
      required: name,trials,overall_start_date,overall_end_date
      optional: seed,record_curves,plot_dir,warmup_days,trading_days
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Test definitions CSV not found: {path}")
    records: List[TestDefinition] = []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        required = {"name", "trials", "overall_start_date", "overall_end_date"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns in test definitions CSV: {missing}")
        for row in reader:
            # Skip fully empty rows or rows without a name
            if not any(((v or "").strip() for v in row.values())):
                continue
            name = (row.get("name") or "").strip()
            if name == "":
                continue
            records.append(
                TestDefinition(
                    name=name,
                    trials=int((row.get("trials") or "").strip()),
                    overall_start_date=(row.get("overall_start_date") or "").strip(),
                    overall_end_date=(row.get("overall_end_date") or "").strip(),
                    seed=(int(row["seed"]) if (row.get("seed") or "").strip() != "" else None),
                    record_curves=_parse_bool(row.get("record_curves", "")),
                    plot_dir=((row.get("plot_dir") or "").strip() or None),
                    warmup_days=int((row.get("warmup_days") or "14").strip() or 14),
                    trading_days=int((row.get("trading_days") or "14").strip() or 14),
                )
            )
    if not records:
        raise ValueError("Test definitions CSV has no rows.")
    return records


def _pick_symbol_windows_within_range(
    rng: random.Random,
    overall_start_date: str,
    overall_end_date: str,
    num_symbols: int,
    windows_per_symbol: int,
    by_symbol: Dict[str, List[ScopeWindow]],
    warmup_days: int,
    trading_days: int,
) -> List[ScopeWindow]:
    symbols = list(by_symbol.keys())
    if not symbols:
        raise ValueError("Test scope is empty.")
    chosen_syms = rng.sample(symbols, k=min(num_symbols, len(symbols)))

    start_dt = pd.to_datetime(overall_start_date)
    end_dt = pd.to_datetime(overall_end_date)
    total_days = int(warmup_days) + int(trading_days)
    max_start = end_dt - pd.Timedelta(days=total_days)
    if max_start < start_dt:
        raise ValueError("Overall date range too short for warmup_days + trading_days.")

    picks: List[ScopeWindow] = []
    for s in chosen_syms:
        defaults = by_symbol.get(s, [])
        base_timespan = defaults[0].timespan if defaults else "minute"
        base_multiplier = defaults[0].multiplier if defaults else 1

        for _ in range(max(1, windows_per_symbol)):
            span_days = (max_start - start_dt).days
            offset_days = rng.randrange(span_days + 1) if span_days > 0 else 0
            win_start_dt = start_dt + pd.Timedelta(days=offset_days)
            win_end_dt = win_start_dt + pd.Timedelta(days=total_days)
            picks.append(
                ScopeWindow(
                    symbol=s,
                    start_date=win_start_dt.strftime("%Y-%m-%d"),
                    end_date=win_end_dt.strftime("%Y-%m-%d"),
                    timespan=base_timespan,
                    multiplier=int(base_multiplier),
                )
            )
    return picks


def load_test_scope_csv(path: str) -> List[ScopeWindow]:
    """
    CSV columns required:
      symbol,start_date,end_date,timespan,multiplier
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Test scope CSV not found: {path}")
    records: List[ScopeWindow] = []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        required = {"symbol", "start_date", "end_date"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns in test scope: {missing}")
        for row in reader:
            records.append(
                ScopeWindow(
                    symbol=row["symbol"].strip(),
                    start_date=row["start_date"].strip(),
                    end_date=row["end_date"].strip(),
                    timespan=(row.get("timespan") or "minute").strip(),
                    multiplier=int((row.get("multiplier") or "1").strip()),
                )
            )
    if not records:
        raise ValueError("Test scope CSV has no rows.")
    return records


def load_test_scope_db() -> List[ScopeWindow]:
    records: List[ScopeWindow] = []
    with _db.get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT symbol, start_date, end_date, timespan, multiplier
                FROM test_scope
                ORDER BY symbol, start_date
                """
            )
            for (symbol, start_date, end_date, timespan, multiplier) in cur.fetchall():
                records.append(
                    ScopeWindow(
                        symbol=str(symbol),
                        start_date=str(start_date),
                        end_date=str(end_date),
                        timespan=str(timespan),
                        multiplier=int(multiplier),
                    )
                )
    if not records:
        raise ValueError("Test scope table has no rows.")
    return records


from typing import Tuple  # local import to avoid top-level change cascade


def load_test_scope_for_test_db(test_name: str) -> Tuple[List[ScopeWindow], str, str]:
    if _db is None:
        raise RuntimeError("DB module not available")
    records: List[ScopeWindow] = []
    start_s: Optional[str] = None
    end_s: Optional[str] = None
    with _db.get_pg_conn() as conn:
        with conn.cursor() as cur:
            # Fetch overall window from test_scope
            cur.execute(
                """
                SELECT start_date, end_date
                FROM test_scope
                WHERE test_name = %s
                """,
                (test_name,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"test_scope not found for test '{test_name}'")
            start_s, end_s = str(row[0]), str(row[1])

            cur.execute(
                """
                SELECT s.symbol, s.timespan, s.multiplier
                FROM test_scope_symbols s
                JOIN test_scope t ON t.test_name = s.test_name
                WHERE s.test_name = %s
                ORDER BY s.symbol
                """,
                (test_name,),
            )
            for (symbol, timespan, multiplier) in cur.fetchall():
                records.append(
                    ScopeWindow(
                        symbol=str(symbol),
                        start_date=start_s,
                        end_date=end_s,
                        timespan=str(timespan),
                        multiplier=int(multiplier),
                    )
                )
    if not records:
        raise ValueError(f"No symbols found in test_scope for test '{test_name}'.")
    return records, start_s, end_s


def _annualization_factor(timespan: str, multiplier: int) -> float:
    # Approximate bar count per trading year for US equities
    if timespan == "minute":
        bars_per_day = 390 / max(multiplier, 1)
        return 252 * bars_per_day
    if timespan == "hour":
        bars_per_day = 6.5 / max(multiplier, 1)
        return 252 * bars_per_day
    if timespan == "day":
        return 252 / max(multiplier, 1)
    # Fallback: treat as daily
    return 252.0


def _compute_metrics(equity_curve: pd.DataFrame, timespan: str, multiplier: int, initial_cash: float) -> Dict:
    if equity_curve.empty:
        return {
            "final_equity": initial_cash,
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe": 0.0,
        }
    equity = equity_curve["equity"].astype(float)
    final_equity = float(equity.iloc[-1])
    total_return = (final_equity / float(initial_cash)) - 1.0

    cummax = equity.cummax()
    drawdown = (equity - cummax) / cummax.replace(0, pd.NA)
    max_drawdown = float(drawdown.min() if not drawdown.isna().all() else 0.0)

    rets = equity.pct_change().dropna()
    if len(rets) >= 2 and rets.std() > 0:
        af = _annualization_factor(timespan, multiplier)
        sharpe = float((rets.mean() / rets.std()) * sqrt(af))
    else:
        sharpe = 0.0

    return {
        "final_equity": final_equity,
        "total_return": total_return,
        "max_drawdown": max_drawdown,
        "sharpe": sharpe,
    }


def load_test_definitions_db(names: Optional[List[str]] = None) -> List[TestDefinition]:
    rows: List[TestDefinition] = []
    with _db.get_pg_conn() as conn:
        with conn.cursor() as cur:
            if names:
                cur.execute(
                    """
                    SELECT name, trials,
                           overall_start_date, overall_end_date, seed,
                           record_curves, plot_dir, warmup_days, trading_days
                    FROM test_definitions
                    WHERE name = ANY(%s)
                    ORDER BY name
                    """,
                    (names,),
                )
            else:
                cur.execute(
                    """
                    SELECT name, trials,
                           overall_start_date, overall_end_date, seed,
                           record_curves, plot_dir, warmup_days, trading_days
                    FROM test_definitions
                    ORDER BY name
                    """
                )
            for r in cur.fetchall():
                (name, trials,
                 overall_start_date, overall_end_date, seed,
                 record_curves, plot_dir, warmup_days, trading_days) = r
                rows.append(
                    TestDefinition(
                        name=str(name),
                        trials=int(trials),
                        overall_start_date=str(overall_start_date),
                        overall_end_date=str(overall_end_date),
                        seed=(int(seed) if seed is not None else None),
                        record_curves=bool(record_curves),
                        plot_dir=(str(plot_dir) if plot_dir else None),
                        warmup_days=int(warmup_days),
                        trading_days=int(trading_days),
                    )
                )
    if not rows:
        raise ValueError("test_definitions table has no rows.")
    return rows


def load_test_jobs_db(names: Optional[List[str]] = None) -> List[Tuple[str, str]]:
    """
    Load (test_name, agent_name) job pairs from test_jobs.
    If names is provided, filter to those test_names only.
    """
    jobs: List[Tuple[str, str]] = []
    with _db.get_pg_conn() as conn:
        with conn.cursor() as cur:
            if names:
                cur.execute(
                    """
                    SELECT test_name, agent_name
                    FROM test_jobs
                    WHERE test_name = ANY(%s)
                    ORDER BY test_name, agent_name
                    """,
                    (names,),
                )
            else:
                cur.execute(
                    """
                    SELECT test_name, agent_name
                    FROM test_jobs
                    ORDER BY test_name, agent_name
                    """
                )
            for (tname, aname) in cur.fetchall():
                jobs.append((str(tname), str(aname)))
    return jobs

class BacktestSuite:
    def __init__(
        self,
        agent_factory: Callable[[], BaseAgent],
        initial_cash: float = 100000.0,
        commission_rate: float = 0.0005,
        seed: Optional[int] = None,
    ) -> None:
        self.agent_factory = agent_factory
        self.initial_cash = float(initial_cash)
        self.commission_rate = float(commission_rate)
        self._rng = random.Random(seed)

    def sample_single_symbol_windows(
        self,
        symbol: str,
        windows_per_symbol: int,
        overall_start_date: str,
        overall_end_date: str,
        warmup_days: int,
        trading_days: int,
        timespan: str,
        multiplier: int,
    ) -> List[ScopeWindow]:
        start_dt = pd.to_datetime(overall_start_date)
        end_dt = pd.to_datetime(overall_end_date)
        total_days = int(warmup_days) + int(trading_days)
        max_start = end_dt - pd.Timedelta(days=total_days)
        if max_start < start_dt:
            raise ValueError("Overall date range too short for warmup_days + trading_days.")
        picks: List[ScopeWindow] = []
        for _ in range(max(1, int(windows_per_symbol))):
            span_days = (max_start - start_dt).days
            offset_days = self._rng.randrange(span_days + 1) if span_days > 0 else 0
            win_start_dt = start_dt + pd.Timedelta(days=offset_days)
            win_end_dt = win_start_dt + pd.Timedelta(days=total_days)
            picks.append(
                ScopeWindow(
                    symbol=str(symbol),
                    start_date=win_start_dt.strftime("%Y-%m-%d"),
                    end_date=win_end_dt.strftime("%Y-%m-%d"),
                    timespan=str(timespan),
                    multiplier=int(multiplier),
                )
            )
        return picks

    def run_trial(
        self,
        symbol: str,
        timespan: str,
        multiplier: int,
        windows_per_symbol: int,
        overall_start_date: str,
        overall_end_date: str,
        record_equity_curves: bool = False,
        plot_dir: Optional[str] = None,
        warmup_days: int = 14,
        trading_days: int = 14,
    ) -> Tuple[pd.DataFrame, Optional[Dict[str, pd.DataFrame]]]:
        scenarios = self.sample_single_symbol_windows(
            symbol=symbol,
            windows_per_symbol=windows_per_symbol,
            overall_start_date=overall_start_date,
            overall_end_date=overall_end_date,
            warmup_days=warmup_days,
            trading_days=trading_days,
            timespan=timespan,
            multiplier=multiplier,
        )
        results: List[Dict] = []
        curves: Dict[str, pd.DataFrame] = {}

        for idx, aw in enumerate(scenarios):
            agent = self.agent_factory()
            env = IBBacktestEnv(
                symbol=aw.symbol,
                start_date=aw.start_date,
                end_date=aw.end_date,
                timespan=aw.timespan,
                multiplier=aw.multiplier,
                initial_cash=self.initial_cash,
                commission_rate=self.commission_rate,
            )
            curve = env.run(agent, warmup_days=warmup_days, trading_days=trading_days)
            metrics = _compute_metrics(curve, aw.timespan, aw.multiplier, self.initial_cash)
            row = {
                "run_id": idx,
                "symbol": aw.symbol,
                "start_date": aw.start_date,
                "end_date": aw.end_date,
                "timespan": aw.timespan,
                "multiplier": aw.multiplier,
                **metrics,
            }
            results.append(row)
            if record_equity_curves:
                key = f"{aw.symbol}_{aw.start_date}_{aw.end_date}_{aw.timespan}{aw.multiplier}"
                curves[key] = curve.copy()

            if plot_dir:
                try:
                    os.makedirs(plot_dir, exist_ok=True)
                    fname = f"trial_{idx}_{aw.symbol}_{aw.start_date}_{aw.end_date}_{aw.timespan}{aw.multiplier}.png"
                    safe_name = fname.replace(":", "-").replace("/", "-").replace("\\", "-")
                    out_path = os.path.join(plot_dir, safe_name)
                    # Title based on actual plotted window (warmup + trading)
                    plot_start_dt = str(env.data.loc[0, "time"]) if not env.data.empty else aw.start_date
                    if getattr(env, "trading_end_timestamp", None) is not None:
                        plot_end_dt = pd.to_datetime(env.trading_end_timestamp, unit="ms").strftime("%Y-%m-%d %H:%M")
                    else:
                        plot_end_dt = aw.end_date
                    title = f"{aw.symbol} {plot_start_dt} to {plot_end_dt} (warmup {warmup_days}d, trade {trading_days}d) ({aw.timespan} x{aw.multiplier})"
                    plot_candles_with_trades(
                        env.data,
                        env.broker.trades,
                        title=title,
                        save_path=out_path,
                        show=False,
                        trading_start_timestamp=env.trading_start_timestamp,
                        trading_end_timestamp=env.trading_end_timestamp,
                        equity_curve=curve,
                    )
                except Exception as _:
                    # Do not fail the suite on plotting errors
                    pass

        return pd.DataFrame(results), (curves if record_equity_curves else None)

    def run_trial_within_range(
        self,
        symbol: str,
        timespan: str,
        multiplier: int,
        windows_per_symbol: int,
        overall_start_date: str,
        overall_end_date: str,
        record_equity_curves: bool = False,
        plot_dir: Optional[str] = None,
        warmup_days: int = 14,
        trading_days: int = 14,
    ) -> Tuple[pd.DataFrame, Optional[Dict[str, pd.DataFrame]]]:
        scenarios = self.sample_single_symbol_windows(
            symbol=symbol,
            windows_per_symbol=windows_per_symbol,
            overall_start_date=overall_start_date,
            overall_end_date=overall_end_date,
            warmup_days=warmup_days,
            trading_days=trading_days,
            timespan=timespan,
            multiplier=multiplier,
        )
        results: List[Dict] = []
        curves: Dict[str, pd.DataFrame] = {}

        for idx, aw in enumerate(scenarios):
            agent = self.agent_factory()
            env = IBBacktestEnv(
                symbol=aw.symbol,
                start_date=aw.start_date,
                end_date=aw.end_date,
                timespan=aw.timespan,
                multiplier=aw.multiplier,
                initial_cash=self.initial_cash,
                commission_rate=self.commission_rate,
            )
            curve = env.run(agent, warmup_days=warmup_days, trading_days=trading_days)
            metrics = _compute_metrics(curve, aw.timespan, aw.multiplier, self.initial_cash)
            row = {
                "run_id": idx,
                "symbol": aw.symbol,
                "start_date": aw.start_date,
                "end_date": aw.end_date,
                "timespan": aw.timespan,
                "multiplier": aw.multiplier,
                **metrics,
            }
            results.append(row)
            if record_equity_curves:
                key = f"{aw.symbol}_{aw.start_date}_{aw.end_date}_{aw.timespan}{aw.multiplier}"
                curves[key] = curve.copy()

            if plot_dir:
                try:
                    os.makedirs(plot_dir, exist_ok=True)
                    fname = f"trial_{idx}_{aw.symbol}_{aw.start_date}_{aw.end_date}_{aw.timespan}{aw.multiplier}.png"
                    safe_name = fname.replace(":", "-").replace("/", "-").replace("\\", "-")
                    out_path = os.path.join(plot_dir, safe_name)
                    # Title based on actual plotted window (warmup + trading)
                    plot_start_dt = str(env.data.loc[0, "time"]) if not env.data.empty else aw.start_date
                    if getattr(env, "trading_end_timestamp", None) is not None:
                        plot_end_dt = pd.to_datetime(env.trading_end_timestamp, unit="ms").strftime("%Y-%m-%d %H:%M")
                    else:
                        plot_end_dt = aw.end_date
                    title = f"{aw.symbol} {plot_start_dt} to {plot_end_dt} (warmup {warmup_days}d, trade {trading_days}d) ({aw.timespan} x{aw.multiplier})"
                    plot_candles_with_trades(
                        env.data,
                        env.broker.trades,
                        title=title,
                        save_path=out_path,
                        show=False,
                        trading_start_timestamp=env.trading_start_timestamp,
                        trading_end_timestamp=env.trading_end_timestamp,
                        equity_curve=curve,
                    )
                except Exception as _:
                    # Do not fail the suite on plotting errors
                    pass

        return pd.DataFrame(results), (curves if record_equity_curves else None)

    def run(
        self,
        trials: int,
        num_symbols: int,
        windows_per_symbol: int,
        record_equity_curves: bool = False,
        plot_dir: Optional[str] = None,
        warmup_days: int = 14,
        trading_days: int = 14,
    ) -> Tuple[pd.DataFrame, Optional[Dict[str, pd.DataFrame]]]:
        all_rows: List[pd.DataFrame] = []
        all_curves: Dict[str, pd.DataFrame] = {}
        for t in range(trials):
            df, curves = self.run_trial(
                num_symbols,
                windows_per_symbol,
                record_equity_curves=record_equity_curves,
                plot_dir=plot_dir,
                warmup_days=warmup_days,
                trading_days=trading_days,
            )
            df = df.assign(trial=t)
            all_rows.append(df)
            if curves:
                all_curves.update({f"trial{t}_{k}": v for k, v in curves.items()})
        res = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
        return res, (all_curves if record_equity_curves else None)

    def run_within_overall_range(
        self,
        trials: int,
        symbol: str,
        timespan: str,
        multiplier: int,
        windows_per_symbol: int,
        overall_start_date: str,
        overall_end_date: str,
        record_equity_curves: bool = False,
        plot_dir: Optional[str] = None,
        warmup_days: int = 14,
        trading_days: int = 14,
    ) -> Tuple[pd.DataFrame, Optional[Dict[str, pd.DataFrame]]]:
        all_rows: List[pd.DataFrame] = []
        all_curves: Dict[str, pd.DataFrame] = {}
        for t in range(trials):
            df, curves = self.run_trial_within_range(
                symbol=symbol,
                timespan=timespan,
                multiplier=multiplier,
                windows_per_symbol=windows_per_symbol,
                overall_start_date=overall_start_date,
                overall_end_date=overall_end_date,
                record_equity_curves=record_equity_curves,
                plot_dir=plot_dir,
                warmup_days=warmup_days,
                trading_days=trading_days,
            )
            df = df.assign(trial=t)
            all_rows.append(df)
            if curves:
                all_curves.update({f"trial{t}_{k}": v for k, v in curves.items()})
        res = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
        return res, (all_curves if record_equity_curves else None)


