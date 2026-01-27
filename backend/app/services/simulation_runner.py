"""Simulation runner service that wraps the backtesting engine."""

import asyncio
import os
import sys
import time
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from fastapi import WebSocket
from starlette.websockets import WebSocketState

# Ensure project root is in path
_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_HERE)
_BACKEND_DIR = os.path.dirname(_APP_DIR)
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_BACKTESTING_DIR = os.path.join(_PROJECT_ROOT, "Backtesting")
if _BACKTESTING_DIR not in sys.path:
    sys.path.insert(0, _BACKTESTING_DIR)

from Common.db import get_pg_conn
from Common.agents_loader import get_agent_factory_from_registry_db
from Common.massive_client import get_aggregate_bars
from Backtesting.ib_backtester.suite import load_test_definitions_db, load_test_jobs_db
from Backtesting.ib_backtester.engine import IBBacktestEnv, BaseAgent

from app.services.job_manager import simulation_sessions

# Configuration for streaming
STREAM_EVERY_N_BARS = 50  # Only send update every N bars (reduces WebSocket overhead)


async def safe_send_json(websocket: WebSocket, data: dict) -> bool:
    """Safely send JSON data, returns False if connection is closed."""
    try:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json(data)
            return True
    except Exception as e:
        print(f"[WebSocket] Send failed: {e}")
    return False


class StreamingAgent(BaseAgent):
    """Wrapper agent that intercepts on_bar calls to stream data."""
    
    def __init__(self, inner_agent: BaseAgent, callback, stream_every_n: int = STREAM_EVERY_N_BARS):
        self.inner = inner_agent
        self.callback = callback
        self.stream_every_n = stream_every_n
        self.bar_count = 0
        self.last_stream_time = 0
        
        # Copy attributes from inner agent
        for attr in ['symbol', 'primary_timespan', 'primary_multiplier']:
            if hasattr(inner_agent, attr):
                setattr(self, attr, getattr(inner_agent, attr))
    
    def on_start(self, ib, contract):
        return self.inner.on_start(ib, contract)
    
    def on_day_start(self, ib, contract, date):
        if hasattr(self.inner, 'on_day_start'):
            return self.inner.on_day_start(ib, contract, date)
    
    def on_bar(self, ib, contract, history):
        self.bar_count += 1
        
        # Send update every N bars
        if self.callback and self.bar_count % self.stream_every_n == 0 and len(history) > 0:
            bar = history.iloc[-1]
            portfolio = ib.get_portfolio_state()
            
            self.callback({
                "bar_index": len(history) - 1,
                "bar": {
                    "timestamp": int(bar.get("timestamp", 0)),
                    "time": str(bar.get("time", "")),
                    "open": float(bar.get("open", 0)),
                    "high": float(bar.get("high", 0)),
                    "low": float(bar.get("low", 0)),
                    "close": float(bar.get("close", 0)),
                    "volume": float(bar.get("volume", 0)),
                },
                "equity": portfolio.get("equity", 0),
                "position": portfolio.get("position", 0),
                "cash": portfolio.get("cash", 0),
            })
        
        return self.inner.on_bar(ib, contract, history)
    
    def on_end(self, ib, contract):
        # Send final update
        if self.callback:
            try:
                portfolio = ib.get_portfolio_state()
                self.callback({
                    "bar_index": self.bar_count - 1,
                    "bar": None,  # No bar data, just final state
                    "equity": portfolio.get("equity", 0),
                    "position": portfolio.get("position", 0),
                    "cash": portfolio.get("cash", 0),
                })
            except Exception:
                pass
        return self.inner.on_end(ib, contract)


