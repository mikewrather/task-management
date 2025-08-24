"""Command Line Interface for Voice Task Manager"""

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text
from pathlib import Path
import sys
from typing import Optional

console = Console()

@click.group()
@click.version_option(version="1.0.0")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """Voice Task Manager - Automated voice recording to GraphRAG task conversion"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    if verbose:
        console.print("[dim]Voice Task Manager v1.0.0[/dim]")

@main.command()
@click.option('--dry-run', is_flag=True, help='Show what would be processed without actually doing it')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def process(ctx: click.Context, dry_run: bool, verbose: bool) -> None:
    """Run voice processing pipeline (replaces automated-voice-processor.py)"""
    
    if dry_run:
        console.print("🔍 [yellow]DRY RUN MODE[/yellow] - No files will be processed")
    
    console.print("🎤 Starting voice processing pipeline...")
    
    try:
        # Import the GraphRAG-enabled processor
        from .core.processor import VoiceProcessorV2
        processor = VoiceProcessorV2()
        console.print("🚀 Using GraphRAG processor with entity managers")
        
        results = processor.process_all_files(dry_run=dry_run)
        
        if results['success']:
            if results.get('processed', 0) > 0:
                console.print(f"✅ Successfully processed {results['processed']} voice files!")
                if results.get('database_url'):
                    console.print(f"📋 Check your tasks: {results['database_url']}")
                
                # Show additional details
                if verbose or ctx.obj.get('verbose'):
                    console.print(f"\n📊 Processing Details:")
                    console.print(f"   • Total files found: {results.get('total_found', 0)}")
                    console.print(f"   • Unprocessed files: {results.get('unprocessed_found', 0)}")
                    console.print(f"   • Successfully processed: {results.get('processed', 0)}")
                    
                    if results.get('run_summary'):
                        summary = results['run_summary']
                        console.print(f"   • Processing duration: {summary.get('run_duration_seconds', 0):.1f}s")
                        console.print(f"   • Success rate: {summary.get('processing_success_rate', 0):.1f}%")
            else:
                if results.get('total_found', 0) > 0:
                    console.print("📋 All discovered files have already been processed")
                else:
                    console.print("📭 No audio files found in Google Drive folder")
        else:
            console.print(f"❌ Processing failed: {results.get('error', 'Unknown error')}", style="red")
            sys.exit(1)
            
    except ImportError as e:
        console.print("⚠️  [red]Import error - missing dependencies[/red]")
        console.print(f"Details: {e}")
        console.print("💡 Make sure you're running in the virtual environment with: source venv/bin/activate")
        sys.exit(1)
        
    except ValueError as e:
        console.print("⚠️  [red]Configuration error[/red]")
        console.print(f"Details: {e}")
        console.print("💡 Check your .env file and ensure all required API keys are set")
        sys.exit(1)
        
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        if verbose or ctx.obj.get('verbose'):
            import traceback
            console.print("\n[dim]Stack trace:[/dim]")
            console.print(traceback.format_exc())
        sys.exit(1)

@main.command()
@click.option('--stats', is_flag=True, help='Show detailed statistics')
@click.option('--today', is_flag=True, help='Show only today\'s activity')
@click.option('--errors', is_flag=True, help='Show recent errors')
@click.option('--export', type=click.Choice(['json', 'csv']), help='Export data in specified format')
@click.pass_context
def analyze(ctx: click.Context, stats: bool, today: bool, errors: bool, export: Optional[str]) -> None:
    """Show voice processing statistics and analysis (replaces analyze-voice-runs.py)"""
    
    console.print("📊 Analyzing voice processing data...")
    
    try:
        from .core.analyzer import VoiceAnalyzer
        
        analyzer = VoiceAnalyzer()
        results = analyzer.generate_analysis(
            include_stats=stats,
            today_only=today,
            include_errors=errors,
            export_format=export
        )
        
        if export:
            # For export formats, just print the raw data
            print(results)
        else:
            # For terminal display, use console for better formatting
            console.print(results)
        
    except ImportError as e:
        console.print("⚠️  [red]Import error - analysis module dependencies missing[/red]")
        console.print(f"Details: {e}")
        console.print("💡 Make sure you're running in the virtual environment")
        
    except Exception as e:
        console.print(f"❌ Analysis failed: {e}", style="red")
        if ctx.obj.get('verbose'):
            import traceback
            console.print("\n[dim]Stack trace:[/dim]")
            console.print(traceback.format_exc())

@main.command()
@click.option('--list', 'list_files', is_flag=True, help='List processed files that can be cleaned up')
@click.option('--guide', is_flag=True, help='Show cleanup guidance')
@click.option('--auto', is_flag=True, help='Automatically clean up old files')
@click.option('--dry-run', is_flag=True, help='Show what would be cleaned without doing it')
@click.pass_context
def cleanup(ctx: click.Context, list_files: bool, guide: bool, auto: bool, dry_run: bool) -> None:
    """Manage processed voice files (replaces cleanup-processed-files.py)"""
    
    console.print("🧹 Voice file cleanup management...")
    
    try:
        from .core.cleanup import VoiceCleanup
        
        cleanup_manager = VoiceCleanup()
        
        if list_files:
            results = cleanup_manager.list_processed_files()
            console.print(results)
        elif guide:
            results = cleanup_manager.show_cleanup_guide()
            console.print(results)
        elif auto:
            results = cleanup_manager.auto_cleanup(dry_run=dry_run)
            console.print(results)
        else:
            # Default: show stats and guide if cleanup is needed
            results = cleanup_manager.format_cleanup_stats()
            console.print(results)
            
            # Show tip about available options
            console.print("\n💡 Available options:")
            console.print("   --list     List all processed files")
            console.print("   --guide    Show manual cleanup instructions")
            console.print("   --auto     Run automated cleanup (when implemented)")
            
    except ImportError as e:
        console.print("⚠️  [red]Import error - cleanup module dependencies missing[/red]")
        console.print(f"Details: {e}")
        console.print("💡 Make sure you're running in the virtual environment")
        
    except Exception as e:
        console.print(f"❌ Cleanup operation failed: {e}", style="red")
        if ctx.obj.get('verbose'):
            import traceback
            console.print("\n[dim]Stack trace:[/dim]")
            console.print(traceback.format_exc())

@main.command()
@click.option('--detailed', is_flag=True, help='Show detailed system information')
@click.option('--json', 'output_json', is_flag=True, help='Output status in JSON format')
@click.pass_context
def status(ctx: click.Context, detailed: bool, output_json: bool) -> None:
    """Show system health and status (replaces voice-status.sh)"""
    
    try:
        from .utils.config import SystemStatus
        
        status_checker = SystemStatus()
        results = status_checker.get_system_status(detailed=detailed, json_format=output_json)
        
        if output_json:
            # For JSON output, parse and use console.print_json for nice formatting
            import json
            data = json.loads(results)
            console.print_json(data=data)
        else:
            # For text output, print directly (it's already formatted)
            print(results)
            
    except ImportError as e:
        console.print("⚠️  [red]Import error - status module dependencies missing[/red]")
        console.print(f"Details: {e}")
        console.print("💡 Make sure you're running in the virtual environment")
        
    except Exception as e:
        console.print(f"❌ Status check failed: {e}", style="red")
        if ctx.obj.get('verbose'):
            import traceback
            console.print("\n[dim]Stack trace:[/dim]")
            console.print(traceback.format_exc())

@main.command()
@click.option('--test', is_flag=True, help='Test all notification channels')
@click.option('--status', is_flag=True, help='Show notification system status')
@click.option('--summary', is_flag=True, help='Send daily summary notification')
@click.option('--history', is_flag=True, help='Show recent notification history')
@click.pass_context
def notify(ctx: click.Context, test: bool, status: bool, summary: bool, history: bool) -> None:
    """Manage notifications system (replaces notification-system.py)"""
    
    console.print("📢 Voice Task Manager Notifications")
    
    try:
        from .utils.notifications import VoiceNotificationSystem
        
        notification_system = VoiceNotificationSystem()
        
        if test:
            console.print("🧪 Testing notification system...")
            results = notification_system.test_notifications()
            
            for channel, success in results.items():
                status_icon = "✅" if success else "❌"
                console.print(f"   {channel.capitalize()}: {status_icon}")
            
        elif status:
            status_info = notification_system.get_notification_status()
            console.print(status_info)
            
        elif summary:
            console.print("📊 Sending daily summary...")
            results = notification_system.notify_daily_summary()
            
            if results.get('skipped'):
                console.print("📭 No activity today - summary skipped")
            else:
                sent_channels = [ch for ch, success in results.items() if success]
                if sent_channels:
                    console.print(f"✅ Summary sent via: {', '.join(sent_channels)}")
                else:
                    console.print("❌ Failed to send summary")
            
        elif history:
            notifications = notification_system.get_notification_history()
            
            if not notifications:
                console.print("📭 No recent notifications")
            else:
                console.print(f"📋 Recent notifications ({len(notifications)} in last 24h):")
                for notif in notifications[-10:]:  # Show last 10
                    timestamp = notif['timestamp'].strftime('%H:%M:%S')
                    template = notif['template']
                    priority = notif['priority']
                    success_channels = [ch for ch, success in notif['results'].items() if success]
                    console.print(f"   {timestamp} | {template} ({priority}) → {', '.join(success_channels)}")
        else:
            # Default: show status
            status_info = notification_system.get_notification_status()
            console.print(status_info)
            
            console.print("\n💡 Available options:")
            console.print("   --test      Test all notification channels")
            console.print("   --status    Show detailed system status")
            console.print("   --summary   Send daily summary notification")
            console.print("   --history   Show recent notification history")
        
    except ImportError as e:
        console.print("⚠️  [red]Import error - notification module dependencies missing[/red]")
        console.print(f"Details: {e}")
        console.print("💡 Make sure you're running in the virtual environment")
        
    except Exception as e:
        console.print(f"❌ Notification operation failed: {e}", style="red")
        if ctx.obj.get('verbose'):
            import traceback
            console.print("\n[dim]Stack trace:[/dim]")
            console.print(traceback.format_exc())

@main.command()
@click.option('--cron', is_flag=True, help='Configure cron job')
@click.option('--validate', is_flag=True, help='Validate system configuration')
@click.option('--reset', is_flag=True, help='Reset configuration to defaults')
@click.pass_context
def setup(ctx: click.Context, cron: bool, validate: bool, reset: bool) -> None:
    """Configure system and cron jobs (replaces setup-voice-cron.sh)"""
    
    console.print("⚙️  Voice Task Manager Setup")
    
    try:
        from .utils.config import SystemSetup
        
        setup_manager = SystemSetup()
        
        if cron:
            results = setup_manager.configure_cron()
            print(results)  # Use print for formatted output
        elif validate:
            results = setup_manager.validate_configuration()
            print(results)  # Use print for formatted output
        elif reset:
            results = setup_manager.reset_configuration()
            print(results)  # Use print for formatted output
        else:
            console.print("\n💡 Available setup options:")
            console.print("   --cron      Configure automated processing cron job")
            console.print("   --validate  Validate system configuration")
            console.print("   --reset     Reset configuration to defaults")
            console.print("\nUse 'vtm setup --help' for more details.")
            
    except ImportError as e:
        console.print("⚠️  [red]Import error - setup module dependencies missing[/red]")
        console.print(f"Details: {e}")
        console.print("💡 Make sure you're running in the virtual environment")
        
    except Exception as e:
        console.print(f"❌ Setup operation failed: {e}", style="red")
        if ctx.obj.get('verbose'):
            import traceback
            console.print("\n[dim]Stack trace:[/dim]")
            console.print(traceback.format_exc())

@main.command()
@click.option('--list', 'list_files', is_flag=True, help='List files pending archival')
@click.option('--mark', help='Mark specific file ID for archival')
@click.option('--mark-archived', help='Mark specific file ID as successfully archived')
@click.option('--auto', is_flag=True, help='Mark eligible files for auto-archival')
@click.option('--status', is_flag=True, help='Show archive statistics')
@click.option('--dry-run', is_flag=True, help='Show what would be archived without doing it')
@click.pass_context
def archive(ctx: click.Context, list_files: bool, mark: Optional[str], 
           mark_archived: Optional[str], auto: bool, status: bool, dry_run: bool) -> None:
    """Manage voice file archival system"""
    
    console.print("📦 Voice File Archive Management")
    
    try:
        from .utils.database import VoiceDatabase
        
        database = VoiceDatabase()
        
        if status:
            # Show archive statistics
            stats = database.get_archive_statistics()
            
            console.print("\n📊 Archive Statistics:")
            console.print(f"   Active files: {stats['active_files']}")
            console.print(f"   Pending archive: {stats['pending_archive']}")  
            console.print(f"   Archived files: {stats['archived_count']}")
            console.print(f"   Recent archived: {stats['recent_archived']} (last 7 days)")
            console.print(f"   Total files: {stats['total_files']}")
            
        elif list_files:
            # List files pending archival
            pending_files = database.get_files_pending_archive()
            
            if not pending_files:
                console.print("📭 No files pending archival")
            else:
                console.print(f"\n📋 Files Pending Archival ({len(pending_files)}):")
                for file in pending_files:
                    console.print(f"   • {file.file_id[:12]}... - Processed: {file.processed_at.strftime('%Y-%m-%d %H:%M') if file.processed_at else 'Unknown'}")
                    if file.transcript:
                        preview = file.transcript[:60] + "..." if len(file.transcript) > 60 else file.transcript
                        console.print(f"     Preview: {preview}")
                        
        elif mark:
            # Mark a specific file for archival
            if dry_run:
                console.print(f"🔍 [DRY RUN] Would mark file {mark} for archival")
            else:
                success = database.mark_file_for_archive(mark)
                if success:
                    console.print(f"✅ Marked file {mark} for archival")
                else:
                    console.print(f"❌ Failed to mark file {mark} (not found or not eligible)")
                    
        elif mark_archived:
            # Mark a file as successfully archived
            if dry_run:
                console.print(f"🔍 [DRY RUN] Would mark file {mark_archived} as archived")
            else:
                success = database.mark_file_archived(mark_archived)
                if success:
                    console.print(f"✅ Marked file {mark_archived} as successfully archived")
                else:
                    console.print(f"❌ Failed to mark file {mark_archived} as archived (not found)")
                    
        elif auto:
            # Auto-mark eligible files for archival
            import os
            from datetime import datetime, timedelta
            
            # Check if auto-archival is enabled
            auto_archive_enabled = os.getenv('AUTO_ARCHIVE_PROCESSED_FILES', 'false').lower() in ('true', '1', 'yes')
            archive_delay_days = int(os.getenv('ARCHIVE_DELAY_DAYS', '7'))
            
            if not auto_archive_enabled:
                console.print("⚠️  Auto-archival is disabled")
                console.print("   Enable by setting AUTO_ARCHIVE_PROCESSED_FILES=true in .env")
                return
            
            # Find files eligible for archival (completed files older than delay)
            cutoff_date = datetime.now() - timedelta(days=archive_delay_days)
            all_files = database.get_all_voice_files(status='completed')
            
            eligible_files = [
                f for f in all_files 
                if f.can_be_archived and f.processed_at and f.processed_at < cutoff_date
            ]
            
            if not eligible_files:
                console.print(f"📭 No files eligible for auto-archival (>{archive_delay_days} days old)")
            else:
                if dry_run:
                    console.print(f"🔍 [DRY RUN] Would mark {len(eligible_files)} files for archival:")
                    for file in eligible_files:
                        console.print(f"   • {file.file_id[:12]}... - {file.processed_at.strftime('%Y-%m-%d')}")
                else:
                    marked_count = 0
                    for file in eligible_files:
                        if database.mark_file_for_archive(file.file_id):
                            marked_count += 1
                    
                    console.print(f"✅ Marked {marked_count} files for archival")
                    
        else:
            # Default: show status and available options
            stats = database.get_archive_statistics()
            console.print("\n📊 Current Status:")
            console.print(f"   Active files: {stats['active_files']}")
            console.print(f"   Pending archive: {stats['pending_archive']}")
            console.print(f"   Archived files: {stats['archived_count']}")
            
            console.print("\n💡 Available options:")
            console.print("   --status           Show detailed archive statistics")
            console.print("   --list             List files pending archival") 
            console.print("   --mark ID          Mark specific file for archival")
            console.print("   --mark-archived ID Mark specific file as successfully archived")
            console.print("   --auto             Auto-mark eligible files for archival")
            console.print("   --dry-run          Preview changes without applying them")
            
    except ImportError as e:
        console.print("⚠️  [red]Import error - archive module dependencies missing[/red]")
        console.print(f"Details: {e}")
        console.print("💡 Make sure you're running in the virtual environment")
        
    except Exception as e:
        console.print(f"❌ Archive operation failed: {e}", style="red")
        if ctx.obj.get('verbose'):
            import traceback
            console.print("\n[dim]Stack trace:[/dim]")
            console.print(traceback.format_exc())

# Query commands removed - using pure GraphRAG now


@main.command()
@click.argument('action', type=click.Choice(['start', 'stop', 'restart', 'status']))
@click.option('--interval', default=300, help='Processing interval in seconds')
@click.pass_context
def service(ctx: click.Context, action: str, interval: int) -> None:
    """Manage the voice processing service daemon"""
    import subprocess
    
    service_script = Path(__file__).parent.parent.parent / "scripts" / "services" / "voice-processing-service.py"
    
    if not service_script.exists():
        console.print(f"❌ Service script not found at {service_script}", style="red")
        return
        
    cmd = [sys.executable, str(service_script), action]
    if action in ['start', 'restart']:
        cmd.extend(['--interval', str(interval)])
        
    try:
        console.print(f"🔧 Running service command: {action}")
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        
        if result.stdout:
            console.print(result.stdout.strip())
        if result.stderr:
            console.print(result.stderr.strip(), style="red")
            
        sys.exit(result.returncode)
    except Exception as e:
        console.print(f"❌ Service command failed: {e}", style="red")
        sys.exit(1)


if __name__ == '__main__':
    main()