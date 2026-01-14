from __future__ import annotations

import json
import os
from typing import Dict, Optional

import pandas as pd


def _safe_mean(series: pd.Series) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    return float(s.mean()) if len(s) else float("nan")


def _format_pct(x: float) -> str:
    if pd.isna(x):
        return "NA"
    return f"{x*100:.2f}%"


def _format_float(x: float) -> str:
    if pd.isna(x):
        return "NA"
    return f"{x:.4f}"


def _summarize_curves(curves: Optional[Dict[str, pd.DataFrame]]) -> Dict[str, float]:
    if not curves:
        return {
            "avg_equity": float("nan"),
            "avg_cash": float("nan"),
            "avg_equity_to_cash_ratio": float("nan"),
            "avg_bars_per_run": float("nan"),
        }
    all_equity = []
    all_cash = []
    bars_per_run = []
    for _, df in curves.items():
        if df is None or df.empty:
            continue
        if "equity" in df.columns:
            all_equity.append(pd.to_numeric(df["equity"], errors="coerce"))
        if "cash" in df.columns:
            all_cash.append(pd.to_numeric(df["cash"], errors="coerce"))
        bars_per_run.append(len(df))
    avg_equity = _safe_mean(pd.concat(all_equity)) if all_equity else float("nan")
    avg_cash = _safe_mean(pd.concat(all_cash)) if all_cash else float("nan")
    ratio = (avg_equity / avg_cash) if (not pd.isna(avg_equity) and not pd.isna(avg_cash) and avg_cash != 0) else float("nan")
    avg_bars = sum(bars_per_run) / len(bars_per_run) if bars_per_run else float("nan")
    return {
        "avg_equity": avg_equity,
        "avg_cash": avg_cash,
        "avg_equity_to_cash_ratio": ratio,
        "avg_bars_per_run": avg_bars,
    }


def generate_test_report(
    plot_dir: Optional[str],
    test_name: str,
    agent_name: str,
    agent_info: object,
    results_df: pd.DataFrame,
    curves: Optional[Dict[str, pd.DataFrame]] = None,
) -> Optional[str]:
    if not plot_dir:
        return None
    os.makedirs(plot_dir, exist_ok=True)
    out_path = os.path.join(plot_dir, f"test_report_{test_name}.md")

    if results_df is None or results_df.empty:
        summary_lines = ["No results available."]
        res = pd.DataFrame()
    else:
        res = results_df.copy()
        for col in ["total_return", "sharpe", "max_drawdown", "final_equity"]:
            if col in res.columns:
                res[col] = pd.to_numeric(res[col], errors="coerce")
        summary_lines = []
        if "total_return" in res.columns:
            summary_lines.append(f"- Avg total return: {_format_pct(res['total_return'].mean())}")
            summary_lines.append(f"- Median total return: {_format_pct(res['total_return'].median())}")
        if "sharpe" in res.columns:
            summary_lines.append(f"- Avg Sharpe: {_format_float(res['sharpe'].mean())}")
        if "max_drawdown" in res.columns:
            summary_lines.append(f"- Avg max drawdown: {_format_pct(res['max_drawdown'].mean())}")
        if "final_equity" in res.columns:
            summary_lines.append(f"- Avg final equity: {_format_float(res['final_equity'].mean())}")
        summary_lines.append(f"- Runs: {len(res)}")

    curve_stats = _summarize_curves(curves)

    if isinstance(agent_info, dict):
        agent_info_str = json.dumps(agent_info, indent=2, sort_keys=True, default=str)
    else:
        agent_info_str = str(agent_info)

    md = []
    md.append(f"# Test Report - {test_name}")
    md.append("")
    md.append(f"**Agent**: {agent_name}")
    md.append("")
    md.append("## Data/Signals Used")
    md.append("")
    md.append("```")
    md.append(agent_info_str)
    md.append("```")
    md.append("")
    md.append("## Summary Statistics")
    md.append("")
    md.extend(summary_lines)
    md.append("")
    md.append("## Equity/Cash Overview (from recorded curves)")
    md.append("")
    md.append(f"- Avg equity: {_format_float(curve_stats['avg_equity'])}")
    md.append(f"- Avg cash: {_format_float(curve_stats['avg_cash'])}")
    md.append(f"- Avg equity/cash ratio: {_format_float(curve_stats['avg_equity_to_cash_ratio'])}")
    md.append(f"- Avg bars per run: {_format_float(curve_stats['avg_bars_per_run'])}")
    md.append("")
    md.append("## Top Results")
    md.append("")
    if not res.empty and "total_return" in res.columns:
        top = res.sort_values("total_return", ascending=False).head(10)
        cols = [c for c in ["trial", "symbol", "start_date", "end_date", "timespan", "multiplier", "total_return", "sharpe", "max_drawdown", "final_equity"] if c in top.columns]
        md.append(top[cols].to_markdown(index=False))
    else:
        md.append("No per-run results available.")
    md.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    return out_path

