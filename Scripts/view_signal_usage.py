"""
View signal usage statistics from the available_signals table.

Shows which signals are being actively used and which are stale.

Usage:
    python Scripts/view_signal_usage.py [--stale-days DAYS]
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

# Add project root to path
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from Common.db import get_pg_conn


def format_timedelta(td):
    """Format timedelta as human-readable string."""
    if td is None:
        return "Never used"
    
    days = td.days
    if days == 0:
        return "Today"
    elif days == 1:
        return "Yesterday"
    elif days < 7:
        return f"{days} days ago"
    elif days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif days < 365:
        months = days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"


def view_usage(stale_days: int = 90):
    """View signal usage statistics."""
    print("=" * 80)
    print("Signal Usage Statistics")
    print("=" * 80)
    
    # Check database connection
    if not (os.environ.get("DATABASE_URL") or os.environ.get("PGHOST")):
        print("ERROR: DATABASE_URL or PGHOST environment variable not set.")
        return 1
    
    try:
        now = datetime.now()
        stale_threshold = now - timedelta(days=stale_days)
        
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                # Get all signals with usage info
                cur.execute(
                    """
                    SELECT 
                        id,
                        source,
                        spec,
                        enabled,
                        created_at,
                        last_access_time,
                        CASE 
                            WHEN last_access_time IS NULL THEN 'never'
                            WHEN last_access_time >= %s THEN 'active'
                            ELSE 'stale'
                        END as status
                    FROM available_signals
                    ORDER BY 
                        CASE 
                            WHEN last_access_time IS NULL THEN 2
                            WHEN last_access_time >= %s THEN 0
                            ELSE 1
                        END,
                        last_access_time DESC NULLS LAST,
                        id
                    """,
                    (stale_threshold, stale_threshold)
                )
                
                signals = cur.fetchall()
                
                if not signals:
                    print("No signals found in database.")
                    return 0
                
                # Count by status
                active_count = sum(1 for s in signals if s[6] == 'active')
                stale_count = sum(1 for s in signals if s[6] == 'stale')
                never_count = sum(1 for s in signals if s[6] == 'never')
                disabled_count = sum(1 for s in signals if not s[3])
                
                print(f"\nTotal Signals: {len(signals)}")
                print(f"  Active (used in last {stale_days} days): {active_count}")
                print(f"  Stale (not used in {stale_days}+ days): {stale_count}")
                print(f"  Never Used: {never_count}")
                print(f"  Disabled: {disabled_count}")
                print()
                
                # Show active signals
                if active_count > 0:
                    print(f"\n{'='*80}")
                    print(f"ACTIVE SIGNALS (used in last {stale_days} days)")
                    print(f"{'='*80}")
                    print(f"{'Signal ID':<30} {'Source':<8} {'Last Used':<20} {'Status'}")
                    print("-" * 80)
                    
                    for sig in signals:
                        if sig[6] == 'active':
                            sig_id, source, spec, enabled, created, last_access, status = sig
                            last_used = format_timedelta(now - last_access) if last_access else "Never"
                            enabled_str = "✓" if enabled else "✗"
                            print(f"{sig_id:<30} {source:<8} {last_used:<20} {enabled_str}")
                
                # Show stale signals
                if stale_count > 0:
                    print(f"\n{'='*80}")
                    print(f"STALE SIGNALS (not used in {stale_days}+ days)")
                    print(f"{'='*80}")
                    print(f"{'Signal ID':<30} {'Source':<8} {'Last Used':<20} {'Status'}")
                    print("-" * 80)
                    
                    for sig in signals:
                        if sig[6] == 'stale':
                            sig_id, source, spec, enabled, created, last_access, status = sig
                            last_used = format_timedelta(now - last_access) if last_access else "Never"
                            enabled_str = "✓" if enabled else "✗"
                            print(f"{sig_id:<30} {source:<8} {last_used:<20} {enabled_str}")
                
                # Show never used signals
                if never_count > 0:
                    print(f"\n{'='*80}")
                    print(f"NEVER USED SIGNALS")
                    print(f"{'='*80}")
                    print(f"{'Signal ID':<30} {'Source':<8} {'Created':<20} {'Status'}")
                    print("-" * 80)
                    
                    for sig in signals:
                        if sig[6] == 'never':
                            sig_id, source, spec, enabled, created, last_access, status = sig
                            created_str = format_timedelta(now - created.replace(tzinfo=None)) if created else "Unknown"
                            enabled_str = "✓" if enabled else "✗"
                            print(f"{sig_id:<30} {source:<8} {created_str:<20} {enabled_str}")
                
                # Recommendations
                print(f"\n{'='*80}")
                print("RECOMMENDATIONS")
                print(f"{'='*80}")
                
                if stale_count > 0 or never_count > 0:
                    print(f"\nConsider reviewing {stale_count + never_count} unused signals:")
                    print("  - Check if they're still needed")
                    print("  - Disable with: UPDATE available_signals SET enabled=false WHERE id='...'")
                    print("  - Delete with: DELETE FROM available_signals WHERE id='...'")
                else:
                    print("\n✓ All signals are being actively used!")
                
                return 0
                
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="View signal usage statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View signals with 90-day stale threshold (default)
  python Scripts/view_signal_usage.py
  
  # View signals with 30-day stale threshold
  python Scripts/view_signal_usage.py --stale-days 30
  
  # View signals with 180-day stale threshold
  python Scripts/view_signal_usage.py --stale-days 180
        """
    )
    
    parser.add_argument(
        '--stale-days',
        type=int,
        default=90,
        help='Number of days without access to consider a signal stale (default: 90)'
    )
    
    args = parser.parse_args()
    
    if args.stale_days < 1:
        print("ERROR: --stale-days must be >= 1")
        return 1
    
    return view_usage(args.stale_days)


if __name__ == "__main__":
    os.environ['MASSIVE_API_KEY'] = "Y2mALom8TLdet7Bc8ktLeQ4355hAdpG6"
    os.environ['NASDAQ_DATA_LINK_API_KEY'] = "s_phvq25xVMyCa6KBXFj"
    os.environ["DATABASE_URL"] = "postgresql://postgres:5369@localhost:5432/postgres"
    sys.exit(main())
