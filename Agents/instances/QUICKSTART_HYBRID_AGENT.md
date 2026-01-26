# Hybrid Encoder-Decoder Agent - Quick Start

## What You Got

A production-ready trading agent with:
- ✅ **Encoder-Decoder architecture** (structured for future scaling)
- ✅ **Hard-coded rules** (fast, interpretable, no training needed)
- ✅ **Comprehensive logging** (every decision tracked)
- ✅ **Professional visualization** (6-panel analysis dashboard)

## 5-Minute Setup

### Step 1: Register Agent (30 seconds)

```bash
python Scripts/register_hybrid_agent.py
```

Output:
```
✓ Successfully registered agent: hybrid_encoder_decoder
```

### Step 2: Configure in GUI (2 minutes)

```bash
python Scripts/general_config_gui.py
```

**Signals Tab** (ensure these exist):
- `SPY_day_close` - Market benchmark
- `AAPL_arq_revenue` - Company fundamentals

**Test Definitions Tab**:
- Name: `hybrid_test`
- Trials: `3`
- Start: `2023-01-01`
- End: `2023-12-31`
- Warmup: `14`, Trading: `30`
- Click "Create Test Definition"

**Jobs Tab**:
- Test: `hybrid_test`
- Agent: `hybrid_encoder_decoder`
- Click "Create Job"

### Step 3: Run Backtest (2 minutes)

```bash
set BACKTEST_TEST_NAMES=hybrid_test
python Backtesting/run_suite.py
```

### Step 4: Visualize (30 seconds)

```bash
python Scripts/visualize_agent.py logs/hybrid_agent_decisions.json
```

**Result:** Beautiful 6-panel dashboard showing:
- Equity progression
- Encoder outputs (market state)
- Decoder inputs (live signals)
- Price & position
- Decision heatmap
- Performance statistics

## How It Works

### Information Flow

```
Historical Data (30 days)
    ↓
ENCODER: Compute market context
    ├─ Market trend
    ├─ Volatility
    ├─ Fundamental score
    └─ Technical score
    ↓
Current Bar Data
    ↓
DECODER: Combine context + live data
    ├─ Price vs MA20/MA50
    ├─ Volume ratio
    └─ Daily return
    ↓
DECISION: Apply rules
    ├─ BUY if price < MA * 0.97 (+ conditions)
    ├─ SELL if price > MA * 1.03 (or risk triggers)
    └─ HOLD otherwise
    ↓
EXECUTE: Place order
    ↓
LOG: Record everything for analysis
```

### Default Strategy

**Buy when (3+ conditions met):**
- ✓ Price < 0.97 * MA20
- ✓ Price < 0.97 * MA50
- ✓ Market not crashing (trend > -5%)
- ✓ Positive technical score

**Sell when (any condition):**
- ✗ Price > 1.03 * MA20
- ✗ Price > 1.03 * MA50
- ✗ Market downturn (trend < -10%)
- ✗ Stop loss (-5%)
- ✗ Take profit (+10%)

**Position sizing:**
- Base: 10 shares per trade
- Max: 90% of capital
- Risk: 5% stop loss, 10% take profit

## Customization

### Change Trading Rules

Edit `Agents/instances/hybrid_encoder_decoder_agent.py`:

```python
def create_agent() -> BaseAgent:
    config = Config(
        buy_threshold=0.95,    # More aggressive (was 0.97)
        sell_threshold=1.05,   # Hold longer (was 1.03)
        base_trade_size=20,    # Larger positions (was 10)
        stop_loss_pct=0.03,    # Tighter stop (was 0.05)
    )
    return HybridEncoderDecoderAgent(config)
```

### Add More Signals

```python
self.used_signal_ids = [
    "SPY_day_close",
    "AAPL_arq_revenue",
    "QQQ_day_close",      # NEW: Tech sector
    "AAPL_mrq_pe",        # NEW: Valuation
]
```

Register new signals in GUI first!

### Change Symbol

```python
self.symbol = "TSLA"  # Trade Tesla instead
self.used_signal_ids = [
    "SPY_day_close",
    "TSLA_arq_revenue",  # Update to TSLA signals
]
```

## Analysis Workflow

1. **Run backtest** → Get results
2. **Visualize** → Identify patterns
3. **Tune parameters** → Improve strategy
4. **Re-run** → Validate improvements
5. **Repeat**

### Questions to Ask

Looking at the visualization:

**Equity curve:**
- Is return consistent or volatile?
- Where are the drawdowns?

**Encoder outputs:**
- Does market_trend predict good trades?
- Is volatility useful?

**Decoder inputs:**
- Are MA crossovers good signals?
- Do volume spikes help?

**Decision heatmap:**
- Are there patterns in when you trade?
- Do you trade too much or too little?

## When to Use Torch

Switch to neural networks when:

1. **Rules become complex** (>15 conditions)
2. **Performance plateaus** (can't improve with simple rules)
3. **Have lots of data** (1000+ logged decisions)
4. **See non-linear patterns** (visualization shows complex relationships)

**Until then:** Hard-coded rules are faster, more interpretable, and easier to debug.

## Files

- **Agent**: `Agents/instances/hybrid_encoder_decoder_agent.py`
- **Visualizer**: `Scripts/visualize_agent.py`
- **Registration**: `Scripts/register_hybrid_agent.py`
- **Docs**: `Agents/instances/HYBRID_AGENT_GUIDE.md` (full guide)

## Summary

You now have:
1. ✅ **Production-ready agent** with encoder-decoder architecture
2. ✅ **Hard-coded rules** for fast iteration
3. ✅ **Comprehensive logging** capturing all decisions
4. ✅ **Professional visualization** for analysis
5. ✅ **Clear upgrade path** to neural networks

**Recommendation:** Run this for a few weeks/months, analyze the logs, tune the rules, and only consider neural networks if you hit a performance ceiling.

---

**Launch:** `python Scripts/register_hybrid_agent.py` to get started!
