# Agent Builder Tab - Usage Examples

## Quick Reference

The Agent Builder tab has two powerful features:

1. **Register Agent** - Add existing Python files to the agent registry
2. **Clone & Customize** - Create variants of existing agents with different symbols/signals

## Example 1: Register an Existing Agent

### Scenario
You've manually created a new agent file and want to register it.

### Steps
1. Open Configuration GUI → Agent Builder tab → "Register Agent" sub-tab
2. Click "Browse..." and select your agent file:
   - `C:\...\ProjectSeagull\Agents\instances\my_momentum_agent.py`
3. Agent name auto-fills: `my_momentum_agent`
4. Add description: "Momentum strategy with RSI confirmation"
5. Click "Validate & Register Agent"
6. System validates structure, then registers if validation passes
7. Agent appears in "Registered Agents" list
8. Ready to use in Jobs tab!

### Validation Output
```
VALIDATION RESULTS
============================================================

Passed Checks:
  [OK] File is readable
  [OK] Found create_agent() function
  [OK] References BaseAgent
  [OK] Found methods: on_start, on_bar, on_end
  [OK] Declares used_signal_ids
  [OK] Declares symbol
  [OK] Python syntax is valid

CONCLUSION: Agent appears valid and ready to register.
```

## Example 2: Clone Agent for Different Symbol

### Scenario
You have a working AAPL agent and want to create a TSLA version.

### Steps

**Step 1: Load Source Agent**
1. Open "Clone & Customize" sub-tab
2. Select "hybrid_encoder_decoder" from dropdown
3. Click "Load Agent"
4. System detects:
   - Symbol: AAPL
   - Signals: SPY_day_close, AAPL_arq_revenue

**Step 2: Configure New Agent**
1. New Agent Name: `hybrid_tsla_agent`
2. Trade Symbol: `TSLA`
3. Click "Load Available Signals" to populate dropdown

**Step 3: Substitute Signals**
1. In "Replace" field: `AAPL_arq_revenue`
2. In "With" dropdown: select `TSLA_arq_revenue`
3. Click "Add Substitution"
4. Substitution appears in list: `AAPL_arq_revenue -> TSLA_arq_revenue`

**Step 4: Create**
1. Click "Preview Changes" to review
2. Click "Create & Register Agent"
3. Success! New files created:
   - `Agents/instances/hybrid_tsla_agent.py`
   - Database entry added

**Result:**
You now have two agents:
- `hybrid_encoder_decoder` - trades AAPL
- `hybrid_tsla_agent` - trades TSLA (same strategy)

## Example 3: Test Multiple Signal Combinations

### Scenario
You want to test 3 different fundamental signals for AAPL to see which performs best.

### Agents to Create
1. `aapl_revenue_agent` - uses revenue signal
2. `aapl_earnings_agent` - uses earnings signal
3. `aapl_fcf_agent` - uses free cash flow signal

### Process

**For each variant:**

1. **Select Source:** `hybrid_encoder_decoder`
2. **Load Agent**
3. **Configure:**
   - Name: `aapl_earnings_agent` (example)
   - Symbol: `AAPL` (keep same)
   - Replace: `AAPL_arq_revenue`
   - With: `AAPL_arq_netinc` (earnings)
   - Description: "AAPL agent using earnings signal"
4. **Create & Register**

**Repeat for FCF variant:**
- Replace: `AAPL_arq_revenue` → With: `AAPL_arq_fcf`

**Result:**
Three agents ready for backtesting! Create a single test definition and assign all three agents to it in the Jobs tab.

## Example 4: Create Multi-Symbol Portfolio

### Scenario
Create agents for 5 tech stocks using the same strategy.

### Stocks
- AAPL, MSFT, GOOGL, AMZN, TSLA

### Quick Process

For each stock:
1. Clone source agent
2. New name: `hybrid_{symbol}_agent`
3. Change symbol to target stock
4. Replace company-specific signals (revenue, earnings, etc.)
5. Create & register

