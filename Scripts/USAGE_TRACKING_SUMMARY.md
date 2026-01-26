# Signal Usage Tracking - Implementation Complete

## ✅ What Was Implemented

I've added automatic signal usage tracking to ProjectSeagull so you can identify which signals are actively used and clean up unused ones.

## 🎯 Key Features

### 1. **Automatic Timestamp Tracking**
- Every time an agent constructor declares signals, `last_access_time` is automatically updated
- No code changes needed in existing agents
- Tracks at the signal level, not per-use

### 2. **Database Schema Addition**
- Added `last_access_time timestamptz` column to `available_signals` table
- NULL = never used
- Timestamp = last time an agent accessed this signal

### 3. **Usage Statistics Viewer**
- New script: `view_signal_usage.py`
- Shows Active/Stale/Never Used signals
- Configurable stale threshold
- Provides cleanup recommendations

### 4. **Migration Script**
- New script: `migrate_add_last_access_time.py`
- Adds column to existing databases
- Safe to run multiple times
- Checks if already migrated

## 📁 Files Modified

### Core System
1. **`db/initialize.sql`** - Added `last_access_time` column to schema
2. **`Common/signals_manager.py`** - Added timestamp update logic
3. **`Common/agent_api.py`** - Enabled tracking in `build_snapshot_from_signal_ids()`

### New Scripts
4. **`Scripts/migrate_add_last_access_time.py`** - Migration for existing databases
5. **`Scripts/view_signal_usage.py`** - Usage statistics viewer
6. **`Scripts/SIGNAL_USAGE_TRACKING.md`** - Comprehensive documentation

## 🚀 How to Use

### Step 1: Run Migration (Existing Databases Only)

If you have an existing database, run the migration once:

```bash
python Scripts/migrate_add_last_access_time.py
```

For new installations, just run `python Scripts/init_db.py` (schema already includes the column).

### Step 2: Use Your Agents Normally

No code changes needed! Just run your agents as usual:

```python
class MyAgent(BaseAgent):
    def __init__(self):
        # This automatically updates last_access_time for these signals
        self.used_signal_ids = [
            "SPY_day_close",
            "AAPL_arq_revenue",
        ]
```

### Step 3: View Usage Statistics

Check which signals are being used:

```bash
# View with 90-day stale threshold (default)
python Scripts/view_signal_usage.py

# View with custom threshold
python Scripts/view_signal_usage.py --stale-days 30
```

### Step 4: Clean Up Unused Signals

Based on the report, disable or delete unused signals:

```sql
-- Disable stale signals (safe first step)
UPDATE available_signals 
SET enabled = false 
WHERE last_access_time < now() - interval '90 days';

-- Delete never-used signals (after verification)
DELETE FROM available_signals 
WHERE last_access_time IS NULL 
  AND created_at < now() - interval '30 days';
```

## 📊 Example Output

```
================================================================================
Signal Usage Statistics
================================================================================

Total Signals: 10
  Active (used in last 90 days): 6
  Stale (not used in 90+ days): 2
  Never Used: 2
  Disabled: 0

================================================================================
ACTIVE SIGNALS (used in last 90 days)
================================================================================
Signal ID                      Source   Last Used            Status
--------------------------------------------------------------------------------
SPY_day_close                  massive  Today                ✓
AAPL_arq_revenue               sf1      3 days ago           ✓
QQQ_minute5_vwap               massive  1 week ago           ✓

================================================================================
STALE SIGNALS (not used in 90+ days)
================================================================================
Signal ID                      Source   Last Used            Status
--------------------------------------------------------------------------------
OLD_signal_1                   massive  4 months ago         ✓
OLD_signal_2                   sf1      6 months ago         ✓

================================================================================
NEVER USED SIGNALS
================================================================================
Signal ID                      Source   Created              Status
--------------------------------------------------------------------------------
TEST_signal                    massive  2 weeks ago          ✓
EXPERIMENTAL_signal            sf1      1 month ago          ✓

================================================================================
RECOMMENDATIONS
================================================================================

Consider reviewing 4 unused signals:
  - Check if they're still needed
  - Disable with: UPDATE available_signals SET enabled=false WHERE id='...'
  - Delete with: DELETE FROM available_signals WHERE id='...'
```

## 🔧 How It Works

### Behind the Scenes

