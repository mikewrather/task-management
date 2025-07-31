"""End-to-end integration tests for complete API workflow"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

from voice_task_manager.core.processor import VoiceProcessor
from voice_task_manager.models.voice_file import VoiceFile


class TestAPIIntegrationFlow:
    """Integration tests for complete API workflow from Drive -> OpenAI -> Notion"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / 'data').mkdir()
            (temp_path / 'logs').mkdir()
            (temp_path / 'temp').mkdir()
            yield temp_path
    
    @pytest.fixture
    def voice_processor(self, temp_project_root):
        """Create a VoiceProcessor instance with mocked integrations"""
        return VoiceProcessor(temp_project_root)
    
    @pytest.fixture
    def sample_audio_data(self):
        """Create sample audio data"""
        return b"fake_audio_data_for_integration_testing" * 1000
    
    @pytest.mark.integration
    @patch('voice_task_manager.core.processor.GoogleDriveClient')
    @patch('voice_task_manager.core.processor.WhisperClient')
    @patch('voice_task_manager.core.processor.NotionClient')
    @patch('voice_task_manager.core.processor.VoiceDatabase')
    def test_complete_processing_workflow_success(
        self, mock_db_class, mock_notion_class, mock_transcriber_class, 
        mock_drive_class, voice_processor, sample_audio_data
    ):
        """Test complete successful workflow: Drive -> Transcribe -> Notion -> Database"""
        
        # Mock Google Drive Integration
        mock_drive = Mock()
        mock_drive.list_audio_files.return_value = {
            'success': True,
            'files': [
                {
                    'id': 'drive_file_123',
                    'name': 'voice_recording.m4a',
                    'size': '1024000',
                    'createdTime': '2025-01-24T10:00:00Z'
                }
            ]
        }
        mock_drive.download_file.return_value = {
            'success': True,
            'file_path': '/tmp/voice_recording.m4a',
            'file_size': 1024000
        }
        mock_drive_class.return_value = mock_drive
        
        # Mock Voice Transcriber (OpenAI)
        mock_transcriber = Mock()
        mock_transcriber.transcribe_audio.return_value = {
            'success': True,
            'transcript': 'Create a task to review the quarterly financial reports and prepare summary for board meeting',
            'processing_time': 15.2,
            'confidence': 0.95
        }
        mock_transcriber_class.return_value = mock_transcriber
        
        # Mock Notion Integration
        mock_notion = Mock()
        mock_notion.create_task.return_value = {
            'success': True,
            'task_id': 'notion_task_123',
            'task_url': 'https://notion.so/quarterly-financial-review-123'
        }
        mock_notion_class.return_value = mock_notion
        
        # Mock Database
        mock_db = Mock()
        mock_db.is_file_processed.return_value = False  # New file
        mock_db.save_voice_file.return_value = None
        mock_db.save_task.return_value = None
        mock_db_class.return_value = mock_db
        
        # Execute complete workflow
        result = voice_processor.process_all_files()
        
        # Verify workflow steps
        assert result['success'] is True
        assert result['processed_count'] >= 1
        
        # Verify Drive interaction
        mock_drive.list_audio_files.assert_called_once()
        mock_drive.download_file.assert_called_once_with(
            'drive_file_123', 
            voice_processor.temp_dir / 'voice_recording.m4a'
        )
        
        # Verify Transcription
        mock_transcriber.transcribe_audio.assert_called_once()
        
        # Verify Notion task creation
        mock_notion.create_task.assert_called_once()
        task_data = mock_notion.create_task.call_args[0][0]
        assert 'quarterly financial reports' in task_data['content'].lower()
        
        # Verify Database operations
        mock_db.save_voice_file.assert_called_once()
        mock_db.save_task.assert_called_once()
    
    @pytest.mark.integration
    @patch('voice_task_manager.core.processor.GoogleDriveClient')
    @patch('voice_task_manager.core.processor.WhisperClient')
    @patch('voice_task_manager.core.processor.NotionClient')
    @patch('voice_task_manager.core.processor.VoiceDatabase')
    def test_processing_workflow_with_transcription_failure(
        self, mock_db_class, mock_notion_class, mock_transcriber_class, 
        mock_drive_class, voice_processor
    ):
        """Test workflow handling transcription failure gracefully"""
        
        # Mock successful Drive operations
        mock_drive = Mock()
        mock_drive.list_audio_files.return_value = {
            'success': True,
            'files': [{'id': 'file_1', 'name': 'corrupted.m4a'}]
        }
        mock_drive.download_file.return_value = {
            'success': True,
            'file_path': '/tmp/corrupted.m4a',
            'file_size': 500
        }
        mock_drive_class.return_value = mock_drive
        
        # Mock transcription failure
        mock_transcriber = Mock()
        mock_transcriber.transcribe_audio.return_value = {
            'success': False,
            'error': 'Audio file is corrupted or invalid format'
        }
        mock_transcriber_class.return_value = mock_transcriber
        
        # Mock database
        mock_db = Mock()
        mock_db.is_file_processed.return_value = False
        mock_db.save_voice_file.return_value = None
        mock_db_class.return_value = mock_db
        
        # Notion should not be called due to transcription failure
        mock_notion = Mock()
        mock_notion_class.return_value = mock_notion
        
        result = voice_processor.process_all_files()
        
        # Verify graceful error handling
        assert 'error_count' in result
        assert result['error_count'] >= 1
        
        # Verify transcription was attempted
        mock_transcriber.transcribe_audio.assert_called_once()
        
        # Verify Notion was NOT called due to transcription failure
        mock_notion.create_task.assert_not_called()
        
        # Verify file was saved with failed status
        mock_db.save_voice_file.assert_called_once()
        saved_file = mock_db.save_voice_file.call_args[0][0]
        assert saved_file.status == 'failed'
        assert 'corrupted' in saved_file.error_message.lower()
    
    @pytest.mark.integration
    @patch('voice_task_manager.core.processor.GoogleDriveClient')
    @patch('voice_task_manager.core.processor.WhisperClient')
    @patch('voice_task_manager.core.processor.NotionClient')  
    @patch('voice_task_manager.core.processor.VoiceDatabase')
    def test_processing_workflow_with_notion_failure(
        self, mock_db_class, mock_notion_class, mock_transcriber_class,
        mock_drive_class, voice_processor
    ):
        """Test workflow handling Notion API failure gracefully"""
        
        # Mock successful Drive and transcription
        mock_drive = Mock()
        mock_drive.list_audio_files.return_value = {
            'success': True,
            'files': [{'id': 'file_1', 'name': 'good_audio.m4a'}]
        }
        mock_drive.download_file.return_value = {
            'success': True,
            'file_path': '/tmp/good_audio.m4a'
        }
        mock_drive_class.return_value = mock_drive
        
        mock_transcriber = Mock()
        mock_transcriber.transcribe_audio.return_value = {
            'success': True,
            'transcript': 'Schedule meeting with client next week'
        }
        mock_transcriber_class.return_value = mock_transcriber
        
        # Mock Notion failure
        mock_notion = Mock()
        mock_notion.create_task.return_value = {
            'success': False,
            'error': 'Notion API rate limit exceeded',
            'status_code': 429
        }
        mock_notion_class.return_value = mock_notion
        
        # Mock database
        mock_db = Mock()
        mock_db.is_file_processed.return_value = False
        mock_db.save_voice_file.return_value = None
        mock_db_class.return_value = mock_db
        
        result = voice_processor.process_all_files()
        
        # Verify transcription succeeded but task creation failed
        mock_transcriber.transcribe_audio.assert_called_once()
        mock_notion.create_task.assert_called_once()
        
        # Verify file was saved with appropriate status
        mock_db.save_voice_file.assert_called_once()
        saved_file = mock_db.save_voice_file.call_args[0][0]
        
        # Should have transcript but no task URL due to Notion failure
        assert saved_file.transcript == 'Schedule meeting with client next week'
        assert saved_file.status == 'failed'  # or 'partial' depending on implementation
    
    @pytest.mark.integration
    @patch('voice_task_manager.core.processor.GoogleDriveClient')
    @patch('voice_task_manager.core.processor.VoiceDatabase')
    def test_drive_integration_error_handling(
        self, mock_db_class, mock_drive_class, voice_processor
    ):
        """Test handling of Drive API connection errors"""
        
        # Mock Drive connection failure
        mock_drive = Mock()
        mock_drive.list_audio_files.side_effect = Exception("Drive API connection failed")
        mock_drive_class.return_value = mock_drive
        
        # Mock database
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        result = voice_processor.process_all_files()
        
        # Should handle Drive errors gracefully
        assert result['success'] is False
        assert 'Drive API connection failed' in result.get('error', '')
    
    @pytest.mark.integration
    @patch('voice_task_manager.core.processor.GoogleDriveClient')
    @patch('voice_task_manager.core.processor.WhisperClient')
    @patch('voice_task_manager.core.processor.NotionClient')
    @patch('voice_task_manager.core.processor.VoiceDatabase')
    def test_duplicate_file_handling(
        self, mock_db_class, mock_notion_class, mock_transcriber_class,
        mock_drive_class, voice_processor
    ):
        """Test proper handling of already processed files"""
        
        # Mock Drive with duplicate file
        mock_drive = Mock()
        mock_drive.list_audio_files.return_value = {
            'success': True,
            'files': [{'id': 'already_processed_file', 'name': 'old_recording.m4a'}]
        }
        mock_drive_class.return_value = mock_drive
        
        # Mock database showing file already processed
        mock_db = Mock()
        mock_db.is_file_processed.return_value = True  # Already processed
        mock_db_class.return_value = mock_db
        
        # These should not be called for already processed files
        mock_transcriber = Mock()
        mock_transcriber_class.return_value = mock_transcriber
        mock_notion = Mock()
        mock_notion_class.return_value = mock_notion
        
        result = voice_processor.process_all_files()
        
        # Verify duplicate detection
        mock_db.is_file_processed.assert_called_once_with('already_processed_file')
        
        # Verify processing was skipped
        mock_transcriber.transcribe_audio.assert_not_called()
        mock_notion.create_task.assert_not_called()
        
        # Should report skipped files
        assert 'skipped_count' in result
        assert result['skipped_count'] >= 1
    
    @pytest.mark.integration
    @patch('voice_task_manager.core.processor.GoogleDriveClient')
    @patch('voice_task_manager.core.processor.WhisperClient')
    @patch('voice_task_manager.core.processor.NotionClient')
    @patch('voice_task_manager.core.processor.VoiceDatabase')
    @patch('voice_task_manager.core.processor.NotificationSystem')
    def test_notification_integration_success(
        self, mock_notification_class, mock_db_class, mock_notion_class,
        mock_transcriber_class, mock_drive_class, voice_processor
    ):
        """Test notification system integration for successful processing"""
        
        # Mock successful workflow
        mock_drive = Mock()
        mock_drive.list_audio_files.return_value = {
            'success': True,
            'files': [{'id': 'notification_test', 'name': 'test.m4a'}]
        }
        mock_drive.download_file.return_value = {'success': True, 'file_path': '/tmp/test.m4a'}
        mock_drive_class.return_value = mock_drive
        
        mock_transcriber = Mock()
        mock_transcriber.transcribe_audio.return_value = {
            'success': True,
            'transcript': 'Test notification transcript'
        }
        mock_transcriber_class.return_value = mock_transcriber
        
        mock_notion = Mock()
        mock_notion.create_task.return_value = {
            'success': True,
            'task_id': 'test_task',
            'task_url': 'https://notion.so/test-task'
        }
        mock_notion_class.return_value = mock_notion
        
        mock_db = Mock()
        mock_db.is_file_processed.return_value = False
        mock_db.save_voice_file.return_value = None
        mock_db.save_task.return_value = None
        mock_db_class.return_value = mock_db
        
        # Mock notification system
        mock_notifications = Mock()
        mock_notifications.notify_processing_success.return_value = {
            'desktop': True,
            'email': True,
            'console': True
        }
        mock_notification_class.return_value = mock_notifications
        
        result = voice_processor.process_all_files()
        
        # Verify notification was sent
        mock_notifications.notify_processing_success.assert_called_once()
        
        # Check notification call arguments
        call_args = mock_notifications.notify_processing_success.call_args
        voice_file_arg = call_args[0][0]
        notion_task_arg = call_args[0][1]
        
        assert isinstance(voice_file_arg, VoiceFile)
        assert voice_file_arg.file_id == 'notification_test'
        assert notion_task_arg is not None
    
    @pytest.mark.integration
    @patch('voice_task_manager.core.processor.GoogleDriveClient') 
    @patch('voice_task_manager.core.processor.WhisperClient')
    @patch('voice_task_manager.core.processor.NotionClient')
    @patch('voice_task_manager.core.processor.VoiceDatabase')
    def test_batch_processing_performance(
        self, mock_db_class, mock_notion_class, mock_transcriber_class,
        mock_drive_class, voice_processor
    ):
        """Test performance with batch processing of multiple files"""
        
        # Mock multiple files for batch processing
        mock_drive = Mock()
        mock_drive.list_audio_files.return_value = {
            'success': True,
            'files': [
                {'id': f'batch_file_{i}', 'name': f'recording_{i}.m4a'}
                for i in range(10)  # 10 files for batch test
            ]
        }
        
        # Mock successful downloads
        def mock_download(file_id, path):
            return {'success': True, 'file_path': str(path)}
        mock_drive.download_file.side_effect = mock_download
        mock_drive_class.return_value = mock_drive
        
        # Mock successful transcriptions
        mock_transcriber = Mock()
        def mock_transcribe(file_path):
            file_num = str(file_path).split('_')[-1].split('.')[0]
            return {
                'success': True,
                'transcript': f'Batch transcript number {file_num}',
                'processing_time': 2.5
            }
        mock_transcriber.transcribe_audio.side_effect = mock_transcribe
        mock_transcriber_class.return_value = mock_transcriber
        
        # Mock successful task creation
        mock_notion = Mock()
        def mock_create_task(task_data):
            return {
                'success': True,
                'task_id': f"batch_task_{hash(task_data['content']) % 1000}",
                'task_url': 'https://notion.so/batch-task'
            }
        mock_notion.create_task.side_effect = mock_create_task
        mock_notion_class.return_value = mock_notion
        
        # Mock database
        mock_db = Mock()
        mock_db.is_file_processed.return_value = False
        mock_db.save_voice_file.return_value = None
        mock_db.save_task.return_value = None
        mock_db_class.return_value = mock_db
        
        import time
        start_time = time.time()
        result = voice_processor.process_all_files()
        processing_time = time.time() - start_time
        
        # Verify batch processing results
        assert result['processed_count'] == 10
        assert result['success_count'] == 10
        assert result['error_count'] == 0
        
        # Verify all components were called for each file
        assert mock_transcriber.transcribe_audio.call_count == 10
        assert mock_notion.create_task.call_count == 10
        assert mock_db.save_voice_file.call_count == 10
        
        # Performance check (should process 10 files reasonably quickly)
        assert processing_time < 30  # Should complete within 30 seconds
    
    @pytest.mark.integration
    @patch('voice_task_manager.core.processor.GoogleDriveClient')
    @patch('voice_task_manager.core.processor.WhisperClient')
    @patch('voice_task_manager.core.processor.NotionClient')
    @patch('voice_task_manager.core.processor.VoiceDatabase')
    def test_retry_mechanism_integration(
        self, mock_db_class, mock_notion_class, mock_transcriber_class,
        mock_drive_class, voice_processor
    ):
        """Test retry mechanisms across different API integrations"""
        
        # Mock Drive with initial failure then success
        mock_drive = Mock()
        mock_drive.list_audio_files.side_effect = [
            Exception("Temporary network error"),
            {
                'success': True,
                'files': [{'id': 'retry_test', 'name': 'retry.m4a'}]
            }
        ]
        mock_drive.download_file.return_value = {'success': True, 'file_path': '/tmp/retry.m4a'}
        mock_drive_class.return_value = mock_drive
        
        # Mock transcriber with retry logic
        mock_transcriber = Mock()
        mock_transcriber.transcribe_audio.side_effect = [
            {'success': False, 'error': 'Rate limit exceeded'},
            {'success': True, 'transcript': 'Retry successful transcript'}
        ]
        mock_transcriber_class.return_value = mock_transcriber
        
        # Mock Notion with retry
        mock_notion = Mock()
        mock_notion.create_task.side_effect = [
            {'success': False, 'error': 'Temporary server error'},
            {'success': True, 'task_id': 'retry_task', 'task_url': 'https://notion.so/retry-task'}
        ]
        mock_notion_class.return_value = mock_notion
        
        # Mock database
        mock_db = Mock()
        mock_db.is_file_processed.return_value = False
        mock_db.save_voice_file.return_value = None
        mock_db.save_task.return_value = None
        mock_db_class.return_value = mock_db
        
        with patch('time.sleep'):  # Speed up retry delays
            result = voice_processor.process_all_files(max_retries=2)
            
            # Should eventually succeed with retries
            assert result['success_count'] >= 1
            
            # Verify retry attempts were made
            assert mock_drive.list_audio_files.call_count == 2
            assert mock_transcriber.transcribe_audio.call_count == 2
            assert mock_notion.create_task.call_count == 2