#!/usr/bin/env python3
"""
Automated Voice Processing Script for Cron
Scans Google Drive folder and processes new voice files automatically.

Features:
- Automated Google Drive folder scanning
- OpenAI Whisper transcription
- Notion task creation
- Comprehensive logging and monitoring
- Duplicate prevention with SQLite tracking
- Desktop notifications

Usage: python3 scripts/automated-voice-processor.py

Logs:
- Detailed processing: logs/voice-automation.log
- Run summaries: logs/cron-run-history.log
- Error tracking: logs/voice-errors.log
"""

import requests
import os
import json
import sqlite3
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import centralized logging system
from voice_logging import VoiceLogger

def setup_env():
    """Load environment variables from .env file"""
    env_file = project_root / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def setup_db():
    """Initialize SQLite database to track processed files"""
    db_path = project_root / 'data' / 'processed_files.db'
    db_path.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS processed_files (
            file_id TEXT PRIMARY KEY,
            processed_at TIMESTAMP,
            transcript TEXT,
            task_url TEXT
        )
    ''')
    conn.commit()
    return conn

# Logging is now handled by the centralized VoiceLogger class
# (imported from voice_logging.py)

def scan_drive_folder(logger: VoiceLogger) -> List[str]:
    """
    Scan Google Drive folder for audio files
    
    Args:
        logger: VoiceLogger instance for consistent logging
        
    Returns:
        List of Google Drive file IDs for potential audio files
    """
    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '1vUNQV617t5mXHtyYrGro6Q3K-6JCmuUj')
    folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
    
    logger.info("🔍 Scanning Google Drive folder", folder_id=folder_id)
    
    try:
        response = requests.get(folder_url, timeout=30)
        if not response.ok:
            logger.warning("Failed to access Google Drive folder", 
                         status_code=response.status_code, folder_id=folder_id)
            return []
        
        html = response.text
        
        # Enhanced pattern to find file IDs in Google Drive HTML
        import re
        
        # Get all potential Google Drive file IDs from the folder
        all_ids = re.findall(r'"([a-zA-Z0-9_-]{28,33})"', html)
        potential_ids = [id for id in set(all_ids) if id != folder_id]
        
        logger.debug(f"Found {len(potential_ids)} potential file IDs to validate")
        
        # Validate which IDs are actually audio files by checking their headers
        file_ids = set()
        for file_id in potential_ids:
            try:
                # Quick HEAD request to check if it's an audio file
                test_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                test_response = requests.head(test_url, timeout=5, allow_redirects=True)
                
                if test_response.ok:
                    content_type = test_response.headers.get('content-type', '')
                    content_length = int(test_response.headers.get('content-length', '0'))
                    
                    # Check if it's an audio file or large enough to be audio
                    if ('audio' in content_type or 
                        content_length > 50000):  # Assume files > 50KB might be audio
                        file_ids.add(file_id)
                        logger.debug(f"Validated audio file: {file_id} ({content_type}, {content_length} bytes)")
                
            except Exception as e:
                logger.debug(f"Failed to validate file {file_id}: {e}")
                continue
        
        logger.info(f"📁 Found {len(file_ids)} potential audio files", count=len(file_ids))
        return list(file_ids)
        
    except Exception as e:
        logger.error("Error scanning Google Drive folder", exception=e, folder_id=folder_id)
        return []

def is_file_processed(conn, file_id):
    """Check if file has already been processed"""
    cursor = conn.execute('SELECT file_id FROM processed_files WHERE file_id = ?', (file_id,))
    return cursor.fetchone() is not None

def process_voice_file(file_id: str, logger: VoiceLogger) -> Optional[Dict[str, Any]]:
    """
    Process a single voice file through the complete pipeline
    
    Args:
        file_id: Google Drive file ID
        logger: VoiceLogger instance for consistent logging
        
    Returns:
        Dictionary with processing results or None if failed
    """
    logger.info("🎤 Processing voice file", file_id=file_id)
    
    try:
        # Step 1: Download audio file from Google Drive
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        audio_response = requests.get(download_url, timeout=60)
        
        if not audio_response.ok:
            logger.error("Failed to download audio file from Google Drive", 
                        file_id=file_id, status_code=audio_response.status_code)
            return None
        
        # Validate audio content
        content_type = audio_response.headers.get('content-type', '')
        content_size = len(audio_response.content)
        
        if 'audio' not in content_type and content_size < 1000:
            logger.warning("File doesn't appear to be valid audio content", 
                          file_id=file_id, content_type=content_type, size_bytes=content_size)
            return None
        
        logger.success("Audio file downloaded successfully", 
                      file_id=file_id, size_bytes=content_size)
        
        # Step 2: Transcribe with OpenAI Whisper
        logger.info("🎙️ Starting transcription with OpenAI Whisper", file_id=file_id)
        
        files = {'file': ('audio.m4a', audio_response.content, 'audio/m4a')}
        data = {
            'model': 'whisper-1',
            'response_format': 'verbose_json'
        }
        headers = {
            'Authorization': f"Bearer {os.getenv('OPENAI_API_KEY')}"
        }
        
        transcribe_response = requests.post(
            'https://api.openai.com/v1/audio/transcriptions',
            headers=headers,
            files=files,
            data=data,
            timeout=120
        )
        
        if not transcribe_response.ok:
            logger.error("OpenAI Whisper transcription failed", 
                        file_id=file_id, response_text=transcribe_response.text)
            return None
        
        transcription = transcribe_response.json()
        transcript_text = transcription.get('text', '').strip()
        duration = transcription.get('duration', 0)
        
        if not transcript_text:
            logger.warning("Transcription resulted in empty text", 
                          file_id=file_id, duration=duration)
            return None
        
        logger.success("Transcription completed successfully", 
                      file_id=file_id, transcript_length=len(transcript_text), 
                      duration_seconds=duration, preview=transcript_text[:100])
        
        # Step 3: Create task in Notion
        logger.info("📝 Creating Notion task", file_id=file_id)
        
        notion_headers = {
            'Authorization': f"Bearer {os.getenv('NOTION_TOKEN')}",
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        
        # Create concise title
        title_text = transcript_text[:60] + "..." if len(transcript_text) > 60 else transcript_text
        
        task_data = {
            "parent": {"database_id": os.getenv('NOTION_TASKS_DB')},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": f"Voice Note: {title_text}"}}]
                },
                "Status": {
                    "status": {"name": "Inbox"}
                },
                "Contexts": {
                    "multi_select": [
                        {"name": "voice"},
                        {"name": "auto-processed"}
                    ]
                }
            }
        }
        
        # Add full transcript as page content for longer texts
        if len(transcript_text) > 100:
            task_data["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": f"Full transcript: {transcript_text}"}}]
                    }
                }
            ]
        
        notion_response = requests.post(
            'https://api.notion.com/v1/pages',
            headers=notion_headers,
            json=task_data,
            timeout=30
        )
        
        if notion_response.ok:
            task_result = notion_response.json()
            task_url = task_result.get('url', 'Unknown')
            
            logger.success("Notion task created successfully", 
                          file_id=file_id, task_url=task_url)
            
            return {
                'file_id': file_id,
                'transcript': transcript_text,
                'task_url': task_url,
                'duration': duration,
                'transcript_length': len(transcript_text)
            }
        else:
            logger.error("Notion API request failed", 
                        file_id=file_id, response_text=notion_response.text)
            return None
            
    except Exception as e:
        logger.error("Unexpected error during voice file processing", 
                    exception=e, file_id=file_id)
        return None

def mark_as_processed(conn, file_id, transcript, task_url):
    """Mark file as processed in database"""
    conn.execute(
        'INSERT OR REPLACE INTO processed_files (file_id, processed_at, transcript, task_url) VALUES (?, ?, ?, ?)',
        (file_id, datetime.now(), transcript, task_url)
    )
    conn.commit()

def cleanup_processed_file(file_id: str, logger: VoiceLogger) -> bool:
    """
    Track processed files for cleanup and prepare for future automated cleanup
    
    This function handles post-processing file management by:
    1. Checking if cleanup is enabled in configuration
    2. Logging cleanup intent for manual or future automated processing
    3. Preparing infrastructure for Google Drive API integration
    
    Current Implementation:
    - Tracks files that have been processed successfully
    - Logs cleanup requests for manual management via cleanup-processed-files.py
    - Provides foundation for future Drive API automation
    
    Future Enhancement:
    - Will automatically rename files with "PROCESSED_" prefix
    - Will move files to "processed" subfolder
    - Will integrate with Google Drive API for authenticated operations
    
    Args:
        file_id: Google Drive file ID of the processed audio file
        logger: VoiceLogger instance for consistent logging and error tracking
        
    Returns:
        bool: True if cleanup tracking was successful, False if disabled or failed
        
    Environment Variables:
        CLEANUP_PROCESSED_FILES: Set to 'true' to enable cleanup tracking
        CLEANUP_DELAY_HOURS: Hours to wait before marking files for cleanup (default: 24)
    """
    # Check if cleanup functionality is enabled
    cleanup_enabled = os.getenv('CLEANUP_PROCESSED_FILES', 'false').lower() in ('true', '1', 'yes')
    
    if not cleanup_enabled:
        logger.debug("File cleanup disabled - set CLEANUP_PROCESSED_FILES=true to enable", 
                    file_id=file_id)
        return False
    
    try:
        # Log cleanup intent for tracking and manual management
        logger.info("🧹 Marking file for cleanup tracking", 
                   file_id=file_id, 
                   cleanup_method="manual_via_cleanup_script")
        
        # Current implementation: Track cleanup intent in logs
        # This enables the cleanup-processed-files.py script to provide guidance
        cleanup_timestamp = datetime.now().isoformat()
        
        logger.debug("File marked for cleanup tracking", 
                    file_id=file_id, 
                    cleanup_timestamp=cleanup_timestamp,
                    management_tool="scripts/cleanup-processed-files.py")
        
        # Future implementation placeholder:
        # When Google Drive API is integrated, this will:
        # 1. Get current file metadata via Drive API
        # 2. Rename file to "PROCESSED_{timestamp}_{original_name}"
        # 3. Or move file to "processed" subfolder
        # 4. Update file permissions if needed
        
        return True
        
    except Exception as e:
        logger.warning("Failed to track file for cleanup", 
                      exception=e, 
                      file_id=file_id)
        return False

def main() -> Dict[str, Any]:
    """
    Main automation function for voice processing
    
    Returns:
        Dictionary containing execution results and statistics
    """
    # Initialize centralized logging system
    logger = VoiceLogger(project_root)
    logger.start_run()
    
    setup_env()
    logger.info("📁 Project root initialized", project_root=str(project_root))
    
    # Validate environment variables
    required_vars = ['OPENAI_API_KEY', 'NOTION_TOKEN', 'NOTION_TASKS_DB']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error("Missing required environment variables", missing_vars=missing_vars)
        logger.log_run_summary(0, 0, 1, 0)
        return {'success': False, 'error': 'Missing environment variables'}
    
    # Initialize database connection
    try:
        conn = setup_db()
        logger.debug("Database connection established")
    except Exception as e:
        logger.error("Failed to initialize database", exception=e)
        logger.log_run_summary(0, 0, 1, 0)
        return {'success': False, 'error': 'Database initialization failed'}
    
    try:
        # Scan Google Drive for voice files
        file_ids = scan_drive_folder(logger)
        logger.update_run_stats(files_found=len(file_ids))
        
        if not file_ids:
            logger.info("📭 No audio files found in Drive folder")
            summary = logger.log_run_summary(len(file_ids), 0, 0, 0)
            return {
                'success': True, 
                'processed': 0, 
                'total_found': 0,
                'message': 'No files to process',
                'run_summary': summary
            }
        
        # Process each discovered file
        results = []
        processed_count = 0
        
        for file_id in file_ids:
            if is_file_processed(conn, file_id):
                logger.info("⏭️ Skipping already processed file", file_id=file_id)
                continue
            
            result = process_voice_file(file_id, logger)
            if result:
                mark_as_processed(conn, file_id, result['transcript'], result['task_url'])
                results.append(result)
                processed_count += 1
                
                logger.success("File processing completed successfully", file_id=file_id)
                
                # Attempt to clean up the processed file
                cleanup_success = cleanup_processed_file(file_id, logger)
                if cleanup_success:
                    logger.success("File cleanup completed", file_id=file_id)
                else:
                    logger.debug("File cleanup skipped or failed", file_id=file_id)
                
                # Send desktop notifications
                try:
                    notification_script = Path(__file__).parent / 'notification-system.py'
                    if notification_script.exists():
                        subprocess.run([
                            sys.executable, str(notification_script), 'success',
                            file_id, result['transcript'][:100], result['task_url']
                        ], check=False, timeout=10)
                except Exception as e:
                    logger.warning("Desktop notification failed", exception=e, file_id=file_id)
        
        # Update final statistics
        logger.update_run_stats(files_processed=processed_count)
        
        # Log comprehensive run summary
        additional_data = {
            'database_url': 'https://www.notion.so/183267fb-e1c1-4b3b-a42a-5ac1ab8353eb',
            'notification_system_available': (Path(__file__).parent / 'notification-system.py').exists()
        }
        
        summary = logger.log_run_summary(
            files_found=len(file_ids),
            files_processed=processed_count, 
            additional_data=additional_data
        )
        
        logger.info("🎉 Voice processing automation completed", 
                   files_processed=processed_count, total_files=len(file_ids))
        
        return {
            'success': True,
            'processed': processed_count,
            'total_found': len(file_ids),
            'results': results,
            'run_summary': summary,
            'database_url': additional_data['database_url']
        }
        
    except Exception as e:
        logger.error("Critical error in main automation loop", exception=e)
        summary = logger.log_run_summary(
            files_found=logger.current_run_data.get('files_found', 0),
            files_processed=logger.current_run_data.get('files_processed', 0),
            errors=logger.current_run_data.get('errors', 0) + 1
        )
        return {'success': False, 'error': str(e), 'run_summary': summary}
        
    finally:
        # Clean up database connection
        try:
            conn.close()
            logger.debug("Database connection closed")
        except:
            pass

if __name__ == "__main__":
    result = main()
    
    if result['success']:
        if result.get('processed', 0) > 0:
            print(f"\n🎉 Successfully processed {result['processed']} voice files!")
            print(f"📋 Check your tasks: {result.get('database_url', '')}")
        else:
            print("\n📭 No new files to process")
    else:
        print(f"\n❌ Automation failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)