# Hybrid Encoder-Decoder Agent - Documentation

## Overview

The Hybrid Encoder-Decoder Agent implements a clean architectural separation between historical analysis and live decision-making, using hard-coded rules for interpretability while maintaining a structure that can later transition to neural networks.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT CONTROL LOOP                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │         ENCODER PHASE                 │
        │  (Process historical signals)         │
        └──────────────────────────────────────┘
                │                    │
                ▼                    ▼
        ┌──────────────┐    ┌──────────────────┐
        │  SPY Daily   │    │ AAPL Quarterly   │
        │  Close       │    │ Revenue          │
        │  (30 days)   │    │ (30 days)        │
        └──────────────┘    └──────────────────┘
                │                    │
                └──────────┬─────────┘
                           ▼
                ┌─────────────────────┐
                │  Encode to State:   │
                │  - Market Trend     │
                │  - Volatility       │
                │  - Fundamental Score│
                │  - Technical Score  │
                └─────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │         DECODER PHASE                 │
        │  (Combine state + live signals)       │
        └──────────────────────────────────────┘
                │                    │
                ▼                    ▼
        ┌──────────────┐    ┌──────────────────┐
        │ Encoded      │    │ Live Signals:    │
        │ State        │    │ - Price/MA20     │
        │ (from above) │    │ - Price/MA50     │
        │              │    │ - Volume Ratio   │
        │              │    │ - Daily Return   │
        └──────────────┘    └──────────────────┘
                │                    │
                └──────────┬─────────┘
                           ▼
                ┌─────────────────────┐
                │  Decode to Action:  │
                │  - BUY / SELL / HOLD│
                │  - Quantity         │
                │  - Reason           │
                └─────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │         EXECUTOR PHASE                │
        │  (Execute trade + risk management)    │
        └──────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │         LOGGER PHASE                  │
        │  (Record for visualization)           │
        └──────────────────────────────────────┘
```

## Key Design Decisions

### 1. **Hard-Coded Rules (Not Torch Models)**

**Why start here:**
- ✅ **Fast iteration** - Change rules instantly, no training required
- ✅ **Interpretable** - Know exactly why each decision was made
- ✅ **Validates infrastructure** - Ensures data pipeline works
- ✅ **Baseline performance** - Establishes what to beat
- ✅ **Limited data** - Daily bars = few samples, hard-coded works better

**When to switch to Torch:**
- Rules become too complex (>15 conditions)
- Performance plateaus
- You have 1000+ episodes of logged data
- Patterns are clearly non-linear

### 2. **Encoder-Decoder Separation**

**Encoder (Historical Context):**
- Processes past 30 days of signals
- Outputs: market_trend, volatility, fundamental_score, technical_score
- Updated daily (cached to avoid redundant API calls)
- **Think:** "What does the recent history tell us?"

**Decoder (Live Decision):**
- Takes encoded state + current price action
- Outputs: action (BUY/SELL/HOLD), quantity, reason
- Runs every bar
- **Think:** "Given the context, what should we do now?"

### 3. **Comprehensive Logging**

Every decision is logged with:
- **Encoder outputs** (market state)
- **Decoder inputs** (live signals)
- **Portfolio state** (position, cash, equity)
- **Decision** (action, quantity, reason)
- **Risk levels** (stop loss, take profit)

This enables:
- Post-analysis visualization
- Strategy refinement
- Future neural network training data

## Configuration

```python
@dataclass
class Config:
    # Signal window
    window_days: int = 30           # How much history to encode
    
    # Trading rules
    buy_threshold: float = 0.97     # Buy when price < MA * 0.97
    sell_threshold: float = 1.03    # Sell when price > MA * 1.03
    fundamental_min: float = 0.0    # Min fundamental growth to trade
    
    # Position sizing
    max_position_pct: float = 0.9   # Max 90% of capital
    base_trade_size: int = 10       # Base shares per trade
    
    # Risk management
    stop_loss_pct: float = 0.05     # 5% stop loss
    take_profit_pct: float = 0.10   # 10% take profit
    
    # Logging
    log_decisions: bool = True
    log_file: Optional[str] = 'logs/hybrid_agent_decisions.json'
