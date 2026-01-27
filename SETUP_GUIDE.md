# ProjectSeagull - Complete Setup & Usage Guide

Complete guide for setting up, configuring, and using the ProjectSeagull trading system.

---

## Table of Contents

1. [Database Setup](#database-setup)
2. [Configuration GUI](#configuration-gui)
3. [Agent Management](#agent-management)
4. [Signal Tracking](#signal-tracking)
5. [Running Backtests](#running-backtests)

---

## Database Setup

### Initial Setup

```bash
# Set environment variables
$env:DATABASE_URL="postgresql://user:pass@localhost:5432/seagull"
$env:MASSIVE_API_KEY="your_polygon_api_key"
$env:NASDAQ_DATA_LINK_API_KEY="your_nasdaq_key"

# Initialize database
python Scripts/init_db.py
```

### What Initialization Does

The `init_db.py` script performs:

1. **Creates database schema**
   - `available_signals` - Signal definitions
   - `agents_registry` - Agent registration with code storage
   - `test_definitions` - Backtest configurations
   - `test_jobs` - Agent-test assignments

2. **Seeds default data**
   - Example signals (SPY, QQQ, AAPL)
   - Test definitions (quick, standard)
   - Default test jobs

3. **Auto-registers all agents**
   - Scans `Agents/instances/*.py`
   - Uploads Python code to database
   - Creates database path references (`db://agents/{name}`)
   - Ready for immediate use!

**Output:**
```
============================================================
ProjectSeagull Database Initialization
============================================================

Connecting to Postgres...
Running SQL initialization script...
[OK] Database schema and default data created

Registering 4 agent files from Agents\instances...
  [OK] Registered: example_function_agent (db://agents/example_function_agent)
  [OK] Registered: hybrid_encoder_decoder_agent (db://agents/hybrid_encoder_decoder_agent)

Agent registration complete:
  Registered: 4
  Skipped: 0

============================================================
Database initialized successfully!
============================================================
```

### Verification

Check your setup:
```bash
python Common/check_agents_registry.py
```

Shows:
- Database connection status
- Registered agents with code size
- Test jobs validation
- Missing references (if any)

---

## Configuration GUI

### Launch

```bash
python Scripts/general_config_gui.py
# OR
Scripts\launch_config_gui.bat  (Windows)
```

### Four Main Tabs

#### 1. 📡 Signal Matrix

**Register trading signals from market data sources**

- **Data Sources**: Massive (Polygon.io), SF1 (Sharadar)
- **Features**:
  - Auto-validates symbols via API
  - Auto-generates signal IDs
  - Auto-matches model frequency to timespan
  - Tests data availability on registration

**Example: Register SPY daily close**
1. Select source: "massive"
2. Enter symbol: "SPY"
3. Select timespan: "day", multiplier: 1, field: "close"
4. Click "Register Signal"

**Result:** Signal `SPY_day_close` registered and ready to use!

#### 2. 🧪 Test Protocols

**Create backtest configurations**

- Define test name, trials, date ranges
- Configure trading days
- Set plot directories (with file browser)
- Enable/disable equity curve recording

**Example: Create test**
```
Name: my_test
Trials: 5
Start: 2023-01-01
End: 2023-12-31
Trading Days: 14
```

#### 3. ⚙️ Job Scheduler

**Assign agents to tests**

- Select test definition
- Select agent
- Create job (agent will run on that test)
- View/delete existing jobs

**Example:**
```
Test: my_test
Agent: example_function_agent
→ Creates job that runs example_function_agent on my_test
```

#### 4. 🤖 Agent Factory

**Two sub-tabs for agent management**

##### Register Agent Tab

**Register existing Python agent files**

1. Browse to agent file (`.py`)
2. Name auto-filled from filename
3. Add description (optional)
4. Click "Validate & Register Agent"

**Validation checks:**
- File readability
- `create_agent()` function exists
- `BaseAgent` inheritance
- Required methods (`on_start`, `on_bar`, `on_end`)
- Python syntax
- Signal declarations
- Symbol declarations

**On success:**
- ✅ Code uploaded to database
- ✅ Backup saved to `Agents/instances/`
- ✅ Database path: `db://agents/{name}`
- ✅ Ready for backtesting!

##### Clone & Customize Tab

**Clone existing agents with modifications**

1. Select source agent to clone
2. Click "Load Agent" (shows detected signals/symbol)
3. Enter new agent name
4. (Optional) Change trading symbol
5. (Optional) Substitute signals:
   - Select signal from "Original Signals" list
   - Choose replacement from dropdown
   - Click "Add Substitution"
6. Preview changes
7. Click "Create & Register Agent"

**Result:**
- ✅ Local file created: `Agents/instances/{new_name}.py`
- ✅ Code uploaded to database
- ✅ Registered and ready to use!

**Example: Clone for different symbol**
```
Source: example_function_agent (trades SPY)
New name: example_function_qqq
New symbol: QQQ
→ Creates agent that trades QQQ instead of SPY
```

---

## Agent Management

### How Agents Are Stored

**Database-First Architecture:**

1. **Agent code stored in PostgreSQL** (`agents_registry.code` column)
2. **Database path format**: `db://agents/{agent_name}`
3. **Local backups** in `Agents/instances/` for editing
4. **Runtime loading** from database (5x faster)

### Agent Lifecycle

```
1. Create/Edit → agents/instances/my_agent.py
2. Register → GUI or init_db.py
3. Upload → Code stored in database
4. Execute → Loaded from database at runtime
```

### Updating Agents

**Option 1: Re-register via GUI**
```
Agent Factory → Register Agent → Browse file → Register
(ON CONFLICT updates existing agent)
```

**Option 2: Re-run initialization**
```bash
python Scripts/init_db.py
(Updates all agents in Agents/instances/)
```

### Agent Requirements

All agents must:
- Inherit from `BaseAgent`
- Implement `create_agent()` factory function
- Define `on_start()`, `on_bar()`, `on_end()` methods
- Declare `self.symbol` (trading symbol)
- Declare `self.used_signal_ids` (optional, for tracking)

### Trading Constraints

The backtesting engine enforces these rules:
- **No short selling**: Agents cannot sell shares they don't hold
- **Position validation**: SELL orders are rejected if quantity exceeds current position
- **Order rejection**: Invalid orders are logged with warnings and not executed

Agents should check `ib.get_portfolio_state()['position']` before placing sell orders.

---

## Signal Tracking

### Automatic Usage Tracking

The system tracks which signals are actively used by agents.

**How it works:**
1. Agent declares `self.used_signal_ids = ['signal_1', 'signal_2']`
2. On agent initialization, `last_access_time` updated in database
3. Query signals table to see usage patterns

### View Signal Usage

```bash
python Scripts/view_signal_usage.py

# With custom staleness threshold
python Scripts/view_signal_usage.py --stale-days 30
```

**Output shows:**
- **Active signals** (used recently)
- **Stale signals** (not used in 90+ days)
- **Never used signals**
- **Recommendations** for cleanup

**Example:**
```
Total Signals: 10
  Active (used in last 90 days): 6
  Stale (not used in 90+ days): 2
  Never Used: 2

ACTIVE SIGNALS
Signal ID                      Source    Last Used
---------------------------------------------------
SPY_day_close                  massive   2 days ago
AAPL_arq_revenue              sf1       1 week ago

STALE SIGNALS
Signal ID                      Source    Last Used
---------------------------------------------------
OLD_signal                     massive   4 months ago

RECOMMENDATIONS
Consider reviewing 4 unused signals:
  - Check if they're still needed
  - Disable or delete
```

### Managing Unused Signals

```sql
-- Disable signal
UPDATE available_signals SET enabled=false WHERE id='old_signal';

-- Delete signal
DELETE FROM available_signals WHERE id='old_signal';
```

---

## Running Backtests

### Via Command Line

```bash
# Run all test jobs
python Scripts/run_backtest.py

# Run specific tests
$env:BACKTEST_TEST_NAMES="my_test,quick"
python Scripts/run_backtest.py
```

### What Happens

1. **Loads test definitions** from database
2. **Loads test jobs** (agent-test pairs)
3. **Loads agents** from database (uses `code` column)
4. **Runs backtests** with specified parameters
5. **Generates reports** and plots (if configured)

### Test Configuration

Configured in GUI (Test Protocols tab) or SQL:
```sql
INSERT INTO test_definitions (name, trials, overall_start_date, overall_end_date, ...)
VALUES ('my_test', 5, '2023-01-01', '2023-12-31', ...);
```

### Job Assignment

Configured in GUI (Job Scheduler tab) or SQL:
```sql
INSERT INTO test_jobs (test_name, agent_name)
VALUES ('my_test', 'my_agent');
```

---

## Quick Reference

### Common Commands

```bash
# Database
python Scripts/init_db.py                    # Initialize database
python Common/check_agents_registry.py       # Check agent status

# GUI
python Scripts/general_config_gui.py         # Launch config GUI
Scripts\launch_config_gui.bat               # Windows launcher

# Signals
python Scripts/view_signal_usage.py         # View signal usage

# Backtesting
python Scripts/run_backtest.py             # Run backtests

# Visualization
python Scripts/visualize_agent.py logs/decisions.json  # Visualize agent
```

### File Locations

```
Project Root/
├── Agents/instances/          # Agent Python files (local backups)
├── Backtesting/              # Backtest engine
├── Common/                   # Shared utilities, DB access
├── Scripts/                  # Tools and utilities
│   ├── init_db.py           # Database initialization
│   ├── general_config_gui.py # Main configuration GUI
│   ├── view_signal_usage.py # Signal usage viewer
│   └── visualize_agent.py   # Agent visualization
├── db/initialize.sql        # Database schema
└── README.md               # Project overview
```

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
MASSIVE_API_KEY=your_polygon_api_key
NASDAQ_DATA_LINK_API_KEY=your_nasdaq_key

# Optional (for backtesting)
BACKTEST_TEST_NAMES=test1,test2    # Run specific tests
BACKTEST_SYMBOL=SPY                # Override symbol
BACKTEST_TIMESPAN=minute           # Override timespan
```

---

## Troubleshooting

### "Agent not found in registry"

```bash
# Check agent status
python Common/check_agents_registry.py

# If agent missing, re-register
python Scripts/init_db.py
```

### "Signal not found"

Check signal exists:
```sql
SELECT * FROM available_signals WHERE id='signal_id';
```

Register via GUI (Signal Matrix tab) if missing.

### Database connection issues

```bash
# Test connection
psql $DATABASE_URL

# Check environment variable
echo $env:DATABASE_URL
```

### GUI won't launch

```bash
# Check tkinter installed
python -c "import tkinter"

# Run with error output
python Scripts/general_config_gui.py
```

---

## Best Practices

### Agent Development

1. **Start with template** (e.g., `example_function_agent.py`)
2. **Test locally** before registering
3. **Use clone feature** for variations
4. **Document** signal usage in code
5. **Register early** to catch validation errors
6. **Check position before selling** - Agents cannot sell shares they don't hold (short selling is not allowed)

### Signal Management

1. **Descriptive IDs** (e.g., `SPY_day_close` not `signal1`)
2. **Regular cleanup** (review stale signals monthly)
3. **Test data availability** before relying on signal
4. **Document** in description field

### Database Management

1. **Backup regularly** (`pg_dump`)
2. **Run migrations** before updates
3. **Check status** after major changes
4. **Re-initialize** if corrupted (non-production)

### Testing Workflow

1. **Create test definition** (small date range first)
2. **Assign single agent** (test one at a time)
3. **Run backtest** (`BACKTEST_TEST_NAMES=test_name`)
4. **Review results** before scaling up
5. **Iterate** with cloned agents

---

## Summary

**Complete workflow from scratch:**

```bash
# 1. Setup database
python Scripts/init_db.py

# 2. Verify setup
python Common/check_agents_registry.py

# 3. Configure (via GUI)
python Scripts/general_config_gui.py
# → Register signals
# → Create test definitions
# → Assign agents to tests

# 4. Run backtests
python Scripts/run_backtest.py

# 5. Monitor signal usage
python Scripts/view_signal_usage.py

# 6. Iterate (create new agents, tests, etc.)
```

**You're ready to trade! 🚀**
