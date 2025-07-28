"""
Voice Files Cleanup Manager
Enhanced cleanup management for processed voice files with automation support.

This module replaces cleanup-processed-files.py with enhanced features:
- Integration with the new database system and models
- Advanced cleanup policies and automation
- Rich console output and better user experience
- Preparation for Google Drive API integration
- Safe cleanup operations with confirmation prompts
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from io import StringIO

from ..utils.logging import VoiceLogger
from ..utils.database import VoiceDatabase
from ..models.voice_file import VoiceFile
from ..integrations.drive import GoogleDriveClient

try:
    from rich.console import Console
    from rich.table import Table
    from rich.prompt import Confirm
    from rich.progress import track
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

class VoiceCleanup:
    """Enhanced voice files cleanup management system"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the cleanup manager
        
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
        
        # Configuration
        self.cleanup_enabled = os.getenv('CLEANUP_PROCESSED_FILES', 'false').lower() in ('true', '1', 'yes')
        self.cleanup_delay_hours = int(os.getenv('CLEANUP_DELAY_HOURS', '24'))
        
        # Google Drive folder URL
        folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '1vUNQV617t5mXHtyYrGro6Q3K-6JCmuUj')
        self.drive_folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
    
    def list_processed_files(self) -> str:
        """
        List all processed files that could be cleaned up
        
        Returns:
            Formatted string with file list
        """
        files = self.database.get_all_voice_files(status='completed')
        
        if not files:
            return "📭 No processed files found in database"
        
        output = StringIO()
        output.write(f"📋 Found {len(files)} processed voice files:\n")
        output.write("=" * 80 + "\n\n")
        
        for i, file in enumerate(files, 1):
            age = datetime.now() - file.processed_at if file.processed_at else timedelta(0)
            transcript_preview = (file.transcript[:60] + "...") if file.transcript and len(file.transcript) > 60 else (file.transcript or "No transcript")
            
            output.write(f"{i:2d}. File ID: {file.file_id}\n")
            output.write(f"    Processed: {file.processed_at.strftime('%Y-%m-%d %H:%M:%S') if file.processed_at else 'Unknown'} ({age.days} days ago)\n")
            output.write(f"    Size: {file.file_size_mb}MB\n" if file.file_size else "")
            output.write(f"    Transcript: \"{transcript_preview}\"\n")
            output.write(f"    Notion Task: {file.task_url or 'No URL'}\n")
            output.write(f"    Google Drive: {file.google_drive_url}\n")
            output.write("\n")
        
        return output.getvalue()
    
    def show_cleanup_guide(self) -> str:
        """
        Generate manual cleanup instructions
        
        Returns:
            Formatted cleanup guide
        """
        files = self.database.get_all_voice_files(status='completed')
        cleanup_cutoff = datetime.now() - timedelta(hours=self.cleanup_delay_hours)
        cleanup_candidates = [f for f in files if f.processed_at and f.processed_at < cleanup_cutoff]
        
        output = StringIO()
        output.write("🧹 VOICE FILES CLEANUP GUIDE\n")
        output.write("=" * 50 + "\n\n")
        
        if not cleanup_candidates:
            output.write(f"✅ No files need cleanup (all processed within last {self.cleanup_delay_hours} hours)\n")
            return output.getvalue()
        
        output.write(f"📁 Found {len(cleanup_candidates)} files ready for cleanup\n\n")
        
        # Calculate cleanup benefits
        total_size = sum(f.file_size or 0 for f in cleanup_candidates)
        total_size_mb = total_size / (1024 * 1024) if total_size else 0
        
        output.write("📊 CLEANUP BENEFITS:\n")
        output.write(f"   Files to clean: {len(cleanup_candidates)}\n")
        if total_size_mb > 0:
            output.write(f"   Storage to reclaim: ~{total_size_mb:.1f}MB\n")
        output.write(f"   Database records: {len(cleanup_candidates)} (will be preserved)\n\n")
        
        output.write("📋 MANUAL CLEANUP STEPS:\n")
        output.write(f"1. Open Google Drive folder: {self.drive_folder_url}\n")
        output.write("2. Look for these processed files:\n\n")
        
        # Show up to 10 files with details
        for i, file in enumerate(cleanup_candidates[:10], 1):
            days_old = (datetime.now() - file.processed_at).days if file.processed_at else 0
            transcript_preview = (file.transcript[:40] + "...") if file.transcript and len(file.transcript) > 40 else (file.transcript or "No transcript")
            
            output.write(f"   {i:2d}. \"{transcript_preview}\" ({days_old} days old)\n")
            output.write(f"       File ID: {file.file_id}\n")
            output.write(f"       Direct link: {file.google_drive_url}\n")
            if file.file_size_mb:
                output.write(f"       Size: {file.file_size_mb}MB\n")
            output.write("\n")
        
        if len(cleanup_candidates) > 10:
            output.write(f"   ... and {len(cleanup_candidates) - 10} more files\n\n")
        
        output.write("🗑️ CLEANUP OPTIONS:\n")
        output.write("   A. DELETE: Permanently remove files (saves space)\n")
        output.write("   B. RENAME: Add 'PROCESSED_' prefix (keeps for reference)\n")
        output.write("   C. MOVE: Create 'processed' subfolder and move files\n\n")
        
        output.write("⚠️  SAFETY NOTES:\n")
        output.write("   - Files are safe to delete (transcripts stored in Notion)\n")
        output.write("   - Database records are preserved for analytics\n")
        output.write("   - Keep files if you want to verify transcription accuracy\n")
        output.write("   - Notion tasks contain the full transcript text\n\n")
        
        # Show automation status
        if self.cleanup_enabled:
            output.write("🤖 AUTOMATION STATUS: ✅ ENABLED\n")
            output.write(f"   Auto-cleanup delay: {self.cleanup_delay_hours} hours\n")
            output.write("   Future versions will handle cleanup automatically\n")
        else:
            output.write("🤖 AUTOMATION STATUS: ❌ DISABLED\n")
            output.write("   To enable: Add CLEANUP_PROCESSED_FILES=true to .env\n")
        
        return output.getvalue()
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cleanup statistics
        
        Returns:
            Dictionary with cleanup statistics
        """
        files = self.database.get_all_voice_files(status='completed')
        
        if not files:
            return {'error': 'No processed files data available'}
        
        now = datetime.now()
        cleanup_cutoff = now - timedelta(hours=self.cleanup_delay_hours)
        
        # Calculate age groups
        age_groups = {
            'today': [],
            'week': [],
            'month': [],
            'older': []
        }
        
        total_size = 0
        total_transcript_length = 0
        
        for file in files:
            if not file.processed_at:
                continue
                
            age = now - file.processed_at
            if file.file_size:
                total_size += file.file_size
            if file.transcript:
                total_transcript_length += len(file.transcript)
            
            if age.days == 0:
                age_groups['today'].append(file)
            elif age.days <= 7:
                age_groups['week'].append(file)
            elif age.days <= 30:
                age_groups['month'].append(file)
            else:
                age_groups['older'].append(file)
        
        # Cleanup candidates
        cleanup_ready = [f for f in files if f.processed_at and f.processed_at < cleanup_cutoff]
        cleanup_size = sum(f.file_size or 0 for f in cleanup_ready)
        
        return {
            'total_files': len(files),
            'age_groups': {k: len(v) for k, v in age_groups.items()},
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2) if total_size else 0,
            'total_transcript_length': total_transcript_length,
            'avg_transcript_length': total_transcript_length // max(len(files), 1),
            'cleanup_ready_count': len(cleanup_ready),
            'cleanup_size_bytes': cleanup_size,
            'cleanup_size_mb': round(cleanup_size / (1024 * 1024), 2) if cleanup_size else 0,
            'cleanup_enabled': self.cleanup_enabled,
            'cleanup_delay_hours': self.cleanup_delay_hours,
            'oldest_file': min(files, key=lambda f: f.processed_at or datetime.now()) if files else None,
            'newest_file': max(files, key=lambda f: f.processed_at or datetime.min) if files else None
        }
    
    def format_cleanup_stats(self) -> str:
        """Format cleanup statistics for display"""
        stats = self.get_cleanup_stats()
        
        if 'error' in stats:
            return f"📊 {stats['error']}"
        
        output = StringIO()
        output.write("📊 CLEANUP STATISTICS\n")
        output.write("=" * 40 + "\n")
        output.write(f"Total processed files:    {stats['total_files']:4d}\n")
        output.write(f"Processed today:          {stats['age_groups']['today']:4d}\n")
        output.write(f"Processed this week:      {stats['age_groups']['week']:4d}\n")
        output.write(f"Processed this month:     {stats['age_groups']['month']:4d}\n")
        output.write(f"Older than 1 month:       {stats['age_groups']['older']:4d}\n\n")
        
        if stats['total_size_mb'] > 0:
            output.write(f"Total storage used:       {stats['total_size_mb']:.1f}MB\n")
            output.write(f"Average file size:        {stats['total_size_mb']/max(stats['total_files'], 1):.1f}MB\n\n")
        
        output.write(f"Total transcript text:    {stats['total_transcript_length']:4d} characters\n")
        output.write(f"Average per file:         {stats['avg_transcript_length']:4d} characters\n\n")
        
        # Cleanup recommendations
        if stats['cleanup_ready_count'] > 0:
            output.write("🧹 CLEANUP RECOMMENDATIONS:\n")
            output.write(f"   Files ready for cleanup: {stats['cleanup_ready_count']}\n")
            if stats['cleanup_size_mb'] > 0:
                output.write(f"   Storage to reclaim:      {stats['cleanup_size_mb']:.1f}MB\n")
            output.write(f"   Run: vtm cleanup --guide\n")
        else:
            output.write("✅ No cleanup needed - all files are recent\n")
        
        # Configuration status
        output.write(f"\n🤖 AUTOMATION: {'✅ ENABLED' if stats['cleanup_enabled'] else '❌ DISABLED'}\n")
        if stats['cleanup_enabled']:
            output.write(f"   Cleanup delay: {stats['cleanup_delay_hours']} hours\n")
        
        return output.getvalue()
    
    def auto_cleanup(self, dry_run: bool = False) -> str:
        """
        Perform automated cleanup of processed files
        
        Args:
            dry_run: If True, show what would be cleaned without doing it
            
        Returns:
            Formatted results of cleanup operation
        """
        if not self.cleanup_enabled and not dry_run:
            return "❌ Automated cleanup is disabled. Set CLEANUP_PROCESSED_FILES=true to enable."
        
        files = self.database.get_all_voice_files(status='completed')
        cleanup_cutoff = datetime.now() - timedelta(hours=self.cleanup_delay_hours)
        cleanup_candidates = [f for f in files if f.processed_at and f.processed_at < cleanup_cutoff]
        
        output = StringIO()
        
        if dry_run:
            output.write("🔍 DRY RUN - Automated Cleanup Preview\n")
        else:
            output.write("🤖 Automated Cleanup Operation\n")
        
        output.write("=" * 50 + "\n\n")
        
        if not cleanup_candidates:
            output.write(f"✅ No files ready for cleanup (all processed within {self.cleanup_delay_hours} hours)\n")
            return output.getvalue()
        
        output.write(f"📁 Found {len(cleanup_candidates)} files ready for cleanup\n")
        
        # Calculate benefits
        total_size = sum(f.file_size or 0 for f in cleanup_candidates)
        if total_size > 0:
            output.write(f"💾 Storage to reclaim: {total_size / (1024 * 1024):.1f}MB\n")
        
        output.write("\n")
        
        if dry_run:
            output.write("Would clean up these files:\n")
            for file in cleanup_candidates[:5]:  # Show first 5
                days_old = (datetime.now() - file.processed_at).days if file.processed_at else 0
                output.write(f"   • {file.file_id} ({days_old} days old)\n")
            
            if len(cleanup_candidates) > 5:
                output.write(f"   ... and {len(cleanup_candidates) - 5} more files\n")
        else:
            # Future implementation: Actually perform cleanup via Google Drive API
            output.write("🚧 AUTOMATED CLEANUP NOT YET IMPLEMENTED\n")
            output.write("Current implementation tracks cleanup intent only.\n")
            output.write("Future versions will integrate with Google Drive API for:\n")
            output.write("   • Automatic file renaming with PROCESSED_ prefix\n")
            output.write("   • Moving files to 'processed' subfolder\n")
            output.write("   • Bulk deletion with safety confirmations\n")
            output.write("\n")
            output.write("For now, use: vtm cleanup --guide\n")
        
        return output.getvalue()
    
    def interactive_cleanup(self) -> str:
        """
        Run interactive cleanup with user prompts (when Rich is available)
        
        Returns:
            Results of interactive cleanup session
        """
        if not HAS_RICH:
            return "Interactive cleanup requires Rich library. Use --guide for manual instructions."
        
        files = self.database.get_all_voice_files(status='completed')
        cleanup_cutoff = datetime.now() - timedelta(hours=self.cleanup_delay_hours)
        cleanup_candidates = [f for f in files if f.processed_at and f.processed_at < cleanup_cutoff]
        
        if not cleanup_candidates:
            return f"✅ No files ready for cleanup (all processed within {self.cleanup_delay_hours} hours)"
        
        self.console.print(f"🧹 Found {len(cleanup_candidates)} files ready for cleanup")
        
        # Show summary table
        table = Table(title="Files Ready for Cleanup")
        table.add_column("Age", style="yellow")
        table.add_column("File ID", style="cyan")
        table.add_column("Transcript Preview", style="white")
        table.add_column("Size", style="green")
        
        for file in cleanup_candidates[:10]:  # Show first 10
            age_days = (datetime.now() - file.processed_at).days if file.processed_at else 0
            transcript_preview = (file.transcript[:40] + "...") if file.transcript and len(file.transcript) > 40 else (file.transcript or "No transcript")
            size_str = f"{file.file_size_mb}MB" if file.file_size_mb else "Unknown"
            
            table.add_row(
                f"{age_days}d",
                file.file_id[:12] + "...",
                transcript_preview,
                size_str
            )
        
        self.console.print(table)
        
        if len(cleanup_candidates) > 10:
            self.console.print(f"... and {len(cleanup_candidates) - 10} more files")
        
        # Ask user what to do
        self.console.print("\n🤖 Automated cleanup is not yet implemented.")
        self.console.print("Would you like to see the manual cleanup guide?")
        
        if Confirm.ask("Show cleanup guide?"):
            return self.show_cleanup_guide()
        else:
            return "Cleanup cancelled by user."
    
    def purge_old_database_records(self, days_old: int = 90, dry_run: bool = False) -> str:
        """
        Clean up old database records (not the actual files)
        
        Args:
            days_old: Remove records older than this many days
            dry_run: If True, show what would be removed without doing it
            
        Returns:
            Results of purge operation
        """
        if dry_run:
            # For dry run, just count what would be removed
            cutoff_date = datetime.now() - timedelta(days=days_old)
            files = self.database.get_all_voice_files()
            old_files = [f for f in files if f.processed_at and f.processed_at < cutoff_date]
            
            return f"🔍 DRY RUN: Would remove {len(old_files)} database records older than {days_old} days"
        else:
            # Actually remove old records
            removed_count = self.database.cleanup_old_records(days_old)
            
            output = StringIO()
            output.write(f"🗑️ Database cleanup completed\n")
            output.write(f"Removed {removed_count} records older than {days_old} days\n")
            
            if removed_count > 0:
                output.write("Note: This only removes database records, not actual files\n")
                output.write("Files in Google Drive are unaffected\n")
            
            return output.getvalue()