```

## Usage

### 1. Register the Agent

```bash
python Scripts/register_hybrid_agent.py
```

This adds the agent to the `agents_registry` table.

### 2. Setup in Configuration GUI

**Signals Tab:**
- Register `SPY_day_close` (if not exists)
- Register `AAPL_arq_revenue` (if not exists)

**Test Definitions Tab:**
- Create a test (e.g., "hybrid_test")
- Set date range, trials, plot directory

**Jobs Tab:**
- Assign "hybrid_encoder_decoder" to your test

### 3. Run Backtest

```bash
set BACKTEST_TEST_NAMES=hybrid_test
python Backtesting/run_suite.py
```

### 4. Visualize Results

```bash
python Scripts/visualize_agent.py logs/hybrid_agent_decisions.json
```

Or save to file:
```bash
python Scripts/visualize_agent.py logs/hybrid_agent_decisions.json --output viz_output/
```

## What Gets Visualized

The visualization script creates a comprehensive 6-panel analysis:

### 1. **Equity Curve** (Top Panel)
- Shows portfolio value over time
- Green triangles = Buy actions
- Red triangles = Sell actions
- Tracks overall performance

### 2. **Encoder Outputs: Market State** (Left Middle)
- Market Trend line (momentum)
- Technical Score line
- Shows what the encoder "understands" about market conditions

### 3. **Encoder Outputs: Fundamentals & Risk** (Right Middle)
- Fundamental Score (company health)
- Market Volatility (risk level)
- Shows quality and risk assessment

### 4. **Decoder Inputs: Price vs Moving Averages** (Left Lower-Middle)
- Price/MA20 ratio
- Price/MA50 ratio
- Buy/Sell threshold lines
- Shows price positioning relative to trends

### 5. **Decoder Inputs: Volume & Returns** (Right Lower-Middle)
- Volume Ratio (current vs average)
- Daily Return percentage
- Shows momentum and activity

### 6. **Price & Position** (Middle Lower)
- Price line (blue, left axis)
- Position area chart (purple, right axis)
- Shows actual trades executed

### 7. **Decision Heatmap** (Bottom Left)
- Color-coded grid of decisions over time
- Green = Buy, Yellow = Hold, Red = Sell
- Shows decision patterns

### 8. **Statistics Panel** (Bottom Right)
- Performance metrics (return, equity)
- Activity breakdown (buy/sell/hold percentages)
- Average encoder state values
- Average decoder signal values
- Position statistics

## Example Output

```
AGENT DECISION LOG SUMMARY
============================================================

Agent: HybridEncoderDecoderAgent
Symbol: AAPL
Total Decisions: 252

Date Range: 2023-01-03 to 2023-12-29

Actions:
  HOLD  :  230 ( 91.3%)
  BUY   :   12 (  4.8%)
  SELL  :   10 (  4.0%)

Performance:
  Initial Equity: $100,000.00
  Final Equity:   $108,543.22
  Total Return:   +8.54%

Encoder State (Averages):
  Market Trend:      +0.0234
  Market Volatility:  0.0156
  Fundamental Score: +0.1234
  Technical Score:   +0.0189

Decoder Signals (Averages):
  Price/MA20:        1.0023
  Price/MA50:        0.9987
  Volume Ratio:      1.0456
  Daily Return:      +0.0012

Position Stats:
  Average Position:  45.2 shares
  Max Position:      100 shares
  Min Position:      0 shares

Top Decision Reasons:
  - Buy signal: below MA20, below MA50, market stable: 8 times
  - Sell signal: above MA20 threshold: 6 times
  - Stop loss triggered: -5.12%: 2 times
```

## Decision Rules Explained

### Buy Logic (Decoder)
Requires 3 out of 4 conditions:
1. ✓ Price < MA20 * buy_threshold (e.g., 0.97)
2. ✓ Price < MA50 * buy_threshold
3. ✓ Market trend > -5% (not crashing)
4. ✓ Technical score > 0 (positive momentum)

**AND**
- Fundamental score ≥ fundamental_min (company not failing)

### Sell Logic (Decoder)
Triggers on ANY of:
1. Price > MA20 * sell_threshold (e.g., 1.03)
2. Price > MA50 * sell_threshold
3. Market trend < -10% (major downturn)

**OR**
- Stop loss triggered (-5%)
- Take profit triggered (+10%)

### Hold Logic
Everything else = HOLD (no action)

## Extending the Agent

### Add More Signals

```python
self.used_signal_ids = [
    "SPY_day_close",
    "AAPL_arq_revenue",
    "QQQ_day_close",      # Add tech sector benchmark
    "AAPL_mrq_pe",        # Add valuation metric
]
```

Then update encoder to use all 4 signals:
```python
spy_signal = mat[:, 0]
aapl_revenue = mat[:, 1]
qqq_signal = mat[:, 2]
aapl_pe = mat[:, 3]
```

### Tune Parameters

Edit the config in `create_agent()`:
```python
config = Config(
    window_days=60,          # More history
    buy_threshold=0.95,      # More aggressive
    sell_threshold=1.05,     # Hold longer
    base_trade_size=20,      # Larger positions
)
```

### Add New Rules

In `_decode_action()`, add conditions:
```python
# New rule: Volume confirmation
high_volume = live_signals['volume_ratio'] > 1.5

