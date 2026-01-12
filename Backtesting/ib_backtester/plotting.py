from __future__ import annotations

from typing import List, Optional, Dict

import pandas as pd

from .engine import FillReport


def plot_candles_with_trades(
    data: pd.DataFrame,
    trades: List[FillReport],
    title: Optional[str] = None,
    save_path: Optional[str] = None,
    show: bool = True,
    trading_start_timestamp: Optional[int] = None,
    trading_end_timestamp: Optional[int] = None,
    equity_curve: Optional[pd.DataFrame] = None,
) -> None:
    """
    Plot candlesticks with volume and overlay buy/sell markers at trade timestamps.
    Shade pre-trading warmup region. Add a bottom panel for cumulative return.

    Requires mplfinance and matplotlib.
    """
    try:
        import mplfinance as mpf
        import numpy as np
        import matplotlib.pyplot as plt
    except Exception as e:
        raise RuntimeError("Plotting requires 'mplfinance' (and matplotlib). Please install them.") from e

    if "time" not in data.columns:
        raise ValueError("Data must include a 'time' column with datetime values.")

    # Futuristic dark theme style
    ai_market_colors = mpf.make_marketcolors(
        up="#00D97E",          # neon green for up candles
        down="#FF6B6B",        # vivid coral for down candles
        edge="inherit",
        wick="inherit",
        volume="inherit",
        ohlc="inherit",
    )
    ai_style = mpf.make_mpf_style(
        base_mpf_style="nightclouds",
        marketcolors=ai_market_colors,
        facecolor="#0b0f19",   # deep navy background
        edgecolor="#2a2f3a",
        gridcolor="#2a2f3a",
        gridstyle="-",
        figcolor="#0b0f19",
        rc={
            "axes.labelcolor": "#C8D0E0",
            "axes.edgecolor": "#5A6372",
            "text.color": "#C8D0E0",
            "xtick.color": "#9AA4B2",
            "ytick.color": "#9AA4B2",
        },
    )

    # Base data indexed by datetime for resampling (keep original columns)
    base = data.copy()
    base = base.set_index(pd.DatetimeIndex(base["time"])).sort_index()
    if trading_end_timestamp is not None:
        end_dt = pd.to_datetime(trading_end_timestamp, unit="ms")
        base = base.loc[:end_dt]

    # Resample to hourly candlesticks and volume for visualization
    df = pd.DataFrame({
        "Open": base["open"].resample("1h").first(),
        "High": base["high"].resample("1h").max(),
        "Low": base["low"].resample("1h").min(),
        "Close": base["close"].resample("1h").last(),
        "Volume": base["volume"].resample("1h").sum(),
    }).dropna(how="all")

    # No VWAP overlay (removed by user request)

    # Build trade positions and labels (used for shading and optional annotation)
    idx = df.index
    buy_pos: List[int] = []
    sell_pos: List[int] = []
    qty_label: Dict[int, str] = {}

    for tr in trades:
        t_dt = pd.to_datetime(int(tr.timestamp), unit="ms")
        # Skip trades outside plotted range
        if t_dt < idx[0] or t_dt > idx[-1]:
            continue
        # Find nearest bar index for robustness
        pos = int(idx.get_indexer([t_dt], method="nearest")[0])
        if tr.action.value == "BUY":
            buy_pos.append(pos)
            qty_label[pos] = f"+{tr.quantity}"
        else:
            sell_pos.append(pos)
            qty_label[pos] = f"-{tr.quantity}"

    apds = []
    # No VWAP overlay

    # Build returns panel: compute cumulative returns starting at trading start equity
    returns_series = None
    if equity_curve is not None and not equity_curve.empty:
        eq = equity_curve.copy()
        eq.index = pd.DatetimeIndex(pd.to_datetime(eq["time"]))
        # Align to candle index
        eq = eq.reindex(idx, method="pad")
        if trading_start_timestamp is not None:
            t0 = pd.to_datetime(trading_start_timestamp, unit="ms")
            if t0 in eq.index:
                start_equity = float(eq.loc[t0, "equity"])
            else:
                # nearest at/after
                start_equity = float(eq.loc[eq.index[0], "equity"])
        else:
            start_equity = float(eq["equity"].iloc[0])
        returns_series = (eq["equity"] / start_equity) - 1.0
        apds.append(mpf.make_addplot(returns_series.values, panel=2, color="#00E5FF", ylabel="Return"))

        # Build holding percent panel (stock value / total equity * 100)
        # Avoid division by zero by masking zeros
        equity_vals = eq["equity"].replace(0, pd.NA).astype(float)
        hold_value = (eq["position"].astype(float) * eq["close"].astype(float))
        hold_pct = (hold_value / equity_vals) * 100.0
        apds.append(mpf.make_addplot(hold_pct.values, panel=3, color="#A78BFA", ylabel="Holding %"))

        # Build position (shares) panel
        position_series = eq["position"].astype(float)
        apds.append(mpf.make_addplot(position_series.values, panel=4, color="#FFB86C", ylabel="Shares"))

    # Volume on its own panel (panel=1) – hourly
    if "Volume" in df.columns and len(df) > 0:
        apds.append(mpf.make_addplot(df["Volume"].values, panel=1, type="bar", color="#3B4455", ylabel="Volume"))

    kwargs = {
        "type": "candle",
        "volume": False,
        "addplot": apds if apds else None,
        "style": ai_style,
        "title": title or "",
        "figratio": (24, 9),
        "figscale": 1.8,
        "tight_layout": True,
        "warn_too_much_data": 10000,
    }

    fig, axes = mpf.plot(df, returnfig=True, **kwargs)

    # Shade warmup region
    if trading_start_timestamp is not None:
        start_dt = idx[0]
        trading_start_dt = pd.to_datetime(trading_start_timestamp, unit="ms")
        axes[0].axvspan(start_dt, trading_start_dt, facecolor="#101826", alpha=0.35, zorder=0)

    # Shade buy/sell regions (one bar wide centered on timestamp)
    def span_bounds(i: int):
        # Compute left/right bounds around bar i using neighbor midpoints
        if len(idx) == 1:
            half = pd.Timedelta(minutes=1)
            return idx[i] - half, idx[i] + half
        if i == 0:
            half = (idx[i + 1] - idx[i]) / 2
            left, right = idx[i] - half, idx[i] + half
        elif i == len(idx) - 1:
            half = (idx[i] - idx[i - 1]) / 2
            left, right = idx[i] - half, idx[i] + half
        else:
            left_half = (idx[i] - idx[i - 1]) / 2
            right_half = (idx[i + 1] - idx[i]) / 2
            left, right = idx[i] - left_half, idx[i] + right_half
        return left, right

    for i in buy_pos:
        l, r = span_bounds(i)
        axes[0].axvspan(l, r, facecolor="#0EA5A5", alpha=0.35, zorder=1)  # teal glow
    for i in sell_pos:
        l, r = span_bounds(i)
        axes[0].axvspan(l, r, facecolor="#F59E0B", alpha=0.35, zorder=1)  # amber glow

    # Annotate quantities next to markers
    # Place annotation at close price of the bar
    if len(qty_label) > 0:
        # Need 'Close' series available in df
        close_series = df["Close"]
        for pos, label in qty_label.items():
            if pos < 0 or pos >= len(idx):
                continue
            y = float(close_series.iloc[pos])
            axes[0].annotate(
                label,
                xy=(idx[pos], y),
                xytext=(0, 8),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                color="#E5E7EB",
                bbox=dict(boxstyle="round,pad=0.2", fc="#0b0f19", ec="#5A6372", alpha=0.7),
            )

    # Add clear borders to each subplot/panel
    axes_list = axes if isinstance(axes, (list, tuple)) else [axes]
    for ax in axes_list:
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_edgecolor("#5A6372")
            spine.set_linewidth(1.0)
        ax.grid(True, color="#2a2f3a", linestyle="-", linewidth=0.6, alpha=0.6)

    if save_path:
        fig.savefig(save_path, dpi=200, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


