"""
Voice Processing Core
Enhanced main automation logic for processing voice recordings.

This module replaces the script-based automated-voice-processor.py with a
clean, testable, and well-structured class-based implementation.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..models.voice_file import VoiceFile
from ..models.task import NotionTask
from ..integrations.drive import GoogleDriveClient
from ..integrations.whisper import WhisperClient
from ..integrations.notion import NotionClient
from ..utils.logging import VoiceLogger
from ..utils.database import VoiceDatabase

class VoiceProcessor:
    """
    Enhanced voice processing automation system
    
    This class orchestrates the entire voice-to-task pipeline:
    1. Discover voice files in Google Drive
    2. Download and validate audio content
    3. Transcribe using OpenAI Whisper
    4. Create Notion tasks
    5. Track processing state and cleanup
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the voice processor
        
        Args:
            project_root: Project root directory (auto-detected if None)
        """
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # Initialize logging system
        self.logger = VoiceLogger(self.project_root)
        
        # Initialize database
        self.database = VoiceDatabase(self.project_root)
        
        # Load environment configuration first
        self._load_environment()
        
        # Initialize API clients
        try:
            self.drive_client = GoogleDriveClient(logger=self.logger)
            self.whisper_client = WhisperClient(logger=self.logger)
            self.notion_client = NotionClient(logger=self.logger)
        except ValueError as e:
            self.logger.error("Failed to initialize API clients", exception=e)
            raise
    
    def _load_environment(self) -> None:
        """Load and validate environment configuration"""
        env_file = self.project_root / '.env'
        if env_file.exists():
            # Load environment variables from .env file
            with open(env_file) as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        try:
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
                        except ValueError:
                            continue
        
        # Validate required environment variables
        required_vars = ['OPENAI_API_KEY', 'NOTION_TOKEN', 'NOTION_TASKS_DB']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        self.logger.debug("Environment configuration loaded successfully")
    
    def process_all_files(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Process all available voice files
        
        Args:
            dry_run: If True, simulate processing without making changes
            
        Returns:
            Dictionary containing processing results and statistics
        """
        self.logger.start_run()
        
        try:
            # Discover voice files
            voice_files = self.discover_voice_files()
            self.logger.update_run_stats(files_found=len(voice_files))
            
            if not voice_files:
                self.logger.info("📭 No audio files found in Drive folder")
                summary = self.logger.log_run_summary(len(voice_files), 0, 0, 0)
                return {
                    'success': True,
                    'processed': 0,
                    'total_found': 0,
                    'message': 'No files to process',
                    'run_summary': summary,
                    'dry_run': dry_run
                }
            
            # Filter out already processed files
            unprocessed_files = self._filter_unprocessed_files(voice_files)
            
            if not unprocessed_files:
                self.logger.info("📋 All discovered files have already been processed")
                summary = self.logger.log_run_summary(len(voice_files), 0, 0, 0)
                return {
                    'success': True,
                    'processed': 0,
                    'total_found': len(voice_files),
                    'message': 'All files already processed',
                    'run_summary': summary,
                    'dry_run': dry_run
                }
            
            # Process each unprocessed file
            results = []
            processed_count = 0
            
            for voice_file in unprocessed_files:
                if dry_run:
                    self.logger.info(f"🔍 [DRY RUN] Would process file: {voice_file.file_id}")
                    continue
                
                result = self.process_single_file(voice_file)
                if result:
                    results.append(result)
                    processed_count += 1
                    
                    # Send desktop notification
                    self._send_notification(voice_file, success=True)
                    
                    # Cleanup processed file if enabled
                    self._cleanup_processed_file(voice_file)
                else:
                    self._send_notification(voice_file, success=False)
            
            # Update final statistics
            self.logger.update_run_stats(files_processed=processed_count)
            
            # Generate comprehensive run summary
            additional_data = {
                'database_url': self.notion_client.format_database_url(),
                'dry_run': dry_run,
                'unprocessed_files': len(unprocessed_files),
                'notification_system_available': self._is_notification_system_available()
            }
            
            summary = self.logger.log_run_summary(
                files_found=len(voice_files),
                files_processed=processed_count,
                additional_data=additional_data
            )
            
            success_message = "🎉 Voice processing automation completed"
            if dry_run:
                success_message += " (DRY RUN)"
            
            self.logger.info(
                success_message,
                files_processed=processed_count,
                total_files=len(voice_files)
            )
            
            return {
                'success': True,
                'processed': processed_count,
                'total_found': len(voice_files),
                'unprocessed_found': len(unprocessed_files),
                'results': results,
                'run_summary': summary,
                'database_url': additional_data['database_url'],
                'dry_run': dry_run
            }
            
        except Exception as e:
            self.logger.error("Critical error in main automation loop", exception=e)
            summary = self.logger.log_run_summary(
                files_found=self.logger.current_run_data.get('files_found', 0),
                files_processed=self.logger.current_run_data.get('files_processed', 0),
                errors=self.logger.current_run_data.get('errors', 0) + 1
            )
            return {
                'success': False,
                'error': str(e),
                'run_summary': summary,
                'dry_run': dry_run
            }
    
    def discover_voice_files(self) -> List[VoiceFile]:
        """
        Discover voice files from Google Drive
        
        Returns:
            List of discovered VoiceFile objects
        """
        self.logger.info("🔍 Starting voice file discovery")
        voice_files = self.drive_client.scan_folder()
        
        # Save discovered files to database (only if not already processed)
        for voice_file in voice_files:
            existing_file = self.database.get_voice_file(voice_file.file_id)
            if not existing_file or existing_file.status == 'discovered':
                # Only save new files or update discovered files
                self.database.save_voice_file(voice_file)
            else:
                # File already exists with processing status - don't overwrite
                self.logger.debug("Preserving existing file status", 
                                file_id=voice_file.file_id, 
                                existing_status=existing_file.status)
        
        return voice_files
    
    def _filter_unprocessed_files(self, voice_files: List[VoiceFile]) -> List[VoiceFile]:
        """Filter out files that have already been processed"""
        unprocessed = []
        
        for voice_file in voice_files:
            if not self.database.is_file_processed(voice_file.file_id):
                unprocessed.append(voice_file)
            else:
                self.logger.info("⏭️ Skipping already processed file", file_id=voice_file.file_id)
        
        return unprocessed
    
    def process_single_file(self, voice_file: VoiceFile) -> Optional[Dict[str, Any]]:
        """
        Process a single voice file through the complete pipeline
        
        Args:
            voice_file: VoiceFile object to process
            
        Returns:
            Dictionary with processing results or None if failed
        """
        self.logger.info("🎤 Processing voice file", file_id=voice_file.file_id)
        
        try:
            # Mark as processing and save state
            voice_file.mark_processing()
            self.database.save_voice_file(voice_file)
            
            # Step 1: Download audio file
            audio_content = self.drive_client.download_file(voice_file)
            if not audio_content:
                voice_file.mark_failed("Failed to download audio file")
                self.database.save_voice_file(voice_file)
                return None
            
            # Step 2: Validate audio format
            is_valid, validation_message = self.whisper_client.validate_audio_format(voice_file)
            if not is_valid:
                voice_file.mark_failed(f"Audio validation failed: {validation_message}")
                self.database.save_voice_file(voice_file)
                return None
            
            # Step 3: Transcribe with Whisper
            transcription_result = self.whisper_client.transcribe_with_retry(voice_file, audio_content)
            if not transcription_result:
                voice_file.mark_failed("Transcription failed")
                self.database.save_voice_file(voice_file)
                return None
            
            transcript_text = transcription_result['text']
            duration = transcription_result.get('duration', 0)
            
            # Step 4: Create Notion task
            notion_task = self.notion_client.create_task_from_voice(voice_file, transcript_text)
            if not notion_task:
                voice_file.mark_failed("Failed to create Notion task")
                self.database.save_voice_file(voice_file)
                return None
            
            # Step 5: Mark as completed and save
            voice_file.mark_completed(transcript_text, notion_task.url, duration)
            self.database.save_voice_file(voice_file)
            
            # Save the Notion task to database
            self.database.save_task(notion_task)
            
            self.logger.success("File processing completed successfully", file_id=voice_file.file_id)
            
            return {
                'file_id': voice_file.file_id,
                'transcript': transcript_text,
                'task_url': notion_task.url,
                'task_id': notion_task.task_id,
                'duration': duration,
                'transcript_length': len(transcript_text),
                'word_count': transcription_result.get('word_count', 0),
                'processing_time': voice_file.processing_duration
            }
            
        except Exception as e:
            error_message = f"Unexpected error during processing: {str(e)}"
            voice_file.mark_failed(error_message)
            self.database.save_voice_file(voice_file)
            
            self.logger.error(
                "Unexpected error during voice file processing",
                exception=e,
                file_id=voice_file.file_id
            )
            return None
    
    def _cleanup_processed_file(self, voice_file: VoiceFile) -> None:
        """Handle cleanup of processed voice files"""
        cleanup_success = self.drive_client.cleanup_processed_file(voice_file)
        
        if cleanup_success:
            self.logger.success("File cleanup completed", file_id=voice_file.file_id)
        else:
            self.logger.debug("File cleanup skipped or failed", file_id=voice_file.file_id)
    
    def _send_notification(self, voice_file: VoiceFile, success: bool) -> None:
        """Send desktop notification about processing result"""
        try:
            notification_script = self.project_root / 'scripts' / 'notification-system.py'
            if not notification_script.exists():
                return
            
            if success:
                # Get the processed file info for notification
                processed_file = self.database.get_voice_file(voice_file.file_id)
                if processed_file and processed_file.transcript and processed_file.task_url:
                    subprocess.run([
                        sys.executable, str(notification_script), 'success',
                        voice_file.file_id, 
                        processed_file.transcript[:100], 
                        processed_file.task_url
                    ], check=False, timeout=10)
            else:
                subprocess.run([
                    sys.executable, str(notification_script), 'error',
                    voice_file.file_id,
                    "Processing failed",
                    ""
                ], check=False, timeout=10)
                
        except Exception as e:
            self.logger.warning("Desktop notification failed", exception=e, file_id=voice_file.file_id)
    
    def _is_notification_system_available(self) -> bool:
        """Check if the notification system is available"""
        notification_script = self.project_root / 'scripts' / 'notification-system.py'
        return notification_script.exists()
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        return self.database.get_processing_stats()
    
    def test_system_health(self) -> Dict[str, Any]:
        """
        Test the health of all system components
        
        Returns:
            Dictionary with health check results
        """
        health_results = {
            'overall_health': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }
        
        # Test database
        try:
            stats = self.database.get_processing_stats()
            health_results['components']['database'] = {
                'status': 'healthy',
                'total_files': stats['total_files']
            }
        except Exception as e:
            health_results['components']['database'] = {
                'status': 'error',
                'error': str(e)
            }
            health_results['overall_health'] = 'degraded'
        
        # Test Google Drive
        try:
            # Quick folder access test
            import requests
            response = requests.head(self.drive_client.folder_url, timeout=10)
            health_results['components']['google_drive'] = {
                'status': 'healthy' if response.ok else 'warning',
                'folder_accessible': response.ok
            }
        except Exception as e:
            health_results['components']['google_drive'] = {
                'status': 'error',
                'error': str(e)
            }
            health_results['overall_health'] = 'degraded'
        
        # Test Notion API
        notion_test = self.notion_client.test_connection()
        health_results['components']['notion'] = {
            'status': 'healthy' if (notion_test['api_connection'] and notion_test['database_access']) else 'error',
            'api_connection': notion_test['api_connection'],
            'database_access': notion_test['database_access'],
            'errors': notion_test['errors']
        }
        
        if notion_test['errors']:
            health_results['overall_health'] = 'degraded'
        
        # Test OpenAI (basic validation)
        try:
            whisper_info = self.whisper_client.get_supported_formats()
            health_results['components']['openai_whisper'] = {
                'status': 'healthy',
                'supported_formats': len(whisper_info['formats'])
            }
        except Exception as e:
            health_results['components']['openai_whisper'] = {
                'status': 'error',
                'error': str(e)
            }
            health_results['overall_health'] = 'degraded'
        
        return health_results