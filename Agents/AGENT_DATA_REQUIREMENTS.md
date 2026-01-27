# Agent Data Requirements Guide

This guide explains how to specify data requirements for your trading agents so the system can pre-fetch all necessary data before simulation starts.

## Required Agent Attributes

Every agent must define these attributes as class properties:

### 1. Trading Symbol and Frequency

```python
class MyAgent(BaseAgent):
    def __init__(self):
        # Required: Primary trading symbol
        self.symbol = "AAPL"
        
        # Required: Timespan for primary bars
        # Options: "minute", "hour", "day", "week", "month"
        self.primary_timespan = "day"
        
        # Required: Multiplier for timespan
        # e.g., 1 for 1-day, 5 for 5-minute, 15 for 15-minute
        self.primary_multiplier = 1
```

### 2. Signal Requirements

Agents should declare all signals they need using the `used_signal_ids` attribute:

```python
class MyAgent(BaseAgent):
    def __init__(self):
        # ... symbol and frequency attributes ...
        
        # Declare all signals the agent will use
        self.used_signal_ids = [
            "SPY_day_close",       # Market benchmark
            "AAPL_arq_revenue",    # Fundamentals
            "VIX_day_close",       # Volatility index
        ]
```

### Alternative: Dynamic Signal IDs

If your agent needs to determine signals dynamically:

```python
class MyAgent(BaseAgent):
    def __init__(self):
        # ... symbol and frequency attributes ...
    
    def get_signal_ids(self) -> List[str]:
        """Return list of signal IDs this agent will use."""
        return [
            "SPY_day_close",
            "AAPL_arq_revenue",
        ]
```

## How Signal IDs Are Defined

Signal IDs must be registered in the database (table: `available_signals`) or in `data/available_signals.csv`.

### Signal ID Format

Signal IDs follow this pattern: `{identifier}_{key}`

Examples:
- `SPY_day_close` - SPY daily close price
- `AAPL_arq_revenue` - AAPL quarterly revenue
- `VIX_hour_close` - VIX hourly close

### Signal Specification

Each signal has a `source` and `spec`:

#### Massive (Price Data)
```
source: massive
spec: SYMBOL:timespan:multiplier
```

Examples:
- `SPY:day:1` - SPY daily bars
- `AAPL:minute:5` - AAPL 5-minute bars
- `VIX:hour:1` - VIX hourly bars

#### SF1 (Fundamentals)
```
source: sf1
spec: SYMBOL:dimension:column
```

Examples:
- `AAPL:ARQ:revenue` - Apple quarterly revenue
- `MSFT:MRY:netinc` - Microsoft yearly net income

Dimensions:
- `ARQ` - As Reported Quarterly
- `MRY` - Most Recent Year
- `ART` - As Reported Trailing Twelve Months

## Data Pre-fetching Process

When you start a simulation:

1. **Agent Introspection** - The system creates a probe instance of your agent and reads:
   - `symbol` - determines which ticker to backtest
   - `primary_timespan` and `primary_multiplier` - determines bar frequency
   - `used_signal_ids` or calls `get_signal_ids()` - determines additional data needs

2. **Data Fetching** - The system fetches:
   - Primary market data (OHLCV bars) for the specified symbol and frequency
   - All signals listed in `used_signal_ids` based on their specs
   - Progress updates are shown in the UI: "Loading market data..." → "Pre-fetching signal data..." → "Running simulation..."

3. **Caching** - All data is cached in memory before simulation starts, so:
   - No API calls during simulation (much faster!)
   - Consistent data for reproducibility
   - Progress bar shows loading status

## Example: Complete Agent

```python
from typing import List, Optional
from ib_backtester.engine import BaseAgent
from Common.agent_api import build_snapshot_from_signal_ids

class HybridAgent(BaseAgent):
    def __init__(self):
        # Trading symbol and frequency
        self.symbol = "AAPL"
        self.primary_timespan = "day"
        self.primary_multiplier = 1
        
        # Signal requirements
        self.used_signal_ids = [
            "SPY_day_close",      # Market context
            "AAPL_arq_revenue",   # Fundamentals
            "VIX_day_close",      # Volatility
        ]
        
        # Internal state
        self._snapshot_cache = None
    
    def on_day_start(self, ib, contract, date):
        """Fetch daily signals."""
        # Get primary history (already cached)
        history = ib.request_historical_data(
            contract=contract,
            end_datetime=date,
            duration_str='30 D',
            bar_size='1 day'
        )
        
        # Build snapshot from signal IDs (these are pre-fetched)
        tensor, names, index = build_snapshot_from_signal_ids(
            primary_history=history,
            snapshot_end=date,
            signal_ids=self.used_signal_ids,
            window_days=30
        )
        
        self._snapshot_cache = tensor
    
    def on_bar(self, ib, contract, history):
        # Use cached snapshot for decision making
        if self._snapshot_cache is None:
            return
        
        # ... your trading logic ...
```

## Chart Frequency

The candlestick chart in the UI automatically uses your agent's frequency:
- If you set `primary_timespan="minute"` and `primary_multiplier=5`
- The chart will display "5-minute" bars
- The chart title shows: "Price Chart (N bars) - minute × 5"

## Signal Registry

To add new signals, update `data/available_signals.csv` or insert into the `available_signals` table:

```csv
signal_id,source,spec,enabled
SPY_day_close,massive,SPY:day:1,1
AAPL_arq_revenue,sf1,AAPL:ARQ:revenue,1
VIX_hour_close,massive,VIX:hour:1,1
```

Or use the Signal Management tab in the React UI to add signals interactively.

## Troubleshooting

### "No data" or "Empty signal"
- Check that signal IDs are registered in `available_signals`
- Verify signal specs are correct (symbol:timespan:multiplier or symbol:dimension:column)
- Check API keys are set in `backend/.env`

### Slow simulation
- Check backend logs for timing breakdown:
  - `Data load time` - time to fetch market data
  - `Simulation time` - actual simulation runtime
- If "Data load time" is high, API is slow (network issue)
- If "Simulation time" is high, agent logic is slow

### Missing signals in chart
- Signals are not displayed on the chart by default
- Check the "Job Info" section in the dashboard to see which signals were used
- Future enhancement: overlay signals on the chart

## Best Practices

1. **Declare all signals upfront** - Don't make API calls inside `on_bar`
2. **Use daily signals when possible** - Intraday signals require more API calls
3. **Cache snapshots** - Build signal snapshots once per day, not per bar
4. **Test signal availability** - Verify signals exist before running backtest
5. **Use meaningful signal IDs** - Make them descriptive and consistent

## See Also

- `Common/agent_api.py` - Signal fetching utilities
- `Agents/instances/hybrid_encoder_decoder_agent.py` - Example agent
- `data/available_signals.csv` - Signal registry
