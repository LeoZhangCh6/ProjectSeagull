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
    """
    api_key = _get_nasdaq_api_key(api_key)
    base = "https://data.nasdaq.com/api/v3/datatables/SHARADAR/SF1.json"
    # Request only needed columns and constrain date range at the API to reduce payload
    params_raw = {
        "ticker": symbol.upper(),
        "dimension": dimension.upper(),
        "qopts.columns": f"calendardate,{column}",
        "calendardate.gte": start_date,
        "calendardate.lte": end_date,
        "paginate": "true",
        "api_key": api_key,
    }
    params = {k: v for k, v in params_raw.items() if v is not None}
    resp = requests.get(base, params=params, timeout=30)
    # Handle common HTTP error cases gracefully so callers can skip unavailable signals
    if resp.status_code == 429:
        raise RuntimeError("Rate limited by Nasdaq Data Link. Please slow down or try again later.")
    if resp.status_code in (401, 403, 422):
        return None
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
        # Column might be unavailable for this ticker/dimension or not permitted by plan
        return None
    df["calendardate"] = pd.to_datetime(df["calendardate"])
    df = df.sort_values("calendardate")
    if df.empty:
        return None
    s = pd.Series(df[column].astype(float).values, index=pd.DatetimeIndex(df["calendardate"]))
    s.name = f"sf1:{symbol.upper()}:{dimension.upper()}:{column}"
    return s

