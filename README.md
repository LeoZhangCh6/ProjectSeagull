# ProjectSeagull
Algorithmic trading platform for backtesting and executing orders from trading strategies

## 📚 Documentation

**→ [Complete Setup & Usage Guide](SETUP_GUIDE.md)** - Everything you need to know!

## Quick Links
- [Database Setup](#database-setup)
- [Configuration GUI](#configuration-gui)
- [Running Backtests](#running-backtests)

## Database Setup

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set database connection
$env:DATABASE_URL = "postgresql://user:pass@localhost:5432/seagull"
$env:MASSIVE_API_KEY = "your_polygon_api_key"
$env:NASDAQ_DATA_LINK_API_KEY = "your_nasdaq_key"

# 3. Initialize database
python Scripts/init_db.py
```

**What this does:**
- ✅ Creates database schema (signals, agents, tests, jobs)
- ✅ Seeds default data
- ✅ **Auto-registers all agents** from `Agents/instances/`
- ✅ **Uploads agent code** to database
- ✅ Ready to run backtests!

**Verification:**
```bash
python Common/check_agents_registry.py
```

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions.

## Configuration GUI

Launch the all-in-one configuration interface:

```bash
python Scripts/general_config_gui.py
# OR: Scripts\launch_config_gui.bat
```

**Four Modules:**

1. **📡 Signal Matrix** - Register trading signals from Massive/SF1
2. **🧪 Test Protocols** - Create backtest configurations
3. **⚙️ Job Scheduler** - Assign agents to tests
4. **🤖 Agent Factory** - Register & clone agents

**Key Features:**
- ✅ Auto-validation of symbols and signals
- ✅ Clone agents with signal substitution
- ✅ Create agent variants in 2 minutes
- ✅ Visual browsing of agents, tests, and jobs

**Example workflows:**
- Register new signals → Create test → Assign agent → Run backtest
- Clone agent for new symbol → Test on multiple timeframes
- Build agent portfolio (AAPL, TSLA, MSFT variants)

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed usage instructions.

## Running Backtests

```bash
# Run all configured test jobs
python Scripts/run_backtest.py

# Run specific tests
$env:BACKTEST_TEST_NAMES="my_test,quick"
python Scripts/run_backtest.py
```

**What happens:**
1. Loads test definitions from database
2. Loads test jobs (agent-test pairs)
3. Loads agents from database (code column)
4. Runs backtests with configured parameters
5. Generates reports and plots

**View results:**
- Logs in `logs/` directory
- Plots in configured plot directory
- JSON decision logs (if agent implements logging)

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete workflow and troubleshooting.

---

## Project Structure

```
ProjectSeagull/
├── Agents/instances/      # Agent Python files
├── Backtesting/          # Backtest engine
├── Common/               # Shared utilities, DB access
├── Scripts/              # Tools (GUI, init, visualize)
├── db/initialize.sql    # Database schema
├── README.md            # This file
└── SETUP_GUIDE.md       # Complete documentation
```

## Quick Reference

```bash
# Setup
python Scripts/init_db.py                    # Initialize database
python Common/check_agents_registry.py       # Verify setup

# Configure
python Scripts/general_config_gui.py         # Launch GUI

# Test
python Scripts/run_backtest.py              # Run backtests

# Monitor
python Scripts/view_signal_usage.py         # Signal usage stats
```

## Getting Help

- **Complete guide**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Hybrid agent template**: [Agents/instances/HYBRID_AGENT_GUIDE.md](Agents/instances/HYBRID_AGENT_GUIDE.md)
- **Troubleshooting**: See SETUP_GUIDE.md → Troubleshooting section

---

**Ready to trade! 🚀**