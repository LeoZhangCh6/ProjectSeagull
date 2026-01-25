import os
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd
import requests


def _partition_dates(start_date: str, end_date: str, chunk_days: int = 7) -> List[tuple]:
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    current = start
    ranges: List[tuple] = []
    while current <= end:
        nxt = min(current + timedelta(days=chunk_days - 1), end)
        ranges.append((current.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d")))
        current = nxt + timedelta(days=1)
    return ranges


def get_aggregate_bars(
    symbol: str,
    start_date: str,
    end_date: str,
    timespan: str = "minute",
    multiplier: int = 1,
    api_key: Optional[str] = None,
    base_url: str = "https://api.polygon.io",
    adjusted: bool = True,
) -> Optional[pd.DataFrame]:
    """
    Fetch aggregated bars from Massive (formerly Polygon.io).

    Returns DataFrame with columns:
    ['symbol','timestamp','time','timespan','open','high','low','close','volume','vwap','transactions','otc']
    """
    api_key = api_key or os.environ.get("MASSIVE_API_KEY") or os.environ.get("POLYGON_API_KEY")
    if not api_key:
        raise RuntimeError("Missing API key. Set MASSIVE_API_KEY or POLYGON_API_KEY in environment.")

    all_frames: List[pd.DataFrame] = []
    for from_, to in _partition_dates(start_date, end_date, chunk_days=7):
        url = f"{base_url}/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{from_}/{to}"
        params = {
            "adjusted": str(adjusted).lower(),
            "sort": "asc",
            "limit": 50000,
            "apiKey": api_key,
        }
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 429:
            raise RuntimeError("Rate limited by API. Please slow down or try again later.")
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            continue
        df = pd.DataFrame(results).assign(
            symbol=symbol,
            timespan=timespan,
            time=lambda _df: pd.to_datetime(_df["t"], unit="ms"),
        )
        rename_map = {
            "t": "timestamp",
            "o": "open",
            "h": "high",
            "l": "low",
            "c": "close",
            "v": "volume",
            "vw": "vwap",
            "n": "transactions",
        }
        df = df.rename(columns=rename_map)
        if "otc" not in df.columns:
            df["otc"] = False
        column_order = [
            "symbol",
            "timestamp",
            "time",
            "timespan",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "vwap",
            "transactions",
            "otc",
        ]
        df = df[column_order]
        all_frames.append(df)

    if not all_frames:
        return None
    res = pd.concat(all_frames, ignore_index=True).sort_values("timestamp").reset_index(drop=True)
    return res

