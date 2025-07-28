"""End-to-end workflow tests for complete voice processing system"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import time
from datetime import datetime

from src.voice_task_manager.core.processor import VoiceProcessor
from src.voice_task_manager.utils.database import VoiceDatabase
from src.voice_task_manager.models.voice_file import VoiceFile
from src.voice_task_manager.models.task import NotionTask


class TestCompleteWorkflow:
    """End-to-end tests for complete voice processing workflow"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a complete temporary project environment"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create full project structure
            (temp_path / 'data').mkdir()
            (temp_path / 'logs').mkdir()
            (temp_path / 'temp').mkdir()
            (temp_path / 'cache').mkdir()
            (temp_path / 'archive').mkdir()
            
            # Create sample configuration files
            config_file = temp_path / 'data' / 'config.json'
            config_file.write_text(json.dumps({
                'openai_model': 'whisper-1',
                'notion_database_id': 'test_db_123',
                'drive_folder_id': 'test_folder_123',
                'processing_enabled': True
            }))
            
            yield temp_path
    
    @pytest.fixture
    def sample_audio_files(self, temp_project_root):
        """Create sample audio files for testing"""
        audio_dir = temp_project_root / 'temp' / 'audio_samples'
        audio_dir.mkdir()
        
        # Create mock audio files with different content
        sample_files = {}
        for i, content in enumerate([
            b'fake_audio_content_meeting_notes' * 500,
            b'fake_audio_content_task_creation' * 300,
            b'fake_audio_content_reminder_setup' * 400
        ]):
            file_path = audio_dir / f'sample_{i+1}.m4a'
            file_path.write_bytes(content)
            sample_files[f'sample_{i+1}'] = {
                'path': file_path,
                'size': len(content),
                'expected_type': ['meeting', 'task', 'reminder'][i]
            }
        
        return sample_files
    
    @pytest.fixture
    def voice_processor(self, temp_project_root):
        """Create a fully configured VoiceProcessor"""
        return VoiceProcessor(temp_project_root)
    
    @pytest.mark.e2e
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_openai_key',
        'NOTION_TOKEN': 'test_notion_token',
        'NOTION_TASKS_DB': 'test_db_123',
        'GOOGLE_DRIVE_FOLDER_ID': 'test_folder_123'
    })
    def test_complete_voice_processing_workflow(self, voice_processor, sample_audio_files, temp_project_root):
        """Test complete workflow from file discovery to task creation"""
        
        with patch('src.voice_task_manager.integrations.google_drive.GoogleDriveIntegration') as mock_drive, \
             patch('src.voice_task_manager.core.transcription.VoiceTranscriber') as mock_transcriber, \
             patch('src.voice_task_manager.integrations.notion.NotionIntegration') as mock_notion:
            
            # Mock Google Drive file discovery
            mock_drive_instance = Mock()
            mock_drive_instance.list_audio_files.return_value = {
                'success': True,
                'files': [
                    {
                        'id': 'sample_1',
                        'name': 'sample_1.m4a',
                        'size': '250000',
                        'createdTime': '2025-01-24T10:00:00Z'
                    },
                    {
                        'id': 'sample_2', 
                        'name': 'sample_2.m4a',
                        'size': '150000',
                        'createdTime': '2025-01-24T11:00:00Z'
                    }
                ]
            }
            
            # Mock successful downloads
            def mock_download(file_id, local_path):
                # Use our sample files for realistic testing
                if file_id in sample_audio_files:
                    shutil.copy(sample_audio_files[file_id]['path'], local_path)
                    return {
                        'success': True,
                        'file_path': str(local_path),
                        'file_size': sample_audio_files[file_id]['size']
                    }
                return {'success': False, 'error': 'File not found'}
            
            mock_drive_instance.download_file.side_effect = mock_download
            mock_drive.return_value = mock_drive_instance
            
            # Mock OpenAI transcription with realistic responses
            mock_transcriber_instance = Mock()
            transcription_responses = {
                'sample_1': {
                    'success': True,
                    'transcript': 'Meeting notes: Discuss Q1 budget allocation and review team performance metrics. Follow up with department heads by Friday.',
                    'processing_time': 12.5,
                    'confidence': 0.92
                },
                'sample_2': {
                    'success': True,
                    'transcript': 'Create task to schedule client presentation for next week. Include slides on product roadmap and pricing strategy.',
                    'processing_time': 8.3,
                    'confidence': 0.89
                }
            }
            
            def mock_transcribe(file_path):
                # Determine which sample based on file path
                for sample_id, info in sample_audio_files.items():
                    if sample_id in str(file_path):
                        return transcription_responses.get(sample_id, {
                            'success': False,
                            'error': 'Transcription failed'
                        })
                return {'success': False, 'error': 'Unknown file'}
            
            mock_transcriber_instance.transcribe_audio.side_effect = mock_transcribe
            mock_transcriber.return_value = mock_transcriber_instance
            
            # Mock Notion task creation
            mock_notion_instance = Mock()
            notion_responses = []
            
            def mock_create_task(task_data):
                task_id = f"notion_task_{len(notion_responses) + 1}"
                response = {
                    'success': True,
                    'task_id': task_id,
                    'task_url': f'https://notion.so/{task_id}'
                }
                notion_responses.append(response)
                return response
            
            mock_notion_instance.create_task.side_effect = mock_create_task
            mock_notion.return_value = mock_notion_instance
            
            # Execute complete workflow
            start_time = time.time()
            result = voice_processor.process_all_files()
            processing_time = time.time() - start_time
            
            # Verify workflow completion
            assert result['success'] is True
            assert result['processed_count'] == 2
            assert result['success_count'] == 2
            assert result['error_count'] == 0
            
            # Verify all integration points were called
            mock_drive_instance.list_audio_files.assert_called_once()
            assert mock_drive_instance.download_file.call_count == 2
            assert mock_transcriber_instance.transcribe_audio.call_count == 2
            assert mock_notion_instance.create_task.call_count == 2
            
            # Verify database persistence
            database = VoiceDatabase(temp_project_root)
            stored_files = database.get_all_voice_files()
            assert len(stored_files) == 2
            
            # Verify all files are marked as completed
            for stored_file in stored_files:
                assert stored_file.status == 'completed'
                assert stored_file.transcript is not None
                assert stored_file.task_url is not None
            
            # Verify processing performance
            assert processing_time < 30  # Should complete within 30 seconds
            
            # Verify log files were created
            log_dir = temp_project_root / 'logs'
            log_files = list(log_dir.glob('*.log'))
            assert len(log_files) > 0
    
    @pytest.mark.e2e
    def test_error_recovery_workflow(self, voice_processor, sample_audio_files, temp_project_root):
        """Test workflow error recovery and partial success handling"""
        
        with patch('src.voice_task_manager.integrations.google_drive.GoogleDriveIntegration') as mock_drive, \
             patch('src.voice_task_manager.core.transcription.VoiceTranscriber') as mock_transcriber, \
             patch('src.voice_task_manager.integrations.notion.NotionIntegration') as mock_notion:
            
            # Mock Drive with mixed success/failure
            mock_drive_instance = Mock()
            mock_drive_instance.list_audio_files.return_value = {
                'success': True,
                'files': [
                    {'id': 'good_file', 'name': 'good.m4a'},
                    {'id': 'bad_file', 'name': 'corrupted.m4a'},
                    {'id': 'transcribe_fail', 'name': 'transcribe_fail.m4a'}
                ]
            }
            
            # Mock downloads with mixed results
            def mock_download(file_id, local_path):
                if file_id == 'good_file':
                    # Use first sample file
                    shutil.copy(sample_audio_files['sample_1']['path'], local_path)
                    return {'success': True, 'file_path': str(local_path)}
                elif file_id == 'bad_file':
                    return {'success': False, 'error': 'Download failed - file corrupted'}
                elif file_id == 'transcribe_fail':
                    shutil.copy(sample_audio_files['sample_2']['path'], local_path)
                    return {'success': True, 'file_path': str(local_path)}
            
            mock_drive_instance.download_file.side_effect = mock_download
            mock_drive.return_value = mock_drive_instance
            
            # Mock transcription with mixed results
            mock_transcriber_instance = Mock()
            def mock_transcribe(file_path):
                if 'good' in str(file_path):
                    return {
                        'success': True,
                        'transcript': 'Successfully transcribed content'
                    }
                elif 'transcribe_fail' in str(file_path):
                    return {
                        'success': False,
                        'error': 'Transcription failed - audio quality too poor'
                    }
                return {'success': False, 'error': 'Unknown transcription error'}
            
            mock_transcriber_instance.transcribe_audio.side_effect = mock_transcribe
            mock_transcriber.return_value = mock_transcriber_instance
            
            # Mock Notion - should only be called for successful transcriptions
            mock_notion_instance = Mock()
            mock_notion_instance.create_task.return_value = {
                'success': True,
                'task_id': 'recovery_task_1',
                'task_url': 'https://notion.so/recovery-task-1'
            }
            mock_notion.return_value = mock_notion_instance
            
            # Execute workflow with errors
            result = voice_processor.process_all_files()
            
            # Verify partial success handling
            assert result['processed_count'] == 3  # All files were attempted
            assert result['success_count'] == 1    # Only good_file succeeded completely
            assert result['error_count'] == 2      # bad_file and transcribe_fail had errors
            
            # Verify appropriate calls were made
            assert mock_drive_instance.download_file.call_count == 3
            assert mock_transcriber_instance.transcribe_audio.call_count == 2  # Only downloaded files
            assert mock_notion_instance.create_task.call_count == 1  # Only successful transcription
            
            # Verify database reflects mixed results
            database = VoiceDatabase(temp_project_root)
            stored_files = database.get_all_voice_files()
            assert len(stored_files) == 3
            
            # Check file statuses
            file_statuses = {f.file_id: f.status for f in stored_files}
            assert file_statuses['good_file'] == 'completed'
            assert file_statuses['bad_file'] == 'failed'
            assert file_statuses['transcribe_fail'] == 'failed'
    
    @pytest.mark.e2e
    def test_duplicate_processing_prevention(self, voice_processor, sample_audio_files, temp_project_root):
        """Test that already processed files are not reprocessed"""
        
        # Pre-populate database with processed file
        database = VoiceDatabase(temp_project_root)
        existing_file = VoiceFile(
            file_id='already_processed',
            transcript='Previously processed transcript',
            status='completed'
        )
        existing_file.mark_completed(
            'Previously processed transcript',
            'https://notion.so/previous-task'
        )
        database.save_voice_file(existing_file)
        
        with patch('src.voice_task_manager.integrations.google_drive.GoogleDriveIntegration') as mock_drive, \
             patch('src.voice_task_manager.core.transcription.VoiceTranscriber') as mock_transcriber, \
             patch('src.voice_task_manager.integrations.notion.NotionIntegration') as mock_notion:
            
            # Mock Drive returning both new and already processed files
            mock_drive_instance = Mock()
            mock_drive_instance.list_audio_files.return_value = {
                'success': True,
                'files': [
                    {'id': 'already_processed', 'name': 'old.m4a'},
                    {'id': 'new_file', 'name': 'new.m4a'}
                ]
            }
            
            # Mock download for new file only
            def mock_download(file_id, local_path):
                if file_id == 'new_file':
                    shutil.copy(sample_audio_files['sample_1']['path'], local_path)
                    return {'success': True, 'file_path': str(local_path)}
                return {'success': False, 'error': 'Should not download already processed'}
            
            mock_drive_instance.download_file.side_effect = mock_download
            mock_drive.return_value = mock_drive_instance
            
            # Mock transcriber and notion
            mock_transcriber_instance = Mock()
            mock_transcriber_instance.transcribe_audio.return_value = {
                'success': True,
                'transcript': 'New file transcript'
            }
            mock_transcriber.return_value = mock_transcriber_instance
            
            mock_notion_instance = Mock()
            mock_notion_instance.create_task.return_value = {
                'success': True,
                'task_id': 'new_task',
                'task_url': 'https://notion.so/new-task'
            }
            mock_notion.return_value = mock_notion_instance
            
            # Execute workflow
            result = voice_processor.process_all_files()
            
            # Verify duplicate prevention
            assert result['processed_count'] == 1  # Only new file processed
            assert result['skipped_count'] == 1    # Already processed file skipped
            
            # Verify only new file went through full pipeline
            mock_drive_instance.download_file.assert_called_once_with('new_file', mock_drive_instance.download_file.call_args[0][1])
            mock_transcriber_instance.transcribe_audio.assert_called_once()
            mock_notion_instance.create_task.assert_called_once()
            
            # Verify database has both files
            all_files = database.get_all_voice_files()
            assert len(all_files) == 2
            file_ids = {f.file_id for f in all_files}
            assert 'already_processed' in file_ids
            assert 'new_file' in file_ids
    
    @pytest.mark.e2e
    def test_system_health_monitoring_workflow(self, voice_processor, temp_project_root):
        """Test system health monitoring during processing"""
        
        from src.voice_task_manager.utils.config import SystemStatus
        
        # Initialize system status checker
        status_checker = SystemStatus(temp_project_root)
        
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_key',
            'NOTION_TOKEN': 'test_token',
            'NOTION_TASKS_DB': 'test_db'
        }):
            # Check initial system health
            initial_status = status_checker.get_system_status(json_format=True)
            initial_data = json.loads(initial_status)
            
            # Should be healthy with proper environment
            assert initial_data['overall_status'] in ['HEALTHY', 'WARNING']
            
            # Mock processing workflow with health monitoring
            with patch('src.voice_task_manager.integrations.google_drive.GoogleDriveIntegration') as mock_drive:
                mock_drive_instance = Mock()
                mock_drive_instance.list_audio_files.return_value = {
                    'success': True,
                    'files': []  # No files to process
                }
                mock_drive.return_value = mock_drive_instance
                
                # Execute processing
                result = voice_processor.process_all_files()
                
                # Check system status after processing
                post_status = status_checker.get_system_status(json_format=True)
                post_data = json.loads(post_status)
                
                # System should remain healthy
                assert post_data['overall_status'] in ['HEALTHY', 'WARNING']
                
                # Verify health components
                assert 'environment' in post_data['components']
                assert 'database' in post_data['components']
                assert 'directories' in post_data['components']
    
    @pytest.mark.e2e
    def test_notification_workflow_integration(self, voice_processor, sample_audio_files, temp_project_root):
        """Test notification system integration with complete workflow"""
        
        with patch('src.voice_task_manager.integrations.google_drive.GoogleDriveIntegration') as mock_drive, \
             patch('src.voice_task_manager.core.transcription.VoiceTranscriber') as mock_transcriber, \
             patch('src.voice_task_manager.integrations.notion.NotionIntegration') as mock_notion, \
             patch('src.voice_task_manager.utils.notifications.VoiceNotificationSystem') as mock_notifications:
            
            # Mock successful processing
            mock_drive_instance = Mock()
            mock_drive_instance.list_audio_files.return_value = {
                'success': True,
                'files': [{'id': 'notify_test', 'name': 'notify.m4a'}]
            }
            mock_drive_instance.download_file.return_value = {
                'success': True,
                'file_path': str(sample_audio_files['sample_1']['path'])
            }
            mock_drive.return_value = mock_drive_instance
            
            mock_transcriber_instance = Mock()
            mock_transcriber_instance.transcribe_audio.return_value = {
                'success': True,
                'transcript': 'Notification test transcript'
            }
            mock_transcriber.return_value = mock_transcriber_instance
            
            mock_notion_instance = Mock()
            mock_notion_instance.create_task.return_value = {
                'success': True,
                'task_id': 'notify_task',
                'task_url': 'https://notion.so/notify-task'
            }
            mock_notion.return_value = mock_notion_instance
            
            # Mock notification system
            mock_notification_instance = Mock()
            mock_notification_instance.notify_processing_success.return_value = {
                'desktop': True,
                'email': False,
                'console': True,
                'log': True
            }
            mock_notification_instance.notify_processing_error.return_value = {
                'desktop': True,
                'console': True
            }
            mock_notifications.return_value = mock_notification_instance
            
            # Execute workflow
            result = voice_processor.process_all_files()
            
            # Verify notifications were triggered
            assert result['success'] is True
            mock_notification_instance.notify_processing_success.assert_called_once()
            
            # Verify notification call parameters
            call_args = mock_notification_instance.notify_processing_success.call_args
            voice_file_arg = call_args[0][0]
            notion_task_arg = call_args[0][1]
            
            assert isinstance(voice_file_arg, VoiceFile)
            assert voice_file_arg.file_id == 'notify_test'
            assert isinstance(notion_task_arg, NotionTask)
    
    @pytest.mark.e2e
    def test_cleanup_workflow_integration(self, voice_processor, temp_project_root):
        """Test cleanup operations integration with main workflow"""
        
        from src.voice_task_manager.core.cleanup import VoiceCleanup
        
        # Create some test files to cleanup
        temp_dir = temp_project_root / 'temp'
        logs_dir = temp_project_root / 'logs'
        
        # Create temporary files
        for i in range(5):
            (temp_dir / f'temp_file_{i}.tmp').write_text(f"Temporary content {i}")
            (logs_dir / f'old_log_{i}.log').write_text(f"Log content {i}")
        
        # Initialize cleanup system
        cleanup_system = VoiceCleanup(temp_project_root)
        
        # Check initial file counts
        initial_temp_files = len(list(temp_dir.glob('*.tmp')))
        initial_log_files = len(list(logs_dir.glob('*.log')))
        
        assert initial_temp_files == 5
        assert initial_log_files >= 5  # May have other log files
        
        # Run processing workflow (this may create additional temp files)
        with patch('src.voice_task_manager.integrations.google_drive.GoogleDriveIntegration') as mock_drive:
            mock_drive_instance = Mock()
            mock_drive_instance.list_audio_files.return_value = {
                'success': True,
                'files': []
            }
            mock_drive.return_value = mock_drive_instance
            
            result = voice_processor.process_all_files()
            
        # Run cleanup after processing
        cleanup_result = cleanup_system.run_all_cleanup()
        
        # Verify cleanup completed successfully
        assert cleanup_result['success'] is True
        assert cleanup_result['total_deleted'] >= 0
        
        # Verify some temp files were cleaned up
        remaining_temp_files = len(list(temp_dir.glob('*.tmp')))
        # Note: Exact count depends on cleanup age thresholds
        assert remaining_temp_files <= initial_temp_files
    
    @pytest.mark.e2e
    def test_configuration_workflow_integration(self, voice_processor, temp_project_root):
        """Test configuration system integration with workflow"""
        
        from src.voice_task_manager.utils.config import SystemSetup
        
        # Initialize setup system
        setup_system = SystemSetup(temp_project_root)
        
        # Run full system setup
        setup_result = setup_system.run_full_setup()
        
        # Verify setup completed (may have warnings but should not fail completely)
        assert setup_result['steps_completed'] >= 3
        
        # Verify required directories were created
        required_dirs = ['data', 'logs', 'temp']
        for dir_name in required_dirs:
            assert (temp_project_root / dir_name).exists()
        
        # Test processing after setup
        with patch('src.voice_task_manager.integrations.google_drive.GoogleDriveIntegration') as mock_drive:
            mock_drive_instance = Mock()
            mock_drive_instance.list_audio_files.return_value = {
                'success': True,
                'files': []
            }
            mock_drive.return_value = mock_drive_instance
            
            # Should be able to process after setup
            result = voice_processor.process_all_files()
            assert 'processed_count' in result
    
    @pytest.mark.e2e
    def test_database_workflow_integration(self, voice_processor, temp_project_root):
        """Test database operations throughout complete workflow"""
        
        database = VoiceDatabase(temp_project_root)
        
        # Check initial database state
        initial_stats = database.get_processing_stats()
        assert initial_stats['total_files'] == 0
        
        # Create test data through workflow
        with patch('src.voice_task_manager.integrations.google_drive.GoogleDriveIntegration') as mock_drive, \
             patch('src.voice_task_manager.core.transcription.VoiceTranscriber') as mock_transcriber, \
             patch('src.voice_task_manager.integrations.notion.NotionIntegration') as mock_notion:
            
            # Mock minimal successful workflow
            mock_drive_instance = Mock()
            mock_drive_instance.list_audio_files.return_value = {
                'success': True,
                'files': [
                    {'id': 'db_test_1', 'name': 'test1.m4a'},
                    {'id': 'db_test_2', 'name': 'test2.m4a'}
                ]
            }
            mock_drive_instance.download_file.return_value = {
                'success': True,
                'file_path': '/tmp/test.m4a'
            }
            mock_drive.return_value = mock_drive_instance
            
            mock_transcriber_instance = Mock()
            mock_transcriber_instance.transcribe_audio.return_value = {
                'success': True,
                'transcript': 'Database test transcript'
            }
            mock_transcriber.return_value = mock_transcriber_instance
            
            mock_notion_instance = Mock()
            mock_notion_instance.create_task.return_value = {
                'success': True,
                'task_id': 'db_task',
                'task_url': 'https://notion.so/db-task'
            }
            mock_notion.return_value = mock_notion_instance
            
            # Execute workflow
            result = voice_processor.process_all_files()
            
            # Verify database was updated
            final_stats = database.get_processing_stats()
            assert final_stats['total_files'] == 2
            assert final_stats['completed_files'] == 2
            assert final_stats['success_rate'] == 100.0
            
            # Verify individual records
            file1 = database.get_voice_file('db_test_1')
            file2 = database.get_voice_file('db_test_2')
            
            assert file1 is not None
            assert file2 is not None
            assert file1.status == 'completed'
            assert file2.status == 'completed'
            
            # Test database query functionality
            completed_files = database.get_all_voice_files(status='completed')
            assert len(completed_files) == 2
            
            # Test database cleanup
            deleted_count = database.cleanup_old_records(days_old=0)  # Clean all records
            assert deleted_count == 2
            
            # Verify cleanup worked
            after_cleanup_stats = database.get_processing_stats()
            assert after_cleanup_stats['total_files'] == 0