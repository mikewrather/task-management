"""
Voice Processing Analytics
Enhanced analysis and reporting for voice processing runs.

This module replaces analyze-voice-runs.py with enhanced features:
- Multiple output formats (JSON, CSV, HTML)
- Advanced statistics and trends
- Data visualization capabilities
- Integration with the new database system
"""

import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from io import StringIO

from ..utils.logging import VoiceLogger
from ..utils.database import VoiceDatabase
from ..models.voice_file import VoiceFile

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

class VoiceAnalyzer:
    """Enhanced voice processing analytics and reporting"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the voice analyzer
        
        Args:
            project_root: Project root directory (auto-detected if None)
        """
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.logger = VoiceLogger(self.project_root)
        self.database = VoiceDatabase(self.project_root)
        self.console = Console() if HAS_RICH else None
        
        # Log file paths
        self.log_dir = self.project_root / 'logs'
        self.run_history_log = self.log_dir / 'cron-run-history.log'
    
    def generate_analysis(self, include_stats: bool = True, today_only: bool = False,
                         include_errors: bool = False, export_format: Optional[str] = None,
                         last_n_runs: int = 10) -> str:
        """
        Generate comprehensive analysis report
        
        Args:
            include_stats: Include detailed statistics
            today_only: Show only today's activity
            include_errors: Include error analysis
            export_format: Export format ('json', 'csv', 'html')
            last_n_runs: Number of recent runs to show
            
        Returns:
            Formatted analysis report or export data
        """
        # Load run history and database data
        runs = self._load_run_history()
        db_stats = self.database.get_processing_stats()
        
        if export_format:
            return self._export_data(runs, db_stats, export_format)
        
        # Generate rich text report
        output = StringIO()
        
        if not runs and db_stats['total_files'] == 0:
            return "📭 No voice processing data found. The system may not have run yet."
        
        # Header
        output.write(f"📈 Voice Processing Analysis ({len(runs)} run records, {db_stats['total_files']} total files)\n\n")
        
        if today_only:
            runs = self._filter_today_runs(runs)
            output.write(self._format_today_analysis(runs, db_stats))
        elif include_stats:
            output.write(self._format_comprehensive_stats(runs, db_stats))
        elif include_errors:
            output.write(self._format_error_analysis(runs))
        else:
            output.write(self._format_recent_runs(runs, last_n_runs))
        
        return output.getvalue()
    
    def _load_run_history(self) -> List[Dict[str, Any]]:
        """Load and parse run history from JSON log file"""
        if not self.run_history_log.exists():
            return []
        
        runs = []
        with open(self.run_history_log) as f:
            for line_num, line in enumerate(f, 1):
                try:
                    run_data = json.loads(line.strip())
                    # Parse timestamp
                    run_data['datetime'] = datetime.fromisoformat(run_data['timestamp'])
                    runs.append(run_data)
                except (json.JSONDecodeError, ValueError) as e:
                    self.logger.debug(f"Skipping invalid log line {line_num}: {e}")
                    continue
        
        return sorted(runs, key=lambda x: x['datetime'], reverse=True)
    
    def _filter_today_runs(self, runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter runs to only include today's runs"""
        today = datetime.now().date()
        return [r for r in runs if r['datetime'].date() == today]
    
    def _format_recent_runs(self, runs: List[Dict[str, Any]], count: int) -> str:
        """Format recent runs display"""
        if not runs:
            return "📭 No run history found.\n"
        
        output = StringIO()
        output.write(f"📊 Last {min(count, len(runs))} runs:\n")
        output.write("-" * 80 + "\n")
        
        for run in runs[:count]:
            output.write(self._format_run_entry(run) + "\n")
        
        if len(runs) > count:
            output.write(f"\n... and {len(runs) - count} older runs\n")
        
        return output.getvalue()
    
    def _format_today_analysis(self, runs: List[Dict[str, Any]], db_stats: Dict[str, Any]) -> str:
        """Format today's activity analysis"""
        output = StringIO()
        output.write(f"📅 Today's Activity ({len(runs)} runs):\n")
        output.write("-" * 80 + "\n")
        
        if not runs and db_stats['today_processed'] == 0:
            output.write("No activity today\n")
            return output.getvalue()
        
        # Show today's runs
        for run in runs:
            output.write(self._format_run_entry(run) + "\n")
        
        # Today's summary from database
        if db_stats['today_processed'] > 0:
            output.write(f"\n📊 Today's Summary:\n")
            output.write(f"Files processed: {db_stats['today_processed']}\n")
            output.write(f"Success rate: {db_stats['success_rate']:.1f}%\n")
        
        return output.getvalue()
    
    def _format_comprehensive_stats(self, runs: List[Dict[str, Any]], db_stats: Dict[str, Any]) -> str:
        """Format comprehensive statistics"""
        output = StringIO()
        
        # Run Statistics
        if runs:
            total_runs = len(runs)
            success_runs = len([r for r in runs if r['status'] == 'success'])
            failed_runs = len([r for r in runs if r['status'] == 'failed'])
            partial_runs = len([r for r in runs if r['status'] == 'partial'])
            
            total_files_found = sum(r['files_found'] for r in runs)
            total_files_processed = sum(r['files_processed'] for r in runs)
            total_errors = sum(r.get('errors', 0) for r in runs)
            total_warnings = sum(r.get('warnings', 0) for r in runs)
            
            # Calculate average duration
            durations = [r.get('run_duration_seconds', r.get('duration_seconds', 0)) for r in runs]
            avg_duration = sum(durations) / total_runs if durations else 0
            
            # Recent activity
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_runs = [r for r in runs if r['datetime'] >= recent_cutoff]
            
            output.write("📊 VOICE PROCESSING STATISTICS\n")
            output.write("=" * 50 + "\n")
            output.write("RUN STATISTICS:\n")
            output.write(f"Total Runs:           {total_runs:4d}\n")
            output.write(f"Successful:           {success_runs:4d} ({success_runs/total_runs*100:.1f}%)\n")
            output.write(f"Failed:               {failed_runs:4d} ({failed_runs/total_runs*100:.1f}%)\n")
            output.write(f"Partial:              {partial_runs:4d} ({partial_runs/total_runs*100:.1f}%)\n")
            output.write("\n")
            
            output.write("FILE STATISTICS:\n")
            output.write(f"Files Found (runs):   {total_files_found:4d}\n")
            output.write(f"Files Processed:      {total_files_processed:4d}\n")
            output.write(f"Processing Success:   {total_files_processed/max(total_files_found,1)*100:.1f}%\n")
            output.write(f"Total Errors:         {total_errors:4d}\n")
            output.write(f"Total Warnings:       {total_warnings:4d}\n")
            output.write("\n")
            
            output.write("PERFORMANCE:\n")
            output.write(f"Average Duration:     {avg_duration:5.1f}s\n")
            output.write(f"Recent Activity:      {len(recent_runs)} runs in last 24h\n")
            
            if runs:
                latest = runs[0]
                oldest = runs[-1]
                duration = latest['datetime'] - oldest['datetime']
                output.write(f"Monitoring Period:    {duration.days} days\n")
                output.write(f"Latest Run:           {latest['datetime'].strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Database Statistics
        output.write("\nDATABASE STATISTICS:\n")
        output.write(f"Total Files in DB:    {db_stats['total_files']:4d}\n")
        output.write(f"Completed Files:      {db_stats['completed_files']:4d}\n")
        output.write(f"Failed Files:         {db_stats['failed_files']:4d}\n")
        output.write(f"Pending Files:        {db_stats['pending_files']:4d}\n")
        output.write(f"Today Processed:      {db_stats['today_processed']:4d}\n")
        output.write(f"Overall Success Rate: {db_stats['success_rate']:.1f}%\n")
        
        if db_stats['avg_processing_time_seconds'] > 0:
            output.write(f"Avg Processing Time:  {db_stats['avg_processing_time_seconds']:.1f}s\n")
        
        # System Health
        if runs:
            recent_success_rate = len([r for r in recent_runs if r['status'] == 'success']) / max(len(recent_runs), 1)
            if recent_success_rate >= 0.9:
                health = "🟢 HEALTHY"
            elif recent_success_rate >= 0.7:
                health = "🟡 WARNING"
            else:
                health = "🔴 CRITICAL"
            
            output.write(f"\nSystem Health:        {health} ({recent_success_rate*100:.0f}% success rate)\n")
        
        return output.getvalue()
    
    def _format_error_analysis(self, runs: List[Dict[str, Any]]) -> str:
        """Format error and warning analysis"""
        output = StringIO()
        
        error_runs = [r for r in runs if r.get('errors', 0) > 0]
        warning_runs = [r for r in runs if r.get('warnings', 0) > 0]
        
        if not error_runs and not warning_runs:
            output.write("✅ No errors or warnings found in recent runs\n")
            return output.getvalue()
        
        if error_runs:
            output.write(f"❌ ERROR SUMMARY ({len(error_runs)} runs with errors):\n")
            output.write("-" * 60 + "\n")
            for run in error_runs[-10:]:  # Show last 10 error runs
                errors = run.get('errors', 0)
                output.write(f"❌ {run['datetime'].strftime('%Y-%m-%d %H:%M:%S')} - {errors} error(s)\n")
            output.write("\n")
        
        if warning_runs:
            output.write(f"⚠️  WARNING SUMMARY ({len(warning_runs)} runs with warnings):\n")
            output.write("-" * 60 + "\n")
            for run in warning_runs[-10:]:  # Show last 10 warning runs
                warnings = run.get('warnings', 0)
                output.write(f"⚠️  {run['datetime'].strftime('%Y-%m-%d %H:%M:%S')} - {warnings} warning(s)\n")
        
        return output.getvalue()
    
    def _format_run_entry(self, run: Dict[str, Any]) -> str:
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
    
    def _export_data(self, runs: List[Dict[str, Any]], db_stats: Dict[str, Any], 
                    format_type: str) -> str:
        """Export data in specified format"""
        if format_type.lower() == 'json':
            return self._export_json(runs, db_stats)
        elif format_type.lower() == 'csv':
            return self._export_csv(runs)
        elif format_type.lower() == 'html':
            return self._export_html(runs, db_stats)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _export_json(self, runs: List[Dict[str, Any]], db_stats: Dict[str, Any]) -> str:
        """Export data as JSON"""
        # Convert datetime objects to ISO strings for JSON serialization
        json_runs = []
        for run in runs:
            json_run = run.copy()
            json_run['timestamp'] = run['datetime'].isoformat()
            del json_run['datetime']
            json_runs.append(json_run)
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'database_stats': db_stats,
            'run_history': json_runs,
            'summary': {
                'total_runs': len(runs),
                'successful_runs': len([r for r in runs if r['status'] == 'success']),
                'failed_runs': len([r for r in runs if r['status'] == 'failed']),
                'total_files_processed': sum(r['files_processed'] for r in runs)
            }
        }
        
        return json.dumps(export_data, indent=2)
    
    def _export_csv(self, runs: List[Dict[str, Any]]) -> str:
        """Export run data as CSV"""
        if not runs:
            return "timestamp,status,files_found,files_processed,errors,warnings,duration_seconds\n"
        
        output = StringIO()
        fieldnames = [
            'timestamp', 'status', 'files_found', 'files_processed', 
            'errors', 'warnings', 'run_duration_seconds', 'processing_success_rate'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for run in runs:
            csv_row = {
                'timestamp': run['datetime'].isoformat(),
                'status': run['status'],
                'files_found': run['files_found'],
                'files_processed': run['files_processed'],
                'errors': run.get('errors', 0),
                'warnings': run.get('warnings', 0),
                'run_duration_seconds': run.get('run_duration_seconds', 0),
                'processing_success_rate': run.get('processing_success_rate', 0)
            }
            writer.writerow(csv_row)
        
        return output.getvalue()
    
    def _export_html(self, runs: List[Dict[str, Any]], db_stats: Dict[str, Any]) -> str:
        """Export data as HTML report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Voice Processing Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f5f5f5; padding: 20px; border-radius: 8px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-box {{ background-color: #e8f4f8; padding: 15px; border-radius: 8px; flex: 1; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .success {{ color: green; }}
        .failed {{ color: red; }}
        .partial {{ color: orange; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎤 Voice Processing Analysis Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Runs: {len(runs)} | Total Files: {db_stats['total_files']}</p>
    </div>
    
    <div class="stats">
        <div class="stat-box">
            <h3>Database Stats</h3>
            <p>Completed: {db_stats['completed_files']}</p>
            <p>Failed: {db_stats['failed_files']}</p>
            <p>Success Rate: {db_stats['success_rate']:.1f}%</p>
        </div>
        <div class="stat-box">
            <h3>Recent Activity</h3>
            <p>Today Processed: {db_stats['today_processed']}</p>
            <p>Avg Processing: {db_stats['avg_processing_time_seconds']:.1f}s</p>
        </div>
    </div>
    
    <h2>Recent Runs</h2>
    <table>
        <tr>
            <th>Timestamp</th>
            <th>Status</th>
            <th>Found</th>
            <th>Processed</th>
            <th>Errors</th>
            <th>Duration</th>
        </tr>
"""
        
        for run in runs[:20]:  # Show last 20 runs
            status_class = run['status']
            duration = run.get('run_duration_seconds', 0)
            html += f"""
        <tr>
            <td>{run['datetime'].strftime('%Y-%m-%d %H:%M:%S')}</td>
            <td class="{status_class}">{run['status']}</td>
            <td>{run['files_found']}</td>
            <td>{run['files_processed']}</td>
            <td>{run.get('errors', 0)}</td>
            <td>{duration:.1f}s</td>
        </tr>
"""
        
        html += """
    </table>
</body>
</html>
"""
        return html
    
    def get_trend_analysis(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Analyze trends over the specified time period
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        runs = self._load_run_history()
        recent_runs = [r for r in runs if r['datetime'] >= cutoff_date]
        
        if not recent_runs:
            return {'error': 'No data available for trend analysis'}
        
        # Group by day
        daily_stats = {}
        for run in recent_runs:
            day_key = run['datetime'].date().isoformat()
            if day_key not in daily_stats:
                daily_stats[day_key] = {
                    'runs': 0,
                    'files_found': 0,
                    'files_processed': 0,
                    'errors': 0,
                    'avg_duration': 0
                }
            
            daily_stats[day_key]['runs'] += 1
            daily_stats[day_key]['files_found'] += run['files_found']
            daily_stats[day_key]['files_processed'] += run['files_processed']
            daily_stats[day_key]['errors'] += run.get('errors', 0)
            daily_stats[day_key]['avg_duration'] += run.get('run_duration_seconds', 0)
        
        # Calculate averages
        for day_data in daily_stats.values():
            if day_data['runs'] > 0:
                day_data['avg_duration'] /= day_data['runs']
        
        return {
            'period_days': days_back,
            'total_runs': len(recent_runs),
            'daily_breakdown': daily_stats,
            'summary': {
                'avg_files_per_day': sum(d['files_processed'] for d in daily_stats.values()) / max(len(daily_stats), 1),
                'avg_runs_per_day': len(recent_runs) / max(len(daily_stats), 1),
                'total_errors': sum(d['errors'] for d in daily_stats.values())
            }
        }