### Time Saved
- Manual: ~30 minutes per agent × 5 = 2.5 hours
- With GUI: ~3 minutes per agent × 5 = 15 minutes

**Result:**
Five agents ready to trade different symbols with consistent strategy logic!

## Example 5: Validation Catches Errors

### Scenario
You try to register a broken agent file.

### Agent Issues
```python
# Missing imports
# No create_agent() function
# Syntax error on line 45

class MyAgent(BaseAgent):
    def on_bar(self, ib, contract, history)
        # Missing colon ^
        pass
```

### Validation Output
```
VALIDATION RESULTS
============================================================

Passed Checks:
  [OK] File is readable
  [OK] References BaseAgent
  [OK] Found methods: on_bar

Issues Found:
  [WARNING] No create_agent() function found (required)
  [WARNING] Missing methods: on_start, on_end
  [ERROR] Syntax error at line 45: invalid syntax

CONCLUSION: Agent has errors. Please fix before registering.
```

### Action
Fix the issues in your editor, then try to register again. The combined validation will prevent registration until all errors are fixed!

## Tips & Best Practices

### Registration
- **Validation is automatic** - No need for separate validate step
- **Use descriptive names** - `momentum_spy_agent` not `agent1`
- **Add descriptions** - Helps remember what each agent does
- **Keep files in Agents/instances/** - Standard location
- **Fix errors before success** - Registration blocked until validation passes

### Cloning
- **Preview before creating** - Verify changes look correct
- **Test signal availability** - Ensure replacement signals exist in database
- **Use meaningful names** - Include symbol/strategy in name
- **Document substitutions** - Note what signals were changed

### Signal Substitution
- **Load available signals first** - Populates dropdown with valid options
- **Match signal types** - Don't replace price signal with fundamental
- **Check timeframes** - Ensure replacement signal has compatible frequency
- **Test one substitution** - Verify it works before making multiple changes

### Common Patterns

**Pattern 1: Symbol Variants**
```
Base: strategy_spy_agent
Clone: strategy_qqq_agent, strategy_dia_agent
Change: Only symbol and symbol-specific signals
```

**Pattern 2: Signal Experiments**
```
Base: agent_with_revenue
Clone: agent_with_earnings, agent_with_fcf
Change: Only fundamental signal
```

**Pattern 3: Timeframe Variants**
```
Base: daily_momentum_agent
Clone: hourly_momentum_agent, weekly_momentum_agent
Change: All signals to different timeframe
```

## Troubleshooting

### "File not found" after registration
- Ensure file is in project directory
- Use relative paths (Agents/instances/...)
- Check file wasn't moved after registration

### "Agent name already exists"
- Choose a different name, or
- Overwrite existing (ON CONFLICT DO UPDATE)

### Preview shows no changes
- Verify you added substitutions
- Check symbol was entered
- Reload source agent

### Cloned agent doesn't work
- Validate the original agent first
- Ensure replacement signals exist
- Check signal substitutions were correct
- Review preview before creating

## Advanced: Manual Editing After Clone

After cloning, you can manually edit the generated file for more complex changes:

1. Clone agent to create base file
2. Open `Agents/instances/{new_agent}.py` in editor
3. Make advanced modifications:
   - Adjust trading logic
   - Add new methods
   - Modify configuration
4. Save file
5. Re-register if needed (GUI will update database)

This workflow gives you:
- ✅ Fast initial setup (clone)
- ✅ Full control (manual editing)
- ✅ Easy registration (GUI)

## Summary

The Agent Builder tab makes it easy to:

1. **Register agents** - Validate and add to database
2. **Clone agents** - Create variants quickly
3. **Substitute signals** - Test different data sources
4. **Change symbols** - Multi-symbol testing
5. **Validate structure** - Catch errors before runtime

**Time savings:** What used to take 30-60 minutes per agent variant now takes 2-3 minutes!

**Use it for:** Multi-symbol testing, signal experimentation, quick prototyping, portfolio strategies.
