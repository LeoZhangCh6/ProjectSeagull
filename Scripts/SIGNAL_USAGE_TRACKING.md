# Signal Usage Tracking Feature

## Overview

Added automatic tracking of signal usage to help identify which signals are actively used and which can be cleaned up. The system now tracks when each signal was last accessed by an agent.

## What Changed

### 1. Database Schema Update

Added `last_access_time` column to `available_signals` table:

```sql
ALTER TABLE available_signals 
ADD COLUMN last_access_time timestamptz;
```

This column is automatically updated whenever an agent declares and uses a signal.

### 2. Automatic Timestamp Updates

When an agent constructor declares signals via `self.used_signal_ids`, the system automatically:
- Updates `last_access_time` to current timestamp
- Tracks which signals are actively being used
- Provides data for cleanup decisions

### 3. New Utility Scripts

#### Migration Script
**`Scripts/migrate_add_last_access_time.py`**
- Adds the `last_access_time` column to existing databases
- Safe to run multiple times (checks if column exists)
- Run once to upgrade existing installations

#### Usage Viewer
**`Scripts/view_signal_usage.py`**
- Shows signal usage statistics
- Categorizes signals as Active/Stale/Never Used
- Provides cleanup recommendations
- Configurable stale threshold (default: 90 days)

## How It Works

### Agent Constructor Tracking

When an agent's constructor runs:

```python
class MyAgent(BaseAgent):
    def __init__(self):
        # Declaring signals automatically updates their last_access_time
        self.used_signal_ids = [
            "SPY_day_close",
            "AAPL_arq_revenue",
        ]
```

Behind the scenes:
1. `build_snapshot_from_signal_ids()` is called when agent processes data
2. It calls `load_available_signals()` with `update_access_time=True`
3. Database is updated: `UPDATE available_signals SET last_access_time = now() WHERE id IN (...)`

### No Code Changes Required

Existing agents work automatically! The tracking happens transparently in:
- `Common/agent_api.py` - `build_snapshot_from_signal_ids()`
- `Common/signals_manager.py` - `load_available_signals_db()`

## Installation & Migration

### For New Installations

The schema is already in `db/initialize.sql`. Just run:

```bash
python Scripts/init_db.py
```

### For Existing Databases

Run the migration script once:

```bash
python Scripts/migrate_add_last_access_time.py
```

Output:
```
============================================================
Migration: Add last_access_time to available_signals
============================================================
Adding 'last_access_time' column to available_signals table...
✓ Successfully added last_access_time column
  4 signals in table
  last_access_time will be updated automatically when signals are used
```

## Usage

### View Signal Usage Statistics

```bash
# Default: 90-day stale threshold
python Scripts/view_signal_usage.py

# Custom threshold: 30 days
python Scripts/view_signal_usage.py --stale-days 30

# Long-term threshold: 180 days
python Scripts/view_signal_usage.py --stale-days 180
```

### Example Output

```
================================================================================
Signal Usage Statistics
================================================================================

Total Signals: 10
  Active (used in last 90 days): 4
  Stale (not used in 90+ days): 3
  Never Used: 2
  Disabled: 1

================================================================================
ACTIVE SIGNALS (used in last 90 days)
================================================================================
Signal ID                      Source   Last Used            Status
--------------------------------------------------------------------------------
SPY_day_close                  massive  Today                ✓
AAPL_arq_revenue               sf1      3 days ago           ✓
QQQ_minute5_vwap               massive  1 week ago           ✓
TSLA_mrq_pe                    sf1      2 weeks ago          ✓

================================================================================
STALE SIGNALS (not used in 90+ days)
================================================================================
Signal ID                      Source   Last Used            Status
--------------------------------------------------------------------------------
MSFT_day_volume                massive  4 months ago         ✓
GOOGL_arq_assets               sf1      6 months ago         ✓
FB_hour_close                  massive  1 year ago           ✓

================================================================================
NEVER USED SIGNALS
================================================================================
Signal ID                      Source   Created              Status
--------------------------------------------------------------------------------
NFLX_day_close                 massive  2 weeks ago          ✓
AMZN_mrq_revenue               sf1      1 month ago          ✓

================================================================================
RECOMMENDATIONS
================================================================================

Consider reviewing 5 unused signals:
  - Check if they're still needed
  - Disable with: UPDATE available_signals SET enabled=false WHERE id='...'
  - Delete with: DELETE FROM available_signals WHERE id='...'
```

## Cleanup Strategies

### 1. Identify Unused Signals

Run the usage viewer regularly:

```bash
python Scripts/view_signal_usage.py
```

### 2. Disable Stale Signals

Instead of deleting, disable first:

```sql
-- Disable signals not used in 90+ days
UPDATE available_signals 
SET enabled = false 
WHERE last_access_time < now() - interval '90 days'
   OR last_access_time IS NULL;
```

This keeps the signal definition but prevents it from being loaded.

### 3. Monitor Impact

Wait a few days/weeks to ensure no agents break. If no issues:

### 4. Delete Unused Signals

```sql
-- Delete never-used signals older than 30 days
DELETE FROM available_signals 
WHERE last_access_time IS NULL 
  AND created_at < now() - interval '30 days';

-- Delete signals not used in 180+ days
DELETE FROM available_signals 
WHERE last_access_time < now() - interval '180 days';
```

