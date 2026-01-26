# Enhanced Database Initialization - Auto-Register Agents

## What's New

The `init_db.py` script now automatically registers ALL agent files from `Agents/instances/` directory with their code uploaded to the database.

## How It Works

### Initialization Process

```
Step 1: Run SQL schema
   ↓
Create tables: available_signals, agents_registry, test_definitions, test_jobs
   ↓
Seed default data (signals, test definitions)
   ↓
Step 2: Auto-register agents
   ↓
Scan Agents/instances/*.py
   ↓
For each .py file:
  - Read Python code
  - Upload to agents_registry.code
  - Set path to db://agents/{name}
  - Set description
   ↓
Done! All agents registered
```

### What Gets Registered

**Directory scanned:** `Agents/instances/`

**Files included:**
- ✅ All `.py` files
- ✅ Code uploaded to database
- ✅ Path set to `db://agents/{name}`
- ✅ Auto-generated description

**Files excluded:**
- ✗ `__init__.py` (special file)
- ✗ Files starting with `_` (private/special)
- ✗ Non-Python files

## Usage

### For New Installation

```bash
# 1. Set database connection
set DATABASE_URL=postgresql://user:pass@localhost:5432/seagull

# 2. Run initialization
python Scripts/init_db.py
```

**Output:**
```
============================================================
ProjectSeagull Database Initialization
============================================================

Connecting to Postgres...
Running SQL initialization script...
✓ Database schema and default data created

Registering 3 agent files from ...\Agents\instances...
  ✓ Registered: example_function_agent (db://agents/example_function_agent)
  ✓ Registered: hybrid_encoder_decoder_agent (db://agents/hybrid_encoder_decoder_agent)
  ✓ Registered: multi_source_model_agent (db://agents/multi_source_model_agent)

Agent registration complete:
  Registered: 3
  Skipped: 0

============================================================
Database initialized successfully!
============================================================
```

### For Existing Installation

If you already have a database and just want to re-register agents:

```bash
# Option 1: Re-run full initialization (safe with ON CONFLICT)
python Scripts/init_db.py

# Option 2: Use the Agent Builder GUI
python Scripts/general_config_gui.py
# → Agent Builder → Register Agent → Browse each file
```

## Database Path Format

All auto-registered agents use the database path format:

```
db://agents/{agent_name}
```

**Examples:**
- `db://agents/example_function_agent`
- `db://agents/hybrid_encoder_decoder_agent`
- `db://agents/my_custom_agent`

This indicates the agent code is stored in the database, not in a file.

## Agent Table After Initialization

```sql
SELECT name, path, LENGTH(code) as code_size, description
FROM agents_registry;
```

**Result:**
```
name                          | path                                    | code_size | description
------------------------------+-----------------------------------------+-----------+-----------------------------------
example_function_agent        | db://agents/example_function_agent      | 3456      | Auto-registered from example_function_agent.py
hybrid_encoder_decoder_agent  | db://agents/hybrid_encoder_decoder_agent| 15234     | Auto-registered from hybrid_encoder_decoder_agent.py
multi_source_model_agent      | db://agents/multi_source_model_agent    | 8901      | Auto-registered from multi_source_model_agent.py
```

## Benefits

### 1. Zero Manual Setup
- No need to register agents one by one
- All existing agents automatically available
- Fresh installations ready immediately

### 2. Consistent State
- Database and filesystem in sync
- All agents have code in database
- No missing code issues

### 3. Easy Onboarding
- New team members: Just run `init_db.py`
- All agents ready to use
- No manual configuration needed

### 4. Development Workflow
```
1. Create new agent → Save to Agents/instances/my_agent.py
2. Re-run init_db.py (or use GUI to register)
3. Agent available in database
4. Ready for backtesting
```

## Code Details

### Agent Scanning Logic

```python
def register_all_agent_files(conn, root):
    """Scan and register all agent files."""
    agents_dir = os.path.join(root, "Agents", "instances")
    agent_files = glob.glob(os.path.join(agents_dir, "*.py"))
    
    for filepath in agent_files:
        filename = os.path.basename(filepath)
        agent_name = os.path.splitext(filename)[0]
        
        # Skip special files
        if filename.startswith('_'):
            continue
        
        # Read code
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Insert into database
        cur.execute("""
            INSERT INTO agents_registry (name, path, code, description, enabled)
            VALUES (%s, %s, %s, %s, true)
            ON CONFLICT (name) DO UPDATE
            SET path = EXCLUDED.path,
                code = EXCLUDED.code,
                description = EXCLUDED.description
        """, (agent_name, f"db://agents/{agent_name}", code, f"Auto-registered from {filename}"))
```