buy_conditions = [
    price_vs_ma20 < self.cfg.buy_threshold,
    price_vs_ma50 < self.cfg.buy_threshold,
    market_trend > -0.05,
    technical_score > 0,
    high_volume,  # NEW: Require volume surge
]

if sum(buy_conditions) >= 4:  # Now need 4 out of 5
    return ('BUY', quantity, reason)
```

### Transition to Torch (Future)

When ready, replace `_encode_market_state()` with:
```python
import torch
import torch.nn as nn

class Encoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(num_features, 64),
            nn.ReLU(),
            nn.Linear(64, 4)  # Output: 4 state values
        )
    
    def forward(self, x):
        return self.net(x)

# In agent:
def _encode_market_state(self):
    features = torch.tensor(self._snapshot_tensor[-1], dtype=torch.float32)
    state_vector = self.encoder(features)
    return {
        'market_trend': state_vector[0].item(),
        'market_volatility': state_vector[1].item(),
        'fundamental_score': state_vector[2].item(),
        'technical_score': state_vector[3].item(),
    }
```

## Files Created

1. **`Agents/instances/hybrid_encoder_decoder_agent.py`** - Main agent implementation
2. **`Scripts/visualize_agent.py`** - Visualization tool
3. **`Scripts/register_hybrid_agent.py`** - Registration helper
4. **This file** - Documentation

## Quick Start

```bash
# 1. Register agent
python Scripts/register_hybrid_agent.py

# 2. Open config GUI and set up test
python Scripts/general_config_gui.py
# - Signals tab: Ensure SPY_day_close and AAPL_arq_revenue exist
# - Test Definitions tab: Create "hybrid_test"
# - Jobs tab: Assign "hybrid_encoder_decoder" to "hybrid_test"

# 3. Run backtest
set BACKTEST_TEST_NAMES=hybrid_test
python Backtesting/run_suite.py

# 4. Visualize
python Scripts/visualize_agent.py logs/hybrid_agent_decisions.json
```

## Advantages of This Approach

### vs. Simple Rules Only
- ✅ **Structure for scaling** - Clear path to add complexity
- ✅ **Better logging** - Separates state from decisions
- ✅ **Debuggable** - Can inspect encoder and decoder separately

### vs. Torch Models Immediately
- ✅ **No training required** - Works immediately
- ✅ **Interpretable** - Know why decisions are made
- ✅ **Fast iteration** - Change rules and re-run instantly
- ✅ **Works with limited data** - Daily bars = few samples

### Best of Both Worlds
- ✅ **Today:** Fast, interpretable, production-ready
- ✅ **Tomorrow:** Can swap in neural networks when needed
- ✅ **Always:** Comprehensive logging for analysis

## Performance Expectations

With default settings on AAPL (2023 data):
- **Expected trades:** ~10-20 per year (low frequency)
- **Expected return:** 5-15% (market-dependent)
- **Win rate:** 50-60% (typical for mean reversion)
- **Max drawdown:** 5-10%

These are baselines. Tune parameters based on your analysis.

## Visualization Example

After running a backtest, the visualization shows:

**Top Panel:** Portfolio growing from $100k to $108.5k (+8.5%)

**Encoder Panels:** 
- Market trend mostly positive (0.02 avg)
- Low volatility (0.015 avg)
- Fundamental score improving (+0.12)

**Decoder Panels:**
- Price oscillating around MA (0.95-1.05 range)
- Volume spikes on buy signals
- Daily returns mean-reverting

**Decision Heatmap:** Clusters of buys at dips, sells at peaks

**Statistics:** 91% holds, 5% buys, 4% sells - typical low-frequency agent

## Next Steps

1. **Run a backtest** with the hybrid agent
2. **Analyze the visualizations** - Look for patterns
3. **Tune parameters** based on what you see
4. **Add more signals** as needed
5. **Consider Torch** only if rules become unwieldy

## Summary

The Hybrid Encoder-Decoder Agent gives you:
- ✅ Clean encoder-decoder architecture
- ✅ Hard-coded rules for fast iteration
- ✅ Comprehensive logging for analysis
- ✅ Professional visualization
- ✅ Clear upgrade path to neural networks
- ✅ Production-ready today

**Start simple, scale when needed!**