def run_single_job(
    test_name: str,
    agent_name: str,
    bar_callback,
    progress_callback,
) -> Dict[str, Any]:
    """Run a single job and call callback for each bar."""
    
    start_time = time.time()
    print(f"[Job] Starting: {test_name} / {agent_name}")
    
    # Load test definition
    test_defs = load_test_definitions_db([test_name])
    if not test_defs:
        return {"error": f"Test '{test_name}' not found"}
    
    cfg = test_defs[0]
    print(f"[Job] Test config: {cfg.overall_start_date} to {cfg.overall_end_date}, {cfg.trading_days} trading days")
    
    # Get agent factory
    try:
        agent_factory = get_agent_factory_from_registry_db(agent_name)
    except Exception as e:
        return {"error": f"Agent '{agent_name}' not found: {e}"}
    
    # Create agent probe to introspect requirements
    agent_probe = agent_factory()
    
    # Get symbol from agent
    symbol = getattr(agent_probe, "symbol", None)
    if symbol is None and hasattr(agent_probe, "get_symbol"):
        try:
            symbol = agent_probe.get_symbol()
        except Exception:
            symbol = None
    if symbol is None:
        symbol = os.environ.get("BACKTEST_SYMBOL")
    if not symbol:
        return {"error": "Agent must define a trading symbol"}
    
    timespan = getattr(agent_probe, "primary_timespan", "minute")
    multiplier = int(getattr(agent_probe, "primary_multiplier", 1))
    
    # Extract signal requirements from agent
    signal_ids = []
    if hasattr(agent_probe, "used_signal_ids"):
        signal_ids = agent_probe.used_signal_ids
    elif hasattr(agent_probe, "get_signal_ids") and callable(agent_probe.get_signal_ids):
        try:
            signal_ids = agent_probe.get_signal_ids()
        except Exception:
            signal_ids = []
    
    print(f"[Job] Symbol: {symbol}, Timespan: {timespan}, Multiplier: {multiplier}")
    print(f"[Job] Signal IDs required: {signal_ids}")
    
    # Validate date range
    import pandas as pd
    start_dt = pd.to_datetime(cfg.overall_start_date)
    end_dt = pd.to_datetime(cfg.overall_end_date)
    
    if start_dt >= end_dt:
        error_msg = (
            f"Invalid date range: start_date ({cfg.overall_start_date}) "
            f"must be before end_date ({cfg.overall_end_date}). "
            f"Please update your test definition to use a valid date range."
        )
        print(f"[Job] ERROR: {error_msg}")
        progress_callback(error_msg, 100)
        return {"error": error_msg}
    
    days_diff = (end_dt - start_dt).days
    if days_diff < 7:
        error_msg = (
            f"Date range too short: {days_diff} days. "
            f"Need at least 7 calendar days (to ensure some trading days). "
            f"Current range: {cfg.overall_start_date} to {cfg.overall_end_date}"
        )
        print(f"[Job] WARNING: {error_msg}")
        progress_callback(error_msg, 100)
        return {"error": error_msg}
    
    # Step 1: Create environment (this fetches market data)
    try:
        progress_callback("Loading market data...", 10)
        env_start = time.time()
        
        print(f"[Job] Fetching market data:")
        print(f"[Job]   Symbol: {symbol}")
        print(f"[Job]   Dates: {cfg.overall_start_date} to {cfg.overall_end_date} ({days_diff} days)")
        print(f"[Job]   Timespan: {timespan} × {multiplier}")
        
        env = IBBacktestEnv(
            symbol=str(symbol),
            start_date=str(cfg.overall_start_date),
            end_date=str(cfg.overall_end_date),
            timespan=str(timespan),
            multiplier=int(multiplier),
            initial_cash=100000.0,
            commission_rate=0.0005,
        )
        
        env_time = time.time() - env_start
        print(f"[Job] Market data loaded in {env_time:.2f}s, {len(env.data)} bars")
        progress_callback(f"Market data loaded ({len(env.data)} bars)", 30)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        # Provide helpful error messages
        suggestions = []
        if "No data returned" in str(e):
            suggestions.append("Check that the date range includes trading days (not just weekends/holidays)")
            suggestions.append("Verify the symbol exists and has data in that period")
            suggestions.append("Ensure MASSIVE_API_KEY is set in backend/.env")
        
        error_msg = (
            f"Failed to load market data for {symbol} "
            f"({cfg.overall_start_date} to {cfg.overall_end_date}, {timespan}×{multiplier}). "
            f"Error: {e}"
        )
        if suggestions:
            error_msg += "\n\nSuggestions:\n- " + "\n- ".join(suggestions)
        
        print(f"[Job] ERROR: {error_msg}")
        progress_callback("Data loading failed", 100)
        return {"error": error_msg}
    
    # Step 2: Pre-fetch all signal data
    try:
        progress_callback("Pre-fetching signal data...", 40)
        prefetch_start = time.time()
        
        if signal_ids:
            print(f"[Job] Pre-fetching {len(signal_ids)} signals...")
            
            # Parse signals from database registry
            from Common.signals_manager import load_available_signals
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            default_csv = os.path.join(repo_root, "data", "available_signals.csv")
            registry = load_available_signals(default_csv, update_access_time=False)
            
            # Pre-fetch each signal based on its spec
            fetched_count = 0
            for sig_id in signal_ids:
                if sig_id not in registry:
                    print(f"[Job] Warning: Signal '{sig_id}' not found in registry")
                    continue
                
                sig = registry[sig_id]
                # SignalDef is a dataclass/object, access attributes directly
                source = getattr(sig, "source", "")
                spec = getattr(sig, "spec", "")
                
                try:
                    if source == "massive" and spec:
                        # Parse spec: "SYMBOL:timespan:multiplier[:field]"
                        # Example: "SPY:day:1:close" or "SPY:day:1"
                        parts = spec.split(":")
                        if len(parts) >= 1:
                            sig_symbol = parts[0]
                            sig_timespan = parts[1] if len(parts) > 1 else "day"
                            sig_multiplier = int(parts[2]) if len(parts) > 2 else 1
                            # parts[3] is the field (close, open, etc.) - not used in fetching
                            
                            progress_callback(f"Fetching {sig_id}...", 40 + (fetched_count * 15 // len(signal_ids)))
                            
                            df = get_aggregate_bars(
                                symbol=sig_symbol,
                                start_date=str(cfg.overall_start_date),
                                end_date=str(cfg.overall_end_date),
                                timespan=sig_timespan,
                                multiplier=sig_multiplier,
                            )
                            if df is not None and not df.empty:
                                print(f"[Job]   ✓ {sig_id}: {len(df)} bars")
                                fetched_count += 1
                            
                    elif source == "sf1" and spec:
                        # Parse spec: "SYMBOL:dimension:column"
                        parts = spec.split(":")
                        if len(parts) >= 3:
                            from Common.sharadar_client import get_sf1_series
                            
                            progress_callback(f"Fetching {sig_id}...", 40 + (fetched_count * 15 // len(signal_ids)))
                            
                            sig_symbol = parts[0]
                            dimension = parts[1]
                            column = parts[2]
                            
                            s = get_sf1_series(
                                symbol=sig_symbol,
                                column=column,
                                dimension=dimension,
                                start_date=str(cfg.overall_start_date),
                                end_date=str(cfg.overall_end_date),
                                api_key=None,
                            )
                            if s is not None and not s.empty:
                                print(f"[Job]   ✓ {sig_id}: {len(s)} points")
                                fetched_count += 1
                
                except Exception as e:
                    print(f"[Job]   ✗ {sig_id}: {e}")
            
            print(f"[Job] Pre-fetched {fetched_count}/{len(signal_ids)} signals")
        
        prefetch_time = time.time() - prefetch_start
        print(f"[Job] Signal data pre-fetched in {prefetch_time:.2f}s")
        progress_callback("All data loaded", 60)
        
    except Exception as e:
        print(f"[Job] Warning: Pre-fetch signals failed: {e}")
        import traceback
        traceback.print_exc()
        # Continue anyway, agent will fetch on-demand
        progress_callback("Running simulation...", 70)
    
    # Step 3: Run simulation with cached data
    try:
        progress_callback("Running simulation...", 70)
        sim_start = time.time()
        
        # Create fresh agent with streaming wrapper
        inner_agent = agent_factory()
        streaming_agent = StreamingAgent(inner_agent, bar_callback)
        
        print(f"[Job] Starting simulation...")
        curve = env.run(streaming_agent, trading_days=cfg.trading_days)
        
        sim_time = time.time() - sim_start
        print(f"[Job] Simulation completed in {sim_time:.2f}s, {len(curve)} bars processed")
        progress_callback("Simulation complete", 100)
        
        # Get final trades
        trades = [
            {
                "timestamp": t.timestamp,
                "action": t.action.value,
                "quantity": t.quantity,
                "price": t.price,
            }
            for t in env.broker.trades
        ]
        
        # Send all bars for chart display
        all_bars = []
        if len(env.data) > 0:
            for idx, row in env.data.iterrows():
                bar_data = {
                    "timestamp": int(row.get("timestamp", 0)),
                    "time": str(row.get("time", "")),
                    "open": float(row.get("open", 0)),
                    "high": float(row.get("high", 0)),
                    "low": float(row.get("low", 0)),
                    "close": float(row.get("close", 0)),
                    "volume": float(row.get("volume", 0)),
                }
                all_bars.append(bar_data)
        
        total_time = time.time() - start_time
        print(f"[Job] Total time: {total_time:.2f}s (Data: {env_time:.2f}s, Simulation: {sim_time:.2f}s)")
        
        return {
            "success": True,
            "final_equity": float(curve["equity"].iloc[-1]) if len(curve) > 0 else 100000.0,
            "trades": trades,
            "total_bars": len(curve),
            "all_bars": all_bars,  # Include all bars for chart
            "execution_time_seconds": total_time,
            "data_load_time_seconds": env_time,
            "simulation_time_seconds": sim_time,
            "chart_frequency": {
                "timespan": timespan,
                "multiplier": multiplier,
            },
            "signal_ids": signal_ids,
            "symbol": str(symbol),  # Trading symbol
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Simulation failed: {e}"}


async def run_simulation_async(
    session_id: str,
    websocket: WebSocket,
    job_ids: Optional[List[str]] = None,
    test_names: Optional[List[str]] = None,
):
    """Run simulation asynchronously and stream results via WebSocket."""
    
    # Helper to check if still connected
    def is_connected():
        return websocket.client_state == WebSocketState.CONNECTED
    
    # Load jobs from database
    try:
        jobs = load_test_jobs_db(test_names)
    except Exception as e:
        await safe_send_json(websocket, {
            "type": "error",
            "message": f"Failed to load jobs: {e}"
        })
        return
    
    if not jobs:
        await safe_send_json(websocket, {
            "type": "error",
            "message": "No jobs found"
        })
        return
    
    print(f"[Simulation] Starting {len(jobs)} jobs")
    
    # Update session
    simulation_sessions[session_id] = {
        "status": "running",
        "jobs_total": len(jobs),
        "jobs_completed": 0,
    }
    
    await safe_send_json(websocket, {
        "type": "status",
        "status": "started",
        "jobs_total": len(jobs),
    })
    
    # Run jobs sequentially with progress updates
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=1)
    
    should_stop = False
    
    for job_index, (test_name, agent_name) in enumerate(jobs):
        if should_stop or not is_connected():
            break
        
        job_id = f"{test_name}_{agent_name}"
        
        if not await safe_send_json(websocket, {
            "type": "job_start",
            "job_id": job_id,
            "job_index": job_index,
            "test_name": test_name,
            "agent_name": agent_name,
        }):
            should_stop = True
            break
        
        # Queue for streaming bar data
        bar_queue = asyncio.Queue()
        progress_queue = asyncio.Queue()
        
        def bar_callback(data):
            if not should_stop:
                try:
                    loop.call_soon_threadsafe(bar_queue.put_nowait, data)
                except Exception:
                    pass
        
        def progress_callback(message: str, percent: int):
            if not should_stop:
                try:
                    loop.call_soon_threadsafe(progress_queue.put_nowait, (message, percent))
                except Exception:
                    pass
        
        # Start streaming tasks
        async def stream_bars():
            nonlocal should_stop
            while not should_stop and is_connected():
                try:
                    data = await asyncio.wait_for(bar_queue.get(), timeout=0.5)
                    if data.get("bar") is not None:  # Skip final update with no bar
                        if not await safe_send_json(websocket, {
                            "type": "bar_update",
                            "job_id": job_id,
                            "job_index": job_index,
                            "test_name": test_name,
                            "agent_name": agent_name,
                            **data
                        }):
                            should_stop = True
                            break
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break
        
        async def stream_progress():
            nonlocal should_stop
            while not should_stop and is_connected():
                try:
                    message, percent = await asyncio.wait_for(progress_queue.get(), timeout=0.5)
                    await safe_send_json(websocket, {
                        "type": "progress",
                        "job_id": job_id,
                        "job_index": job_index,
                        "message": message,
                        "percent": percent,
                    })
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break
        
        # Start tasks
        stream_task = asyncio.create_task(stream_bars())
        progress_task = asyncio.create_task(stream_progress())
        
        try:
            result = await loop.run_in_executor(
                executor,
                run_single_job,
                test_name,
                agent_name,
                bar_callback,
                progress_callback,
            )
        finally:
            # Cancel tasks
            stream_task.cancel()
            progress_task.cancel()
            try:
                await stream_task
            except asyncio.CancelledError:
                pass
            try:
                await progress_task
            except asyncio.CancelledError:
                pass
        
        # Send job completion
        if is_connected():
            await safe_send_json(websocket, {
                "type": "job_complete",
                "job_id": job_id,
                "job_index": job_index,
                "test_name": test_name,
                "agent_name": agent_name,
                "result": result
            })
    
    # Update session
    simulation_sessions[session_id]["status"] = "completed"
    simulation_sessions[session_id]["jobs_completed"] = len(jobs)
    
    # Send completion
    if is_connected():
        await safe_send_json(websocket, {
            "type": "status",
            "status": "completed",
            "jobs_total": len(jobs),
            "jobs_completed": len(jobs),
        })
    
    executor.shutdown(wait=False)
    print(f"[Simulation] Completed")
