# Agent Registry Fix Summary

## Problem

When running backtests, you got the error:
```
Skipping job (quick, example_function) – agent not found in registry.
Skipping job (standard, example_function) – agent not found in registry.
```

## Root Cause

**Name mismatch between test jobs and registered agents:**

- Agent filename: `example_function_agent.py`
- Auto-registered name: `example_function_agent` (strips `.py`)
- Test job reference: `example_function` (wrong!)

## Solution

### 1. Fixed SQL Seeds

**Updated `db/initialize.sql`:**

```sql
-- Before (wrong)
INSERT INTO agents_registry (name, path, ...) VALUES
  ('example_function', 'db://agents/example_function', ...);

INSERT INTO test_jobs (test_name, agent_name) VALUES
  ('quick','example_function'),
  ('standard','example_function');

-- After (correct)
INSERT INTO agents_registry (name, path, ...) VALUES
  ('example_function_agent', 'db://agents/example_function_agent', ...);

INSERT INTO test_jobs (test_name, agent_name) VALUES
  ('quick','example_function_agent'),
  ('standard','example_function_agent');
```

### 2. Re-initialized Database

Ran `python Scripts/init_db.py` which:
1. ✅ Created database schema
2. ✅ Auto-registered all 4 agent files:
   - `copied_agent_test`
   - `copied_copied`
   - `example_function_agent` (the one we needed)
   - `hybrid_encoder_decoder_agent`
3. ✅ Uploaded code to database (3,247 - 19,834 chars each)
4. ✅ Created correct test job mappings

### 3. Verification

Created diagnostic script `Scripts/check_agents_registry.py` to verify:

```bash
python Scripts/check_agents_registry.py
```

**Output:**
```
[OK] Database connected
[OK] agents_registry table exists
[OK] code column exists

Registered agents: 4
------------------------------------------------------------
Name                           Path                      Code Status     Enabled
------------------------------------------------------------------------------------------
example_function_agent         db://agents/example_function_agent 3247 chars      [OK]
...

Test Jobs
------------------------------------------------------------
Test Name            Agent Name                     Status
------------------------------------------------------------
quick                example_function_agent         [OK]
standard             example_function_agent         [OK]

[OK] All checks passed!
```

## Files Modified

1. **`db/initialize.sql`**
   - Fixed agent registry seed name: `example_function` → `example_function_agent`
   - Fixed test_jobs references: `example_function` → `example_function_agent`

2. **`Scripts/init_db.py`**
   - Fixed Unicode characters (`✓` → `[OK]`, `✗` → `[X]`)

3. **`Scripts/check_agents_registry.py`** (new)
   - Created diagnostic tool to verify agent registration

## How Auto-Registration Works

When you run `python Scripts/init_db.py`:

```
1. Scans: Agents/instances/*.py
2. For each file:
   - Strips .py extension
   - Reads Python code
   - Uploads to agents_registry.code
   - Sets path to db://agents/{name}
3. Result: All agents registered with code in database
```

**Example:**
- File: `Agents/instances/example_function_agent.py`
- Registered as: `example_function_agent`
- Path: `db://agents/example_function_agent`
- Code: Stored in database (3,247 chars)

## Current Status

✅ **All Fixed!**

- Database initialized
- 4 agents registered with code uploaded
- Test jobs correctly reference agents
- Backtests can now run

## Quick Reference

### Check agent status
```bash
python Scripts/check_agents_registry.py
```

### Re-initialize database (safe to re-run)
```bash
python Scripts/init_db.py
```

### Run backtests
```bash
python Backtesting/run_suite.py
```

### View agents in pgAdmin
```sql
SELECT name, path, LENGTH(code) as code_size, enabled
FROM agents_registry
ORDER BY name;
```

## Lessons Learned

1. **Agent name = filename without .py**
   - `my_agent.py` → registered as `my_agent`
   - `example_function_agent.py` → registered as `example_function_agent`

2. **Test jobs must match registered names exactly**
   - Use diagnostic script to verify

3. **Unicode characters break Windows console**
   - Use ASCII: `[OK]`, `[X]`, `[!]` instead of `✓`, `✗`, `⚠`

4. **Auto-registration is powerful**
   - Scans all `.py` files
   - Uploads code automatically
   - Creates database references
   - Zero manual work needed

## Future Workflow

**When adding new agents:**

```bash
# 1. Create agent file
# (edit Agents/instances/my_new_agent.py)

# 2. Re-run initialization
python Scripts/init_db.py

# 3. Verify
python Scripts/check_agents_registry.py

# 4. Assign to test via GUI
python Scripts/general_config_gui.py
# → Jobs tab → Create new job
```

**When updating existing agents:**

```bash
# 1. Edit agent file
# (edit Agents/instances/existing_agent.py)

# 2. Re-run initialization (updates code in DB)
python Scripts/init_db.py

# 3. Run backtests
python Backtesting/run_suite.py
```

## Summary

**Problem:** Agent name mismatch  
**Root cause:** Wrong names in SQL seeds  
**Solution:** Fixed SQL, re-initialized database  
**Result:** All agents registered, backtests working  
**Time to fix:** ~5 minutes  
**Prevention:** Use diagnostic script regularly
