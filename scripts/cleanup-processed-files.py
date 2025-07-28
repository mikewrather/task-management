#!/usr/bin/env python3
"""
Voice Files Cleanup Manager
Comprehensive tool for managing processed voice files and Google Drive storage.

This script provides cleanup management for the voice task management system by:
1. Tracking all processed voice files from the SQLite database
2. Providing cleanup guidance and statistics
3. Generating manual cleanup instructions with direct links
4. Supporting future automated cleanup when Drive API is integrated

Current Capabilities:
- List all processed files with timestamps and transcripts
- Show cleanup statistics and storage recommendations  
- Generate step-by-step manual cleanup guides
- Calculate storage usage and cleanup benefits

Integration with Voice Processing:
- Works with data from automated-voice-processor.py
- Uses the same SQLite database (data/processed_files.db)
- Follows the same logging patterns via voice_logging.py
- Respects CLEANUP_PROCESSED_FILES configuration

Future Enhancements:
- Automated file renaming via Google Drive API
- Bulk cleanup operations with confirmation prompts
- Integration with notification system for cleanup reminders
- Advanced cleanup policies (keep recent, archive old, etc.)

Usage:
    python scripts/cleanup-processed-files.py [options]
    
    Options:
        --list     List all processed files with details
        --guide    Show manual cleanup instructions
        --stats    Display cleanup statistics and recommendations
        (no args) Show summary stats and guidance if cleanup needed

Environment Variables:
    CLEANUP_PROCESSED_FILES: Enable/disable cleanup tracking
    CLEANUP_DELAY_HOURS: Hours before files are eligible for cleanup

Dependencies:
    - sqlite3: For accessing processed files database
    - voice_logging: For consistent logging (optional)
    - pathlib: For file system operations
"""

import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from voice_logging import VoiceLogger

def load_processed_files():
    """
    Load processed voice files from the SQLite database
    
    Reads the processed_files table created by automated-voice-processor.py
    and returns a list of file records with parsed timestamps.
    
    Returns:
        list: List of dictionaries containing:
            - file_id: Google Drive file ID
            - processed_at: datetime object when file was processed
            - transcript: Full transcript text from Whisper
            - task_url: URL of created Notion task
    
    Raises:
        sqlite3.Error: If database access fails
    """
    db_path = project_root / 'data' / 'processed_files.db'
    
    if not db_path.exists():
        return []
    
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute('''
            SELECT file_id, processed_at, transcript, task_url 
            FROM processed_files 
            ORDER BY processed_at DESC
        ''')
        
        files = []
        for row in cursor.fetchall():
            files.append({
                'file_id': row[0],
                'processed_at': datetime.fromisoformat(row[1]),
                'transcript': row[2],
                'task_url': row[3]
            })
        
        return files
        
    finally:
        conn.close()

def show_processed_files_list():
    """Show list of processed files that could be cleaned up"""
    files = load_processed_files()
    
    if not files:
        print("📭 No processed files found in database")
        return
    
    print(f"📋 Found {len(files)} processed voice files:")
    print("=" * 80)
    
    for i, file in enumerate(files, 1):
        age = datetime.now() - file['processed_at']
        transcript_preview = file['transcript'][:60] + "..." if len(file['transcript']) > 60 else file['transcript']
        
        print(f"{i:2d}. File ID: {file['file_id']}")
        print(f"    Processed: {file['processed_at'].strftime('%Y-%m-%d %H:%M:%S')} ({age.days} days ago)")
        print(f"    Transcript: \"{transcript_preview}\"")
        print(f"    Notion Task: {file['task_url']}")
        print()

