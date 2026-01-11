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


@dataclass(frozen=True)
class AllowedWindow:
    symbol: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    timespan: str = "minute"
    multiplier: int = 1


def load_allowlist_csv(path: str) -> List[AllowedWindow]:
    """
    CSV columns required:
      symbol,start_date,end_date,timespan,multiplier
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Allowlist CSV not found: {path}")
    records: List[AllowedWindow] = []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        required = {"symbol", "start_date", "end_date"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns in allowlist: {missing}")
        for row in reader:
            records.append(
                AllowedWindow(
                    symbol=row["symbol"].strip(),
                    start_date=row["start_date"].strip(),
                    end_date=row["end_date"].strip(),
                    timespan=(row.get("timespan") or "minute").strip(),
                    multiplier=int((row.get("multiplier") or "1").strip()),
                )
            )
    if not records:
        raise ValueError("Allowlist CSV has no rows.")
    return records


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


class BacktestSuite:
    def __init__(
        self,
        allowlist: List[AllowedWindow],
        agent_factory: Callable[[], BaseAgent],
        initial_cash: float = 100000.0,
        commission_rate: float = 0.0005,
        seed: Optional[int] = None,
    ) -> None:
        self.allowlist = list(allowlist)
        self.agent_factory = agent_factory
        self.initial_cash = float(initial_cash)
        self.commission_rate = float(commission_rate)
        self._rng = random.Random(seed)

        # Index by symbol
        self._by_symbol: Dict[str, List[AllowedWindow]] = {}
        for aw in self.allowlist:
            self._by_symbol.setdefault(aw.symbol, []).append(aw)

    def sample_scenarios(
        self,
        num_symbols: int,
        windows_per_symbol: int,
    ) -> List[AllowedWindow]:
        symbols = list(self._by_symbol.keys())
        if not symbols:
            raise ValueError("Allowlist is empty.")
        chosen_syms = self._rng.sample(symbols, k=min(num_symbols, len(symbols)))
        picks: List[AllowedWindow] = []
        for s in chosen_syms:
            pool = self._by_symbol[s]
            if len(pool) <= windows_per_symbol:
                picks.extend(pool)
            else:
                picks.extend(self._rng.sample(pool, k=windows_per_symbol))
        return picks

    def run_trial(
        self,
        num_symbols: int,
        windows_per_symbol: int,
        record_equity_curves: bool = False,
        plot_dir: Optional[str] = None,
        warmup_days: int = 14,
        trading_days: int = 14,
    ) -> Tuple[pd.DataFrame, Optional[Dict[str, pd.DataFrame]]]:
        scenarios = self.sample_scenarios(num_symbols=num_symbols, windows_per_symbol=windows_per_symbol)
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


