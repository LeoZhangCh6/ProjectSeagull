# General Configuration GUI - User Guide

## Overview

The General Configuration GUI is a comprehensive tool for managing all ProjectSeagull configurations through a single tabbed interface.

## Four Tabs

### 1. **Signals Tab** - Manage Trading Signals
Register and manage signals from market data and fundamentals.

**Features:**
- Add signals from Massive (Polygon.io) or SF1 (Sharadar)
- Auto-validation with API
- Auto-generated signal IDs and model frequencies
- View all registered signals

**Workflow:**
1. Select data source (massive or sf1)
2. Enter symbol ticker
3. Configure parameters (timespan/field or dimension/column)
4. Optional: add description
5. Click "Validate & Register Signal"

**Example:**
- Source: massive
- Symbol: SPY
- Timespan: day, Multiplier: 1, Field: close
- → Creates: `SPY_day_close` with spec `SPY:day:1:close`

### 2. **Test Definitions Tab** - Create Test Configurations
Define backtest parameters and date ranges.

**Fields:**
- **Test Name*** - Unique identifier for the test
- **Trials*** - Number of random windows to test
- **Start/End Date*** - Overall date range for sampling
- **Seed** - Random seed for reproducibility
- **Record Curves** - Save equity curves for analysis
- **Plot Directory** - Where to save output charts (click "Browse..." to select)
- **Warmup Days** - Days for agent initialization
- **Trading Days** - Duration of each test window

**Workflow:**
1. Enter test name (e.g., "quick", "standard", "monthly_2024")
2. Set number of trials
3. Specify date range
4. Configure options (seed, curves, plot dir)
   - Click "Browse..." to select plot directory
5. Set warmup and trading days
6. Click "Create Test Definition"

**Example:**
```
Name: my_test
Trials: 5
Start: 2023-01-01
End: 2023-12-31
Seed: 42
Plot Dir: C:\backtest_output (click "Browse..." to select)
Warmup: 14 days
Trading: 30 days
```

### 3. **Jobs Tab** - Assign Agents to Tests
Create and manage test jobs (which agent runs on which test).

**Features:**
- Assign any agent to any test definition
- View all current job assignments
- Delete unused jobs
- Refresh lists to load latest tests/agents

**Workflow:**
1. Click "Refresh Lists" to load tests and agents
2. Select a test definition from dropdown
3. Select an agent from dropdown
4. Click "Create Job"
5. Job appears in the list below

**Example:**
```
Test: quick → Agent: example_function
Test: standard → Agent: my_new_agent
Test: monthly_2024 → Agent: example_function
```

### 4. **Agent Builder Tab** - Create and Register Agents
Build new agents by registering existing files or cloning and customizing agents.

**Two Sub-Tabs:**

#### 4a. Register Agent
Register an existing Python file as an agent.

**Features:**
- Browse and select agent .py files
- Validate agent structure and syntax
- Register agent in database
- View all registered agents

**Workflow:**
1. Click "Browse..." to select agent file
2. Agent name auto-fills from filename (editable)
3. Add optional description
4. Click "Validate & Register Agent"
   - Automatically validates structure and syntax
   - Only registers if validation passes
   - Shows detailed validation results
5. Agent appears in "Registered Agents" list

**Validation Checks:**
- File readability
- `create_agent()` function exists
- Inherits from `BaseAgent`
- Required methods: `on_start`, `on_bar`, `on_end`
- Has `used_signal_ids` (optional)
- Has `symbol` declaration (optional)
- Python syntax validity

**Example:**
```
File: C:\...\Agents\instances\my_agent.py
Name: my_agent (auto-filled)
Description: Custom trading strategy for TSLA

[Validate & Register Agent] -> 
  - Validates structure
  - Shows validation results
  - Registers if validation passes
  - Agent added to database
```

#### 4b. Clone & Customize
Create a new agent by cloning an existing one with modifications.

**Features:**
- Clone any registered agent
- Auto-detect signals and symbol
- Substitute signals with different ones
- Change trading symbol
- Preview changes before creating
- Automatically register cloned agent

**Workflow:**
1. **Select Source:**
   - Choose agent from dropdown
   - Click "Load Agent"
   - Original signals appear in list

2. **Customize:**
   - Enter new agent name
   - (Optional) Change trade symbol
   - Add signal substitutions:
     - Select signal from "Original Signals" list
     - Choose replacement from "Replace with" dropdown
     - Click "Add Substitution"
   - Add description

3. **Create:**
   - Click "Preview Changes" to review
   - Click "Create & Register Agent" to save

**Example - Clone AAPL agent for TSLA:**
```
Step 1: Select Source
  Source Agent: hybrid_encoder_decoder
  [Load Agent] -> Detects: SPY_day_close, AAPL_arq_revenue

Step 2: Customize
  New Name: hybrid_tsla_agent
  Trade Symbol: TSLA
  
  Signal Substitutions:
    - Select from list: AAPL_arq_revenue
    - Replace with: TSLA_arq_revenue [from dropdown]
    - [Add Substitution]
  
  Substitutions list shows:
    AAPL_arq_revenue -> TSLA_arq_revenue
  
  Description: Hybrid agent for Tesla

Step 3: Create
  [Preview Changes] -> Shows modified code
  [Create & Register Agent] -> Creates:
    - File: Agents/instances/hybrid_tsla_agent.py
    - Database entry with name "hybrid_tsla_agent"
```

