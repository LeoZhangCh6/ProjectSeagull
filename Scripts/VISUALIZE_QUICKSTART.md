# Visualization Script - Quick Reference

## Auto-Find Mode (Easiest!)

Just run without arguments - it will automatically find and use the most recent decision log:

```powershell
python Scripts/visualize_agent.py
```

**What it does:**
1. Searches for decision log files in:
   - `Backtesting/plots/`
   - `logs/`
   - Project root
2. Shows you the 10 most recent logs found
3. Automatically uses the newest one
4. Opens an interactive plot window

## Specify Log File

If you want to use a specific log:

```powershell
python Scripts/visualize_agent.py "path/to/agent_decisions.json"
```

## Save to File Instead of Interactive

To save as PNG instead of showing interactively:

```powershell
# Auto-find and save
python Scripts/visualize_agent.py --output viz_results/

# Specific log and save
python Scripts/visualize_agent.py "logs/my_log.json" --output viz_results/
```

## If No Logs Found

If you see "No decision log files found", you need to generate one first:

```powershell
# Run a backtest (will generate logs in Backtesting/plots/)
python Scripts/run_backtest.py
```

Then run the visualization script again - it will find the new log automatically!

## What Gets Visualized

The script creates a comprehensive 6-panel chart showing:

1. **Equity Curve** - Portfolio value over time with trade markers
2. **Encoder Signals** - Historical feature evolution
3. **Decoder Signals** - Real-time trading signals
4. **Position Over Time** - Share holdings
5. **Decision Heatmap** - Signal correlations
6. **Trade Analysis** - Performance metrics by action

Plus a detailed text summary in the console!

## Example Output

```
No log file specified. Searching for recent decision logs...

Found 2 decision log(s):

  1. logs\hybrid_agent_decisions.json
     Modified: 2024-01-25 14:23:15

Using most recent: logs\hybrid_agent_decisions.json

Loading decision log: logs\hybrid_agent_decisions.json
Loaded 156 decisions

=== Agent Performance Summary ===
Agent: HybridEncoderDecoderAgent
Symbol: SPY
...

Generating visualizations...

Showing interactive plot. Close window to exit.
```

## Troubleshooting

**"No decision log files found"**
- Run a backtest first: `python Scripts/run_backtest.py`
- Make sure your agent has decision logging enabled

**"Failed to load log file"**
- Check the JSON file is valid
- Make sure it's an agent decision log (not a different JSON)

**Plot looks weird**
- The script handles complex layouts - some warnings are normal
- Try saving to file instead: add `--output results/`
