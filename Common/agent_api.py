from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import os
import numpy as np
import pandas as pd

from Common.massive_client import get_aggregate_bars
from Common.sharadar_client import get_sf1_series
from .signals_manager import load_available_signals, load_available_signals_csv, build_tensor_from_signals


@dataclass
class SnapshotSpec:
    window_days: int = 14
    include_primary_price: bool = True
    massive_specs: Optional[List[str]] = None  # ["SPY:day:1", ...]
    csv_paths: Optional[List[str]] = None      # ["path/to/econ.csv", ...]
    sf1_specs: Optional[List[str]] = None      # ["AAPL:ARQ:revenue", ...]


def _parse_massive_specs(specs: Optional[List[str]]) -> List[Tuple[str, str, int]]:
    parsed: List[Tuple[str, str, int]] = []
    for raw in (specs or []):
        parts = [p.strip() for p in str(raw).split(":")]
        if not parts or parts[0] == "":
            continue
        symbol = parts[0]
        timespan = parts[1] if len(parts) > 1 and parts[1] else "day"
        try:
            multiplier = int(parts[2]) if len(parts) > 2 and parts[2] else 1
        except Exception:
            multiplier = 1
        parsed.append((symbol, timespan, multiplier))
    return parsed


def _parse_sf1_specs(specs: Optional[List[str]]) -> List[Tuple[str, str, str]]:
    parsed: List[Tuple[str, str, str]] = []
    for raw in (specs or []):
        parts = [p.strip() for p in str(raw).split(":")]
        if len(parts) < 3:
            continue
        parsed.append((parts[0], parts[1], parts[2]))
    return parsed


def build_snapshot_tensor(
    primary_history: pd.DataFrame,
    snapshot_end: pd.Timestamp,
    spec: SnapshotSpec,
) -> Tuple[np.ndarray, List[str], pd.DatetimeIndex]:
    """
    Utility to assemble a synchronized tensor [time, features] from multiple sources.
    - Respects spec.window_days and spec.include_primary_price
    - Interpolates other series to the primary index using time interpolation
    Returns: (tensor, feature_names, index)
    """
    if primary_history.empty or "time" not in primary_history.columns:
        return np.empty((0, 0)), [], pd.DatetimeIndex([])
    start_dt = (snapshot_end.normalize() - pd.Timedelta(days=int(spec.window_days)))
    end_dt = snapshot_end
    base = primary_history.copy()
    base["time"] = pd.to_datetime(base["time"])
    base = base[(base["time"] >= start_dt) & (base["time"] <= end_dt)]
    if base.empty:
        return np.empty((0, 0)), [], pd.DatetimeIndex([])
    base_index = pd.DatetimeIndex(base["time"])

    features: List[pd.Series] = []
    names: List[str] = []

    if spec.include_primary_price and "close" in base.columns:
        s = pd.Series(base["close"].astype(float).values, index=base_index)
        s.name = "primary:close"
        features.append(s)
        names.append(s.name)

    # Massive sources
    for symbol, timespan, multiplier in _parse_massive_specs(spec.massive_specs):
        df = get_aggregate_bars(
            symbol=symbol,
            start_date=start_dt.strftime("%Y-%m-%d"),
            end_date=end_dt.strftime("%Y-%m-%d"),
            timespan=timespan,
            multiplier=int(multiplier),
        )
        if df is None or df.empty:
            continue
        s = pd.Series(df["close"].astype(float).values, index=pd.DatetimeIndex(pd.to_datetime(df["time"])))
        s = s.sort_index().reindex(base_index, method=None).interpolate(method="time", limit_direction="both")
        s.name = f"massive:{symbol}:{timespan}x{multiplier}"
        features.append(s)
        names.append(s.name)

    # SF1 sources
    for symbol, dimension, column in _parse_sf1_specs(spec.sf1_specs):
        s = get_sf1_series(
            symbol=symbol,
            column=column,
            dimension=dimension,
            start_date=start_dt.strftime("%Y-%m-%d"),
            end_date=end_dt.strftime("%Y-%m-%d"),
            api_key=None,
        )
        if s is None or s.empty:
            continue
        s = s.sort_index().reindex(base_index, method=None).interpolate(method="time", limit_direction="both")
        s.name = f"sf1:{symbol}:{dimension}:{column}"
        features.append(s)
        names.append(s.name)

    # CSV sources
    for path in (spec.csv_paths or []):
        try:
            df = pd.read_csv(path)
            if "date" not in df.columns or "value" not in df.columns:
                continue
            df["date"] = pd.to_datetime(df["date"])
            df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)].sort_values("date")
            if df.empty:
                continue
            s = pd.Series(df["value"].astype(float).values, index=pd.DatetimeIndex(df["date"]))
            s = s.sort_index().reindex(base_index, method=None).interpolate(method="time", limit_direction="both")
            s.name = f"csv:{path}"
            features.append(s)
            names.append(s.name)
        except Exception:
            continue

    if not features:
        return np.empty((len(base_index), 0)), [], base_index
    mat = np.column_stack([f.astype(float).values for f in features])
    return mat, names, base_index


def build_snapshot_from_signal_ids(
    primary_history: pd.DataFrame,
    snapshot_end: pd.Timestamp,
    signal_ids: List[str],
    available_signals_csv: Optional[str] = None,
    window_days: int = 14,
) -> Tuple[np.ndarray, List[str], pd.DatetimeIndex]:
    """
    Build snapshot tensor from registered signal IDs defined in available_signals.csv.
    
    This function automatically updates the last_access_time for the requested signals
    in the database to track signal usage.
    """
    if primary_history.empty or "time" not in primary_history.columns:
        return np.empty((0, 0)), [], pd.DatetimeIndex([])
    start_dt = (snapshot_end.normalize() - pd.Timedelta(days=int(window_days)))
    end_dt = snapshot_end
    base = primary_history.copy()
    base["time"] = pd.to_datetime(base["time"])
    base = base[(base["time"] >= start_dt) & (base["time"] <= end_dt)]
    if base.empty:
        return np.empty((0, 0)), [], pd.DatetimeIndex([])
    base_index = pd.DatetimeIndex(base["time"])

    # Resolve registry (prefer DB; fallback CSV)
    # IMPORTANT: Update access timestamps for the signals being used
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_csv = os.path.join(repo_root, "data", "available_signals.csv")
    registry_path = available_signals_csv or default_csv
    reg = load_available_signals(registry_path, update_access_time=True, signal_ids=signal_ids)

    # Fetch and align all signals
    df_sig, cols = build_tensor_from_signals(
        signal_ids=signal_ids,
        registry=reg,
        primary_index=base_index,
        start_date=start_dt.strftime("%Y-%m-%d"),
        end_date=end_dt.strftime("%Y-%m-%d"),
    )
    if df_sig.empty:
        return np.empty((len(base_index), 0)), [], base_index
    return df_sig.values.astype(float), list(df_sig.columns), base_index