### Upsert Behavior

**ON CONFLICT (name) DO UPDATE:**
- If agent already exists → Updates code and path
- If agent is new → Inserts new record
- **Safe to re-run** - Won't create duplicates

## Workflow Examples

### Example 1: Fresh Installation

```bash
# Clone repository
git clone <repo>
cd ProjectSeagull

# Set up database
set DATABASE_URL=postgresql://user:pass@localhost:5432/seagull

# Initialize (includes agents!)
python Scripts/init_db.py

# Check results
python Scripts/general_config_gui.py
# → Agent Builder → Register Agent → View list
# All agents already there!
```

### Example 2: Add New Agent

```bash
# Create new agent
# (Edit Agents/instances/my_new_agent.py)

# Re-run initialization
python Scripts/init_db.py
# → Automatically picks up new agent
# → Uploads code to database

# Or use GUI
python Scripts/general_config_gui.py
# → Agent Builder → Register Agent → Browse file
```

### Example 3: Update Existing Agent

```bash
# Modify agent code
# (Edit Agents/instances/existing_agent.py)

# Option 1: Re-run init
python Scripts/init_db.py
# → Updates code in database

# Option 2: Use GUI
python Scripts/general_config_gui.py
# → Agent Builder → Register Agent → Browse file
# → ON CONFLICT updates existing record
```

## Verification

### Check registered agents

```sql
-- In pgAdmin or psql
SELECT 
    name,
    path,
    LENGTH(code) as code_length,
    description,
    enabled
FROM agents_registry
ORDER BY name;
```

### Verify code is uploaded

```sql
-- Check which agents have code
SELECT 
    name,
    path,
    CASE 
        WHEN code IS NULL THEN 'No code (legacy)'
        WHEN LENGTH(code) > 0 THEN 'Code stored (' || LENGTH(code) || ' chars)'
        ELSE 'Empty code'
    END as code_status
FROM agents_registry;
```

### View agent code

```sql
-- See full Python code for an agent
SELECT code
FROM agents_registry
WHERE name = 'hybrid_encoder_decoder_agent';
```

## Comparison

### Before (Manual Registration)

```bash
# 1. Initialize database
python Scripts/init_db.py

# 2. Manually register each agent
python Scripts/register_agent1.py
python Scripts/register_agent2.py
python Scripts/register_agent3.py

# OR use GUI for each agent
python Scripts/general_config_gui.py
# → Browse, validate, register (repeat 10x)

Time: 5-10 minutes
```

### After (Automatic Registration)

```bash
# 1. Initialize database (includes agents!)
python Scripts/init_db.py

Time: 30 seconds
Result: All agents registered with code uploaded!
```

## Files Modified

1. **`Scripts/init_db.py`** - Added `register_all_agent_files()` function
2. **`db/initialize.sql`** - Updated agent seed comment

## Error Handling

### If agent file has errors

```
Registering 3 agent files...
  ✓ Registered: good_agent
  ✗ Error registering bad_agent.py: invalid syntax (line 45)
  ✓ Registered: another_agent

Agent registration complete:
  Registered: 2
  Skipped: 1
```

**Result:**
- Good agents registered
- Bad agents skipped
- Initialization continues
- Fix errors and re-run

### If no agents found

```
No agent files found in Agents/instances/
```

**Result:**
- Database still initialized
- Tables created
- Default data seeded
- Add agents later via GUI

## Summary

**Enhanced initialization now:**
- ✅ Creates database schema
- ✅ Seeds default data
- ✅ **Automatically registers ALL agents**
- ✅ **Uploads code to database**
- ✅ Creates database path references
- ✅ Ready for immediate use

**Benefits:**
- Zero manual agent setup
- Fresh installations ready instantly
- All agents in database with code
- Consistent state guaranteed
- Re-runnable (safe upserts)

**Usage:**
```bash
python Scripts/init_db.py
```

**Result:** Complete database setup including all agents! 🚀
