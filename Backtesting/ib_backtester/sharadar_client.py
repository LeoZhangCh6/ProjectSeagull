import os
from typing import Optional

import pandas as pd
import requests


def _get_nasdaq_api_key(explicit: Optional[str] = None) -> Optional[str]:
    if explicit:
        return explicit
    return (
        os.environ.get("NASDAQ_DATA_LINK_API_KEY")
        or os.environ.get("NASDAQ_API_KEY")
        or os.environ.get("QUANDL_API_KEY")
        or None
    )


def get_sf1_series(
    symbol: str,
    column: str,
    dimension: str,
    start_date: str,
    end_date: str,
    api_key: Optional[str] = None,
) -> Optional[pd.Series]:
    """
    Fetch a single SF1 fundamental column for a ticker/dimension from Nasdaq Data Link
    (Sharadar SF1 datatable) and return as a Series indexed by calendardate.

    Parameters
    ----------
    symbol : str
        Ticker symbol (e.g., 'AAPL')
    column : str
        SF1 column name (e.g., 'revenue', 'pe', 'assets', etc.)
    dimension : str
        One of ARQ/MRQ/ARY/MRY (quarterly/yearly, as-reported/most-recent)
    start_date, end_date : str
        YYYY-MM-DD boundaries; results will be filtered to this range
    api_key : Optional[str]
        If not provided, tries NASDAQ_DATA_LINK_API_KEY / NASDAQ_API_KEY / QUANDL_API_KEY env vars
    """
    api_key = _get_nasdaq_api_key(api_key)
    base = "https://data.nasdaq.com/api/v3/datatables/SHARADAR/SF1.json"
    params = {
        "ticker": symbol.upper(),
        "dimension": dimension.upper(),
        "api_key": api_key,
        "paginate": "true",
    }
    resp = requests.get(base, params=params, timeout=30)
    if resp.status_code == 429:
        raise RuntimeError("Rate limited by Nasdaq Data Link. Please slow down or try again later.")
    resp.raise_for_status()
    payload = resp.json()
    data = payload.get("datatable", {}).get("data", [])
    columns = payload.get("datatable", {}).get("columns", [])
    if not data or not columns:
        return None
    col_names = [c.get("name") for c in columns]
    df = pd.DataFrame(data, columns=col_names)
    if "calendardate" not in df.columns:
        return None
    if column not in df.columns:
        raise ValueError(f"SF1 column '{column}' not found in response.")
    df["calendardate"] = pd.to_datetime(df["calendardate"])
    df = df.sort_values("calendardate")
    # Filter date range
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    df = df[(df["calendardate"] >= start_dt) & (df["calendardate"] <= end_dt)]
    if df.empty:
        return None
    s = pd.Series(df[column].astype(float).values, index=pd.DatetimeIndex(df["calendardate"]))
    s.name = f"sf1:{symbol.upper()}:{dimension.upper()}:{column}"
    return s