def show_cleanup_guide():
    """Show manual cleanup instructions"""
    files = load_processed_files()
    cleanup_candidates = [f for f in files if (datetime.now() - f['processed_at']).days >= 1]
    
    print("🧹 VOICE FILES CLEANUP GUIDE")
    print("=" * 50)
    print()
    
    if not cleanup_candidates:
        print("✅ No files need cleanup (all processed within last 24 hours)")
        return
    
    print(f"📁 Found {len(cleanup_candidates)} files ready for cleanup")
    print()
    
    print("📋 MANUAL CLEANUP STEPS:")
    print("1. Open Google Drive folder: https://drive.google.com/drive/folders/1vUNQV617t5mXHtyYrGro6Q3K-6JCmuUj")
    print("2. Look for these processed files:")
    print()
    
    for i, file in enumerate(cleanup_candidates[:10], 1):  # Show first 10
        days_old = (datetime.now() - file['processed_at']).days
        transcript_preview = file['transcript'][:40] + "..." if len(file['transcript']) > 40 else file['transcript']
        
        print(f"   {i:2d}. \"{transcript_preview}\" ({days_old} days old)")
        print(f"       File ID: {file['file_id']}")
        print(f"       Direct link: https://drive.google.com/file/d/{file['file_id']}/view")
        print()
    
    if len(cleanup_candidates) > 10:
        print(f"   ... and {len(cleanup_candidates) - 10} more files")
        print()
    
    print("🗑️ CLEANUP OPTIONS:")
    print("   A. DELETE: Permanently remove files (saves space)")
    print("   B. RENAME: Add 'PROCESSED_' prefix (keeps for reference)")
    print("   C. MOVE: Create 'processed' subfolder and move files")
    print()
    
    print("⚠️  IMPORTANT NOTES:")
    print("   - Files are safe to delete (already transcribed and stored in Notion)")
    print("   - Keep files if you want to verify transcription accuracy")
    print("   - Original audio is preserved in Notion task descriptions")
    print()
    
    # Show automated cleanup option
    print("🤖 FUTURE AUTOMATION:")
    print("   To enable automatic cleanup tracking (when Drive API is implemented):")
    print("   Add to .env file: CLEANUP_PROCESSED_FILES=true")

def show_cleanup_stats():
    """Show cleanup statistics"""
    files = load_processed_files()
    
    if not files:
        print("📊 No processed files data available")
        return
    
    now = datetime.now()
    
    # Calculate age groups
    age_groups = {
        'today': 0,
        'week': 0,
        'month': 0,
        'older': 0
    }
    
    total_transcript_length = 0
    
    for file in files:
        age = now - file['processed_at']
        total_transcript_length += len(file['transcript'])
        
        if age.days == 0:
            age_groups['today'] += 1
        elif age.days <= 7:
            age_groups['week'] += 1
        elif age.days <= 30:
            age_groups['month'] += 1
        else:
            age_groups['older'] += 1
    
    print("📊 CLEANUP STATISTICS")
    print("=" * 40)
    print(f"Total processed files:    {len(files):4d}")
    print(f"Processed today:          {age_groups['today']:4d}")
    print(f"Processed this week:      {age_groups['week']:4d}")
    print(f"Processed this month:     {age_groups['month']:4d}")
    print(f"Older than 1 month:       {age_groups['older']:4d}")
    print()
    print(f"Total transcript text:    {total_transcript_length:4d} characters")
    print(f"Average per file:         {total_transcript_length // max(len(files), 1):4d} characters")
    print()
    
    # Cleanup recommendations
    cleanup_ready = age_groups['week'] + age_groups['month'] + age_groups['older']
    if cleanup_ready > 0:
        print(f"🧹 CLEANUP RECOMMENDATIONS:")
        print(f"   Files ready for cleanup: {cleanup_ready}")
        print(f"   Estimated space to reclaim: ~{cleanup_ready * 100}KB")
        print(f"   Run: python scripts/cleanup-processed-files.py --guide")
    else:
        print("✅ No cleanup needed - all files are recent")

def main():
    parser = argparse.ArgumentParser(description='Manage processed voice files cleanup')
    parser.add_argument('--list', action='store_true', help='List all processed files')
    parser.add_argument('--guide', action='store_true', help='Show manual cleanup guide')
    parser.add_argument('--stats', action='store_true', help='Show cleanup statistics')
    
    args = parser.parse_args()
    
    if args.list:
        show_processed_files_list()
    elif args.guide:
        show_cleanup_guide()
    elif args.stats:
        show_cleanup_stats()
    else:
        # Default: show stats and guide if cleanup is needed
        show_cleanup_stats()
        print()
        
        files = load_processed_files()
        cleanup_candidates = [f for f in files if (datetime.now() - f['processed_at']).days >= 1]
        
        if cleanup_candidates:
            print("💡 TIP: Run with --guide flag for cleanup instructions")

if __name__ == "__main__":
    main()