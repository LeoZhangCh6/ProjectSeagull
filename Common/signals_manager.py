from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd

from Common.massive_client import get_aggregate_bars
from Common.sharadar_client import get_sf1_series
from .db import get_pg_conn


@dataclass(frozen=True)
class SignalDef:
    id: str
    source: str          # "massive" | "sf1"
    spec: str            # massive: TICKER:TIMESPAN:MULTIPLIER[:FIELD]; sf1: TICKER:DIMENSION:COLUMN
    model_freq: Optional[str] = None  # pandas offset alias like '1D','1H','15T'
    description: str = ""
    enabled: bool = True


def load_available_signals_csv(path: str) -> Dict[str, SignalDef]:
    """
    Required columns:
      id,source,spec
    Optional:
      description,enabled
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"available_signals.csv not found: {path}")
    out: Dict[str, SignalDef] = {}
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        required = {"id", "source", "spec"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns in available_signals.csv: {missing}")
        for row in reader:
            if not any(((v or "").strip() for v in row.values())):
                continue
            sid = (row.get("id") or "").strip()
            if sid == "":
                continue
            src = (row.get("source") or "").strip().lower()
            spec = (row.get("spec") or "").strip()
            # support either 'model_freq' or legacy 'frequency' column name
            mf = (row.get("model_freq") or row.get("frequency") or "").strip()
            desc = (row.get("description") or "").strip()
            enabled = (row.get("enabled") or "1").strip().lower() in {"1", "true", "t", "yes", "y"}
            out[sid] = SignalDef(id=sid, source=src, spec=spec, model_freq=(mf or None), description=desc, enabled=enabled)
    if not out:
        raise ValueError("available_signals.csv has no usable rows.")
    return out


def load_available_signals_db(update_access_time: bool = False, signal_ids: Optional[List[str]] = None) -> Dict[str, SignalDef]:
    """
    Load available signals from Postgres table 'available_signals'.
    
    Args:
        update_access_time: If True, update last_access_time for the requested signals
        signal_ids: List of specific signal IDs to update (if None and update_access_time=True, updates all loaded signals)
    """
    out: Dict[str, SignalDef] = {}
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, source, spec, model_freq, description, enabled
                FROM available_signals
                WHERE enabled = TRUE
                """
            )
            for row in cur.fetchall():
                sid, source, spec, model_freq, desc, enabled = row
                out[str(sid)] = SignalDef(
                    id=str(sid),
                    source=str(source).lower(),
                    spec=str(spec),
                    model_freq=(str(model_freq) if model_freq else None),
                    description=(str(desc) if desc else ""),
                    enabled=bool(enabled),
                )
            
            # Update access timestamps if requested
            if update_access_time and out:
                ids_to_update = signal_ids if signal_ids else list(out.keys())
                if ids_to_update:
                    cur.execute(
                        """
                        UPDATE available_signals
                        SET last_access_time = now()
                        WHERE id = ANY(%s)
                        """,
                        (ids_to_update,)
                    )
                conn.commit()
                
    if not out:
        raise ValueError("No enabled signals found in available_signals.")
    return out


def load_available_signals(registry_csv: Optional[str] = None, update_access_time: bool = False, signal_ids: Optional[List[str]] = None) -> Dict[str, SignalDef]:
    """
    Preferred: load from Postgres if DATABASE_URL/PG* env present.
    Fallback: CSV at registry_csv argument (or raise).
    
    Args:
        registry_csv: Path to CSV fallback
        update_access_time: If True, update last_access_time for the requested signals
        signal_ids: List of specific signal IDs to update timestamps for
    """
    try:
        # Heuristic: if DATABASE_URL or PGHOST is set, try DB
        if os.environ.get("DATABASE_URL") or os.environ.get("PGHOST"):
            return load_available_signals_db(update_access_time=update_access_time, signal_ids=signal_ids)
    except Exception:
        pass
    if registry_csv is None:
        raise FileNotFoundError("Registry CSV path is required when DB is not configured.")
    return load_available_signals_csv(registry_csv)


def _fetch_massive_series(spec: str, start_date: str, end_date: str) -> Optional[pd.Series]:
    # spec: "TICKER:TIMESPAN:MULTIPLIER[:FIELD]"
    parts = [p.strip() for p in spec.split(":")]
    if len(parts) < 3:
        return None
    symbol = parts[0]
    timespan = parts[1] or "day"
    try:
        multiplier = int(parts[2] or "1")
    except Exception:
        multiplier = 1
    field = parts[3] if len(parts) > 3 and parts[3] else "close"
    df = get_aggregate_bars(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        timespan=timespan,
        multiplier=multiplier,
    )
    if df is None or df.empty or field not in df.columns:
        return None
    s = pd.Series(df[field].astype(float).values, index=pd.DatetimeIndex(pd.to_datetime(df["time"])))
    s.name = f"massive:{symbol}:{timespan}x{multiplier}:{field}"
    return s


def _fetch_sf1_series(spec: str, start_date: str, end_date: str) -> Optional[pd.Series]:
    # spec: "TICKER:DIMENSION:COLUMN"
    parts = [p.strip() for p in spec.split(":")]
    if len(parts) < 3:
        return None
    symbol, dimension, column = parts[0], parts[1], parts[2]
    s = get_sf1_series(
        symbol=symbol,
        column=column,
        dimension=dimension,
        start_date=start_date,
        end_date=end_date,
        api_key=None,
    )
    if s is not None and not s.empty:
        s.name = f"sf1:{symbol}:{dimension}:{column}"
    return s


def fetch_signal_series(
    signal: SignalDef,
    start_date: str,
    end_date: str,
) -> Optional[pd.Series]:
    if not signal.enabled:
        return None
    if signal.source == "massive":
        s = _fetch_massive_series(signal.spec, start_date, end_date)
    elif signal.source == "sf1":
        s = _fetch_sf1_series(signal.spec, start_date, end_date)
    else:
        s = None
    # Optional resample to model frequency if requested
    if s is not None and not s.empty and signal.model_freq:
        try:
            s = s.sort_index().resample(signal.model_freq).last()
        except Exception:
            # if resample fails, keep original
            pass
    return s


def build_tensor_from_signals(
    signal_ids: List[str],
    registry: Dict[str, SignalDef],
    primary_index: pd.DatetimeIndex,
    start_date: str,
    end_date: str,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Returns a DataFrame indexed by primary_index containing columns of each signal,
    time-aligned and linearly interpolated, and the list of column names.
    """
    cols: List[str] = []
    df_out = pd.DataFrame(index=primary_index)
    for sid in signal_ids:
        sig = registry.get(sid)
        if sig is None:
            continue
        s = fetch_signal_series(sig, start_date, end_date)
        if s is None or s.empty:
            continue
        s = s.sort_index().reindex(primary_index, method=None).interpolate(method="time", limit_direction="both")
        df_out[s.name] = s.astype(float).values
        cols.append(s.name)
    return df_out, cols

