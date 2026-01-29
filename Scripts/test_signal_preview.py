#!/usr/bin/env python3
"""Test script to check signal preview functionality."""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, "backend", ".env"))

from Common.db import get_pg_conn

print("=== Available Signals ===")
with get_pg_conn() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT id, source, spec, model_freq FROM available_signals LIMIT 10")
        rows = cur.fetchall()
        for row in rows:
            print(f"  ID: {row[0]}, Source: {row[1]}, Spec: {row[2]}, Freq: {row[3]}")

print("\n=== Testing Signal Preview ===")
# Test with first massive signal
with get_pg_conn() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT id, source, spec FROM available_signals WHERE source = 'massive' LIMIT 1")
        row = cur.fetchone()

if row:
    signal_id, source, spec = row
    print(f"Testing signal: {signal_id} (spec: {spec})")
    
    # Parse spec
    parts = spec.split(":")
    symbol = parts[0]
    timespan = parts[1] if len(parts) > 1 else "day"
    multiplier = int(parts[2]) if len(parts) > 2 else 1
    field = parts[3] if len(parts) > 3 else "close"
    
    print(f"  Symbol: {symbol}, Timespan: {timespan}, Multiplier: {multiplier}, Field: {field}")
    
    try:
        from Common.massive_client import get_aggregate_bars
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"  Fetching data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
        
        df = get_aggregate_bars(
            symbol=symbol,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            timespan=timespan,
            multiplier=multiplier,
        )
        
        if df is None:
            print("  ERROR: get_aggregate_bars returned None")
        elif df.empty:
            print("  ERROR: get_aggregate_bars returned empty DataFrame")
        else:
            print(f"  SUCCESS: Got {len(df)} rows")
            print(f"  Columns: {list(df.columns)}")
            print(f"  Last 5 {field} values: {df[field].tail(5).tolist()}")
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
else:
    print("No massive signals found in database")