## Benefits

1. **Identify Dead Signals**: See which signals are never used
2. **Track Active Usage**: Know which signals are critical to your agents
3. **Optimize Database**: Remove unused signals to reduce clutter
4. **Audit Trail**: Understand signal usage patterns over time
5. **Safe Cleanup**: Make informed decisions about what to delete

## Best Practices

### Run Usage Reports Regularly

```bash
# Weekly review
python Scripts/view_signal_usage.py --stale-days 30

# Monthly cleanup review
python Scripts/view_signal_usage.py --stale-days 90

# Annual audit
python Scripts/view_signal_usage.py --stale-days 365
```

### Set Up Monitoring

Create a cron job or scheduled task:

```bash
# Linux/Mac crontab: weekly report
0 9 * * 1 cd /path/to/ProjectSeagull && python Scripts/view_signal_usage.py > /tmp/signal_usage_$(date +\%Y\%m\%d).txt
```

### Gradual Cleanup Process

1. Week 1: Identify stale signals
2. Week 2: Disable stale signals
3. Week 3: Monitor for any breakage
4. Week 4: Delete if no issues

### Document Signal Purposes

When registering signals, use meaningful descriptions:

```python
# Good description
"SPY daily close - market benchmark for portfolio correlation"

# Bad description  
"SPY close"
```

## SQL Queries

### Find signals not used in N days

```sql
SELECT id, source, spec, last_access_time
FROM available_signals
WHERE last_access_time < now() - interval '90 days'
   OR last_access_time IS NULL
ORDER BY last_access_time NULLS LAST;
```

### Find most frequently used signals

```sql
SELECT id, source, last_access_time, 
       now() - last_access_time as time_since_use
FROM available_signals
WHERE last_access_time IS NOT NULL
ORDER BY last_access_time DESC
LIMIT 10;
```

### Count signals by usage status

```sql
SELECT 
  CASE 
    WHEN last_access_time IS NULL THEN 'Never Used'
    WHEN last_access_time >= now() - interval '30 days' THEN 'Active (30d)'
    WHEN last_access_time >= now() - interval '90 days' THEN 'Stale (90d)'
    ELSE 'Very Stale (90d+)'
  END as status,
  COUNT(*) as count
FROM available_signals
GROUP BY status
ORDER BY count DESC;
```

## Files Modified

1. **`db/initialize.sql`**
   - Added `last_access_time timestamptz` column

2. **`Common/signals_manager.py`**
   - Updated `load_available_signals_db()` with timestamp tracking
   - Updated `load_available_signals()` with new parameters

3. **`Common/agent_api.py`**
   - Updated `build_snapshot_from_signal_ids()` to track usage

## Files Created

1. **`Scripts/migrate_add_last_access_time.py`**
   - Migration script for existing databases

2. **`Scripts/view_signal_usage.py`**
   - Usage statistics viewer with recommendations

3. **`Scripts/SIGNAL_USAGE_TRACKING.md`** (this file)
   - Comprehensive documentation

## Backward Compatibility

✅ **Fully backward compatible!**

- Existing agents work without changes
- CSV fallback still works (tracking disabled)
- NULL `last_access_time` means "never used"
- Migration script safe to run multiple times

## Performance

- Minimal overhead: single UPDATE per agent instantiation
- Bulk update for multiple signals (one query)
- No performance impact on data fetching
- Indexed on `id` (primary key)

## Limitations

1. **Constructor-based tracking only**: Only tracks when agents are instantiated
2. **No per-use granularity**: Timestamp updated once per agent run, not per bar
3. **Database-only**: Tracking disabled when using CSV fallback
4. **No usage count**: Only tracks last access time, not frequency

## Future Enhancements

Potential improvements:

- [ ] Track usage count (how many times used)
- [ ] Track which agents use which signals
- [ ] Auto-disable signals not used in X months
- [ ] Email reports for stale signals
- [ ] Dashboard with usage graphs
- [ ] Signal dependency tracking

## Troubleshooting

### Migration fails

```bash
# Check if column already exists
psql $DATABASE_URL -c "\d available_signals"

# If stuck, manually add column
psql $DATABASE_URL -c "ALTER TABLE available_signals ADD COLUMN last_access_time timestamptz"
```

### Timestamps not updating

Check:
1. Using database (not CSV fallback)
2. `DATABASE_URL` or `PGHOST` is set
3. Agent uses `build_snapshot_from_signal_ids()`
4. Database user has UPDATE permissions

### View script fails

```bash
# Check database connection
psql $DATABASE_URL -c "SELECT COUNT(*) FROM available_signals"

# Check column exists
psql $DATABASE_URL -c "SELECT last_access_time FROM available_signals LIMIT 1"
```

## Summary

The signal usage tracking feature provides automatic, transparent tracking of which signals are actively used by your agents. This enables informed cleanup decisions and helps keep your signal registry lean and maintainable.

**Key takeaways:**
- ✅ Automatic tracking (no code changes needed)
- ✅ Run migration once for existing databases
- ✅ Use `view_signal_usage.py` regularly
- ✅ Gradually disable/delete unused signals
- ✅ Keep your signal registry clean!