**Use Cases:**
- **Quick symbol changes:** Clone agent, change symbol, swap symbol-specific signals
- **Multi-symbol testing:** Create variants of same strategy for different stocks
- **Signal experimentation:** Test different signal combinations without manual editing
- **Template reuse:** Keep base agent intact, create customized versions

## Launch the Tool

### Windows
```bash
Scripts\launch_config_gui.bat
```

### Command Line
```bash
python Scripts/general_config_gui.py
```

## Prerequisites

- `DATABASE_URL` or `PGHOST` environment variable set
- API keys (for signal validation):
  - `MASSIVE_API_KEY` for Polygon data
  - `NASDAQ_DATA_LINK_API_KEY` for SF1 data

## Complete Workflow Example

### Scenario: Set up a new backtest

#### Step 1: Register Signals (Signals Tab)
```
1. Register SPY benchmark:
   - Source: massive
   - Symbol: SPY
   - Timespan: day, Multiplier: 1, Field: close
   - Result: SPY_day_close

2. Register AAPL fundamentals:
   - Source: sf1
   - Symbol: AAPL
   - Dimension: ARQ, Column: revenue
   - Result: AAPL_arq_revenue
```

#### Step 2: Create Test Definition (Test Definitions Tab)
```
Name: my_backtest
Trials: 10
Start Date: 2023-01-01
End Date: 2023-12-31
Seed: 42
Record Curves: ✓
Plot Dir: C:\backtest_output
Warmup Days: 14
Trading Days: 30
```

#### Step 3: Create Job (Jobs Tab)
```
1. Refresh Lists
2. Select Test: my_backtest
3. Select Agent: example_function
4. Create Job
```

#### Step 4: Run the Backtest
```bash
# Set test name to run
set BACKTEST_TEST_NAMES=my_backtest

# Run suite
python Backtesting/run_suite.py
```

## Database Tables

The GUI manages these tables:

### available_signals
```sql
CREATE TABLE available_signals (
  id text PRIMARY KEY,
  source text NOT NULL,
  spec text NOT NULL,
  model_freq text,
  description text,
  enabled boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  last_access_time timestamptz
);
```

### test_definitions
```sql
CREATE TABLE test_definitions (
  name text PRIMARY KEY,
  trials integer NOT NULL,
  overall_start_date date NOT NULL,
  overall_end_date date NOT NULL,
  seed integer,
  record_curves boolean DEFAULT false,
  plot_dir text,
  warmup_days integer DEFAULT 14,
  trading_days integer DEFAULT 14,
  created_at timestamptz DEFAULT now()
);
```

### test_jobs
```sql
CREATE TABLE test_jobs (
  test_name text REFERENCES test_definitions(name),
  agent_name text REFERENCES agents_registry(name),
  created_at timestamptz DEFAULT now(),
  PRIMARY KEY (test_name, agent_name)
);
```

## Tips

### Signals
- Use descriptive symbols (SPY, AAPL, etc.)
- Validate before registering to avoid bad data
- Signal IDs are auto-generated and deterministic
- View existing signals to avoid duplicates

### Test Definitions
- Use clear, descriptive test names
- Set appropriate warmup days for your strategy
- Trading days determine window length
- More trials = more statistical confidence
- Record curves for detailed analysis

### Jobs
- One agent can run on multiple tests
- One test can have multiple agents
- Delete unused jobs to keep things clean
- Refresh lists after adding new tests/agents

## Troubleshooting

### "Database connection not configured"
- Set `DATABASE_URL` or `PGHOST` environment variable
- Example: `set DATABASE_URL=postgresql://user:pass@localhost:5432/db`

### "Symbol not found"
- Check that the ticker is correct
- Ensure API keys are configured
- Try a different date range (some symbols have limited history)

### "Test name already exists"
- The GUI will update the existing test (upsert)
- Or choose a different name

### "Foreign key violation" (Jobs)
- Ensure the test definition exists
- Ensure the agent is registered in agents_registry
- Click "Refresh Lists" to reload

## Keyboard Shortcuts

- **Tab**: Navigate between fields
- **Enter**: Submit form (in some fields)
- **Ctrl+Tab**: Switch between tabs
- **Esc**: Close popup windows

## Advanced Usage

### Bulk Operations

For bulk operations, use SQL directly:

```sql
-- Create multiple test definitions
INSERT INTO test_definitions (name, trials, overall_start_date, overall_end_date, warmup_days, trading_days)
VALUES
  ('test_2022', 10, '2022-01-01', '2022-12-31', 14, 30),
  ('test_2023', 10, '2023-01-01', '2023-12-31', 14, 30),
  ('test_2024', 10, '2024-01-01', '2024-12-31', 14, 30);

-- Assign one agent to all tests
INSERT INTO test_jobs (test_name, agent_name)
SELECT name, 'my_agent'
FROM test_definitions
WHERE name LIKE 'test_%';
```

### Export Configuration

```sql
-- Export signals
COPY (SELECT * FROM available_signals) TO '/tmp/signals.csv' CSV HEADER;

-- Export test definitions
COPY (SELECT * FROM test_definitions) TO '/tmp/tests.csv' CSV HEADER;

-- Export jobs
COPY (SELECT * FROM test_jobs) TO '/tmp/jobs.csv' CSV HEADER;
```

## Summary

The General Configuration GUI provides a unified interface for managing:
1. **Signals** - Data sources for your agents
2. **Test Definitions** - Backtest configurations  
3. **Jobs** - Agent-test assignments
4. **Agent Builder** - Create and register agents (new!)

All changes are saved to PostgreSQL and immediately available for use in backtests and live trading.

**Launch:** `python Scripts/general_config_gui.py`
