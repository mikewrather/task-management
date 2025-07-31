#!/usr/bin/env python3
"""
Voice Processing Run Analyzer
Analyze and display statistics from voice processing runs.

Usage: python3 scripts/analyze-voice-runs.py [--last N] [--today] [--stats]
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import argparse

project_root = Path(__file__).parent.parent

def load_run_history():
    """Load run history from JSON log file"""
    log_file = project_root / 'logs' / 'cron-run-history.log'
    
    if not log_file.exists():
        return []
    
    runs = []
    with open(log_file) as f:
        for line in f:
            try:
                run_data = json.loads(line.strip())
                # Parse timestamp
                run_data['datetime'] = datetime.fromisoformat(run_data['timestamp'])
                runs.append(run_data)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ Skipping invalid log line: {e}")
                continue
    
    return sorted(runs, key=lambda x: x['datetime'], reverse=True)

def format_run_entry(run):
    """Format a single run entry for display"""
    dt = run['datetime']
    status_symbols = {'success': '✅', 'partial': '⚠️ ', 'failed': '❌'}
    status = status_symbols.get(run['status'], '❓')
    
    # Handle both old and new log formats
    duration = run.get('run_duration_seconds', run.get('duration_seconds', 0))
    errors = run.get('errors', 0)
    warnings = run.get('warnings', 0)
    
    return (
        f"{status} {dt.strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Found: {run['files_found']:2d} | "
        f"Processed: {run['files_processed']:2d} | "
        f"Errors: {errors:2d} | "
        f"Warnings: {warnings:2d} | "
        f"Duration: {duration:5.1f}s"
    )

def show_recent_runs(runs, count=10):
    """Show recent runs"""
    print(f"📊 Last {min(count, len(runs))} runs:")
    print("-" * 80)
    
    for run in runs[:count]:
        print(format_run_entry(run))
    
    if len(runs) > count:
        print(f"\n... and {len(runs) - count} older runs")

def show_today_runs(runs):
    """Show today's runs"""
    today = datetime.now().date()
    today_runs = [r for r in runs if r['datetime'].date() == today]
    
    print(f"📅 Today's runs ({len(today_runs)} total):")
    print("-" * 80)
    
    if not today_runs:
        print("No runs today")
        return
    
    for run in today_runs:
        print(format_run_entry(run))

def show_statistics(runs):
    """Show comprehensive statistics"""
    if not runs:
        print("📊 No run data available")
        return
    
    total_runs = len(runs)
    success_runs = len([r for r in runs if r['status'] == 'success'])
    failed_runs = len([r for r in runs if r['status'] == 'failed'])
    partial_runs = len([r for r in runs if r['status'] == 'partial'])
    
    total_files_found = sum(r['files_found'] for r in runs)
    total_files_processed = sum(r['files_processed'] for r in runs)
    total_errors = sum(r.get('errors', 0) for r in runs)
    total_warnings = sum(r.get('warnings', 0) for r in runs)
    
    # Handle both old and new duration field names
    durations = [r.get('run_duration_seconds', r.get('duration_seconds', 0)) for r in runs]
    avg_duration = sum(durations) / total_runs
    
    # Recent activity (last 24 hours)
    recent_cutoff = datetime.now() - timedelta(hours=24)
    recent_runs = [r for r in runs if r['datetime'] >= recent_cutoff]
    
    print("📊 VOICE PROCESSING STATISTICS")
    print("=" * 50)
    print(f"Total Runs:           {total_runs:4d}")
    print(f"Successful:           {success_runs:4d} ({success_runs/total_runs*100:.1f}%)")
    print(f"Failed:               {failed_runs:4d} ({failed_runs/total_runs*100:.1f}%)")
    print(f"Partial:              {partial_runs:4d} ({partial_runs/total_runs*100:.1f}%)")
    print()
    print(f"Files Found:          {total_files_found:4d}")
    print(f"Files Processed:      {total_files_processed:4d}")
    print(f"Processing Success:   {total_files_processed/max(total_files_found,1)*100:.1f}%")
    print(f"Total Errors:         {total_errors:4d}")
    print(f"Total Warnings:       {total_warnings:4d}")
    print()
    print(f"Average Duration:     {avg_duration:5.1f}s")
    print(f"Recent Activity:      {len(recent_runs)} runs in last 24h")
    
    if runs:
        latest = runs[0]
        oldest = runs[-1]
        duration = latest['datetime'] - oldest['datetime']
        print(f"Monitoring Period:    {duration.days} days")
        print(f"Latest Run:           {latest['datetime'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    # System health indicator
    recent_success_rate = len([r for r in recent_runs if r['status'] == 'success']) / max(len(recent_runs), 1)
    if recent_success_rate >= 0.9:
        health = "🟢 HEALTHY"
    elif recent_success_rate >= 0.7:
        health = "🟡 WARNING"
    else:
        health = "🔴 CRITICAL"
    
    print(f"\nSystem Health:        {health} ({recent_success_rate*100:.0f}% success rate)")

def show_error_summary(runs):
    """Show summary of errors"""
    error_runs = [r for r in runs if r.get('errors', 0) > 0]
    warning_runs = [r for r in runs if r.get('warnings', 0) > 0]
    
    if not error_runs and not warning_runs:
        print("✅ No errors or warnings found in recent runs")
        return
    
    if error_runs:
        print(f"❌ ERROR SUMMARY ({len(error_runs)} runs with errors):")
        print("-" * 60)
        for run in error_runs:
            errors = run.get('errors', 0)
            print(f"❌ {run['datetime'].strftime('%Y-%m-%d %H:%M:%S')} - {errors} error(s)")
        print()
    
    if warning_runs:
        print(f"⚠️  WARNING SUMMARY ({len(warning_runs)} runs with warnings):")
        print("-" * 60)
        for run in warning_runs:
            warnings = run.get('warnings', 0)
            print(f"⚠️  {run['datetime'].strftime('%Y-%m-%d %H:%M:%S')} - {warnings} warning(s)")

def main():
    parser = argparse.ArgumentParser(description='Analyze voice processing runs')
    parser.add_argument('--last', type=int, default=10, help='Show last N runs (default: 10)')
    parser.add_argument('--today', action='store_true', help='Show only today\'s runs')
    parser.add_argument('--stats', action='store_true', help='Show comprehensive statistics')
    parser.add_argument('--errors', action='store_true', help='Show error summary')
    
    args = parser.parse_args()
    
    runs = load_run_history()
    
    if not runs:
        print("📭 No run history found. The system may not have run yet.")
        print("💡 Try running: ./scripts/voice-cron-wrapper.sh")
        return
    
    print(f"📈 Voice Processing Run Analysis ({len(runs)} total runs)")
    print()
    
    if args.stats:
        show_statistics(runs)
    elif args.today:
        show_today_runs(runs)
    elif args.errors:
        show_error_summary(runs)
    else:
        show_recent_runs(runs, args.last)

if __name__ == "__main__":
    main()