1. **Agent instantiation** → declares `used_signal_ids`
2. **First data bar** → calls `build_snapshot_from_signal_ids()`
3. **Load signals** → calls `load_available_signals(update_access_time=True, signal_ids=[...])`
4. **Database update** → `UPDATE available_signals SET last_access_time = now() WHERE id IN (...)`
5. **Signal data fetched** → agent runs normally

### Tracking Location

The tracking happens in:
- `Common/agent_api.py` line ~162: `load_available_signals(... update_access_time=True, signal_ids=signal_ids)`
- `Common/signals_manager.py` line ~72-82: Executes UPDATE statement

### Performance Impact

- **Minimal**: One UPDATE per agent instantiation
- **Bulk update**: All signal IDs updated in single query
- **No data fetching impact**: Tracking happens before data fetch

## ✅ Backward Compatibility

**100% backward compatible:**
- ✅ Existing agents work without changes
- ✅ CSV fallback still works (tracking disabled)
- ✅ NULL timestamps = never used (not an error)
- ✅ Migration script safe to run multiple times

## 📋 Best Practices

### Regular Reviews

```bash
# Weekly: Check for new unused signals
python Scripts/view_signal_usage.py --stale-days 7

# Monthly: Review stale signals
python Scripts/view_signal_usage.py --stale-days 30

# Quarterly: Major cleanup
python Scripts/view_signal_usage.py --stale-days 90
```

### Gradual Cleanup Process

1. **Week 1**: Run report, identify stale signals
2. **Week 2**: Disable stale signals (`enabled = false`)
3. **Week 3**: Monitor for broken agents
4. **Week 4**: Delete if no issues

### SQL Queries

**Find signals not used in 90 days:**
```sql
SELECT id, source, spec, last_access_time
FROM available_signals
WHERE last_access_time < now() - interval '90 days'
   OR last_access_time IS NULL
ORDER BY last_access_time NULLS LAST;
```

**Most recently used signals:**
```sql
SELECT id, source, last_access_time
FROM available_signals
WHERE last_access_time IS NOT NULL
ORDER BY last_access_time DESC
LIMIT 10;
```

## 🎓 Documentation

Complete documentation in:
- **`Scripts/SIGNAL_USAGE_TRACKING.md`** - Full guide with examples, SQL queries, troubleshooting

## 🧪 Testing

Verify tracking works:

1. **Run migration:**
   ```bash
   python Scripts/migrate_add_last_access_time.py
   ```

2. **Check column exists:**
   ```sql
   SELECT id, last_access_time FROM available_signals LIMIT 1;
   ```

3. **Run an agent:**
   ```bash
   python Backtesting/run_suite.py
   ```

4. **Check timestamps updated:**
   ```bash
   python Scripts/view_signal_usage.py
   ```

5. **Verify SQL:**
   ```sql
   SELECT id, last_access_time 
   FROM available_signals 
   WHERE last_access_time IS NOT NULL;
   ```

## 🎯 Benefits

1. **Identify Dead Signals** - Know which signals are never used
2. **Track Active Usage** - Understand which signals are critical
3. **Database Optimization** - Remove clutter safely
4. **Audit Trail** - Historical usage patterns
5. **Informed Decisions** - Data-driven cleanup

## 🚨 Important Notes

- **Database only**: Tracking only works with PostgreSQL backend (not CSV)
- **Constructor tracking**: Updates when agent is instantiated, not per-bar
- **Bulk updates**: One query per agent run, not per signal
- **NULL is valid**: NULL means never used (not an error)

## 📦 Summary

You now have automatic signal usage tracking! Here's what you can do:

1. ✅ **Migration script ready** - Run once to add column to existing DB
2. ✅ **Automatic tracking** - Agents update timestamps transparently
3. ✅ **Usage viewer** - See which signals are active/stale/unused
4. ✅ **Cleanup guidance** - SQL queries and best practices included
5. ✅ **Full documentation** - Complete guide in SIGNAL_USAGE_TRACKING.md

**Next steps:**
1. Run `python Scripts/migrate_add_last_access_time.py` (if existing DB)
2. Run your agents normally
3. Check usage with `python Scripts/view_signal_usage.py`
4. Clean up unused signals based on the report!

---

**All files tested and ready to use!** The feature is production-ready and fully documented.
