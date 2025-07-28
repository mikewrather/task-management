"""End-to-end system scenario tests for various real-world use cases"""

import pytest
import os
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.voice_task_manager.core.processor import VoiceProcessor
from src.voice_task_manager.utils.database import VoiceDatabase
from src.voice_task_manager.core.analyzer import VoiceAnalyzer
from src.voice_task_manager.utils.notifications import VoiceNotificationSystem


class TestSystemScenarios:
    """End-to-end tests for realistic system usage scenarios"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a complete project environment"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create project structure
            for dir_name in ['data', 'logs', 'temp', 'cache', 'archive']:
                (temp_path / dir_name).mkdir()
            
            yield temp_path
    
    @pytest.fixture
    def configured_processor(self, temp_project_root):
        """Create a processor with realistic configuration"""
        return VoiceProcessor(temp_project_root)
    
    @pytest.mark.e2e
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_key',
        'NOTION_TOKEN': 'test_token',
        'NOTION_TASKS_DB': 'test_db',
        'GOOGLE_DRIVE_FOLDER_ID': 'test_folder'
    })
    def test_daily_processing_scenario(self, configured_processor, temp_project_root):
        """Test typical daily processing scenario with multiple voice files"""
        
        with patch('src.voice_task_manager.integrations.google_drive.GoogleDriveIntegration') as mock_drive, \
             patch('src.voice_task_manager.core.transcription.VoiceTranscriber') as mock_transcriber, \
             patch('src.voice_task_manager.integrations.notion.NotionIntegration') as mock_notion:
            
            # Mock daily voice files (typical user might have 3-5 recordings)
            mock_drive_instance = Mock()
            daily_files = [
                {
                    'id': f'daily_voice_{i}',
                    'name': f'morning_notes_{i}.m4a',
                    'size': str(150000 + i * 50000),
                    'createdTime': f'2025-01-24T{8+i}:00:00Z'
                }
                for i in range(5)
            ]
            
            mock_drive_instance.list_audio_files.return_value = {
                'success': True,
                'files': daily_files
            }
            
            # Mock successful downloads
            mock_drive_instance.download_file.return_value = {
                'success': True,
                'file_path': '/tmp/voice_file.m4a',
                'file_size': 200000
            }
            mock_drive.return_value = mock_drive_instance
            
            # Mock transcriptions with realistic content
            mock_transcriber_instance = Mock()
            daily_transcripts = [
                "Schedule team meeting for Wednesday at 2 PM to discuss project timeline and resource allocation",
                "Review quarterly budget report and prepare summary for finance team by end of week",
                "Follow up with client regarding contract negotiations and pricing adjustments",
                "Create presentation slides for board meeting next Monday covering Q4 performance metrics",
                "Book travel arrangements for conference next month and submit expense pre-approval"
            ]
            
            def mock_transcribe(file_path):
                # Cycle through realistic transcripts
                transcript_index = mock_transcriber_instance.transcribe_audio.call_count % len(daily_transcripts)
                return {
                    'success': True,
                    'transcript': daily_transcripts[transcript_index],
                    'processing_time': 8.5 + transcript_index * 2,
                    'confidence': 0.88 + transcript_index * 0.02
                }
            
            mock_transcriber_instance.transcribe_audio.side_effect = mock_transcribe
            mock_transcriber.return_value = mock_transcriber_instance
            
            # Mock Notion task creation
            mock_notion_instance = Mock()
            def mock_create_task(task_data):
                return {
                    'success': True,
                    'task_id': f"daily_task_{hash(task_data['content']) % 10000}",
                    'task_url': f"https://notion.so/daily-task-{hash(task_data['content']) % 10000}"
                }
            mock_notion_instance.create_task.side_effect = mock_create_task
            mock_notion.return_value = mock_notion_instance
            
            # Execute daily processing
            start_time = time.time()
            result = configured_processor.process_all_files()
            processing_time = time.time() - start_time
            
            # Verify daily processing results
            assert result['success'] is True
            assert result['processed_count'] == 5
            assert result['success_count'] == 5
            assert result['error_count'] == 0
            
            # Verify performance is reasonable for daily use
            assert processing_time < 60  # Should complete within 1 minute
            
            # Verify database state after daily processing
            database = VoiceDatabase(temp_project_root)
            daily_stats = database.get_processing_stats()
            
            assert daily_stats['total_files'] == 5
            assert daily_stats['completed_files'] == 5
            assert daily_stats['success_rate'] == 100.0
            
            # Verify all transcripts were saved
            all_files = database.get_all_voice_files()
            transcripts = [f.transcript for f in all_files if f.transcript]
            assert len(transcripts) == 5
            
            # Verify typical content is present
            all_content = ' '.join(transcripts)
            assert 'meeting' in all_content.lower()
            assert 'schedule' in all_content.lower()
            assert 'review' in all_content.lower()
    
    @pytest.mark.e2e
    def test_weekend_batch_processing_scenario(self, configured_processor, temp_project_root):
        """Test weekend batch processing of accumulated voice files"""
        
        with patch('src.voice_task_manager.integrations.google_drive.GoogleDriveIntegration') as mock_drive, \
             patch('src.voice_task_manager.core.transcription.VoiceTranscriber') as mock_transcriber, \
             patch('src.voice_task_manager.integrations.notion.NotionIntegration') as mock_notion:
            
            # Mock large batch of accumulated files (15-20 files)
            mock_drive_instance = Mock()
            batch_files = []
            
            # Simulate files from different days
            for day in range(3):  # 3 days worth
                for hour in range(6):  # 6 files per day
                    batch_files.append({
                        'id': f'batch_{day}_{hour}',
                        'name': f'voice_batch_{day}_{hour}.m4a',
                        'size': str(100000 + day * 30000 + hour * 10000),
                        'createdTime': f'2025-01-{22+day}T{9+hour}:00:00Z'
                    })
            
            mock_drive_instance.list_audio_files.return_value = {
                'success': True,
                'files': batch_files
            }
            
            # Mock downloads with occasional failures
            def mock_download(file_id, local_path):
                # Simulate 5% failure rate
                if hash(file_id) % 20 == 0:  # ~5% failure
                    return {'success': False, 'error': 'Network timeout'}
                return {
                    'success': True,
                    'file_path': str(local_path),
                    'file_size': 150000
                }
            
            mock_drive_instance.download_file.side_effect = mock_download
            mock_drive.return_value = mock_drive_instance
            
            # Mock transcription with occasional API limits
            mock_transcriber_instance = Mock()
            transcription_call_count = 0
            
            def mock_transcribe(file_path):
                nonlocal transcription_call_count
                transcription_call_count += 1
                
                # Simulate rate limiting after many calls
                if transcription_call_count > 15 and transcription_call_count % 10 == 0:
                    return {
                        'success': False,
                        'error': 'OpenAI rate limit exceeded, please try again later'
                    }
                
                return {
                    'success': True,
                    'transcript': f'Batch processing transcript {transcription_call_count}',
                    'processing_time': 7.2,
                    'confidence': 0.91
                }
            
            mock_transcriber_instance.transcribe_audio.side_effect = mock_transcribe
            mock_transcriber.return_value = mock_transcriber_instance
            
            # Mock Notion with rate limiting
            mock_notion_instance = Mock()
            notion_call_count = 0
            
            def mock_create_task(task_data):
                nonlocal notion_call_count
                notion_call_count += 1
                
                # Simulate occasional Notion rate limits
                if notion_call_count > 12 and notion_call_count % 8 == 0:
                    return {
                        'success': False,
                        'error': 'Notion API rate limit exceeded',
                        'status_code': 429
                    }
                
                return {
                    'success': True,
                    'task_id': f'batch_task_{notion_call_count}',
                    'task_url': f'https://notion.so/batch-task-{notion_call_count}'
                }
            
            mock_notion_instance.create_task.side_effect = mock_create_task
            mock_notion.return_value = mock_notion_instance
            
            # Execute batch processing
            start_time = time.time()
            result = configured_processor.process_all_files()
            processing_time = time.time() - start_time
            
            # Verify batch processing handled errors gracefully
            assert result['processed_count'] == 18  # Total attempted
            assert result['success_count'] < result['processed_count']  # Some failures expected
            assert result['error_count'] > 0  # Expected some errors
            
            # Verify reasonable performance even with large batch
            assert processing_time < 300  # Should complete within 5 minutes
            
            # Verify database reflects mixed results
            database = VoiceDatabase(temp_project_root)
            batch_stats = database.get_processing_stats()
            
            assert batch_stats['total_files'] == 18
            assert batch_stats['completed_files'] > 0
            assert batch_stats['failed_files'] > 0
            
            # Verify success rate is reasonable despite errors
            assert batch_stats['success_rate'] > 50.0  # At least 50% success
    
    @pytest.mark.e2e
    def test_system_recovery_scenario(self, configured_processor, temp_project_root):
        """Test system recovery after interruption or failure"""
        
        # Simulate partial processing state (some files processed, others not)
        database = VoiceDatabase(temp_project_root)
        
        # Pre-populate with partially processed files from "previous session"
        from src.voice_task_manager.models.voice_file import VoiceFile
        
        # Completed file
        completed_file = VoiceFile(
            file_id='recovery_completed',
            transcript='Previously completed transcript',
            status='completed'
        )
        completed_file.mark_completed(
            'Previously completed transcript',
            'https://notion.so/previous-task'
        )
        database.save_voice_file(completed_file)
        
        # Failed file that should be retried
        failed_file = VoiceFile(
            file_id='recovery_failed',
            status='failed',
            error_message='Previous processing failed due to network error',
            retry_count=1
        )
        database.save_voice_file(failed_file)
        
        # Processing file that was interrupted
        interrupted_file = VoiceFile(
            file_id='recovery_interrupted',  
            status='processing'
        )
        database.save_voice_file(interrupted_file)
        
        with patch('src.voice_task_manager.integrations.google_drive.GoogleDriveIntegration') as mock_drive, \
             patch('src.voice_task_manager.core.transcription.VoiceTranscriber') as mock_transcriber, \
             patch('src.voice_task_manager.integrations.notion.NotionIntegration') as mock_notion:
            
            # Mock Drive returning all files (including previously processed)
            mock_drive_instance = Mock()
            mock_drive_instance.list_audio_files.return_value = {
                'success': True,
                'files': [
                    {'id': 'recovery_completed', 'name': 'completed.m4a'},
                    {'id': 'recovery_failed', 'name': 'failed.m4a'}, 
                    {'id': 'recovery_interrupted', 'name': 'interrupted.m4a'},
                    {'id': 'recovery_new', 'name': 'new.m4a'}
                ]
            }
            
            # Mock successful downloads for non-completed files
            def mock_download(file_id, local_path):
                if file_id == 'recovery_completed':
                    return {'success': False, 'error': 'Should not download completed file'}
                return {
                    'success': True,
                    'file_path': str(local_path),
                    'file_size': 100000
                }
            
            mock_drive_instance.download_file.side_effect = mock_download
            mock_drive.return_value = mock_drive_instance
            
            # Mock successful transcription for recovery
            mock_transcriber_instance = Mock()
            def mock_transcribe(file_path):
                if 'failed' in str(file_path):
                    return {
                        'success': True,
                        'transcript': 'Successfully recovered failed transcription'
                    }
                elif 'interrupted' in str(file_path):
                    return {
                        'success': True,
                        'transcript': 'Successfully completed interrupted transcription'
                    }
                else:
                    return {
                        'success': True,
                        'transcript': 'New file transcription'
                    }
            
            mock_transcriber_instance.transcribe_audio.side_effect = mock_transcribe
            mock_transcriber.return_value = mock_transcriber_instance
            
            # Mock Notion task creation
            mock_notion_instance = Mock()
            def mock_create_task(task_data):
                return {
                    'success': True,
                    'task_id': f"recovery_task_{hash(task_data['content']) % 1000}",
                    'task_url': 'https://notion.so/recovery-task'
                }
            mock_notion_instance.create_task.side_effect = mock_create_task
            mock_notion.return_value = mock_notion_instance
            
            # Execute recovery processing
            result = configured_processor.process_all_files()
            
            # Verify recovery behavior
            assert result['processed_count'] == 3  # failed, interrupted, new (not completed)
            assert result['skipped_count'] == 1   # completed file skipped
            assert result['success_count'] == 3   # All recovered successfully
            
            # Verify downloads only happened for non-completed files
            assert mock_drive_instance.download_file.call_count == 3
            
            # Verify database state after recovery
            recovery_stats = database.get_processing_stats()
            assert recovery_stats['total_files'] == 4
            assert recovery_stats['completed_files'] == 4  # All should be completed now
            assert recovery_stats['failed_files'] == 0     # No more failed files
            
            # Verify specific file states
            recovered_failed = database.get_voice_file('recovery_failed')
            recovered_interrupted = database.get_voice_file('recovery_interrupted')
            original_completed = database.get_voice_file('recovery_completed')
            new_file = database.get_voice_file('recovery_new')
            
            assert recovered_failed.status == 'completed'
            assert recovered_interrupted.status == 'completed'
            assert original_completed.status == 'completed'  # Unchanged
            assert new_file.status == 'completed'
    
    @pytest.mark.e2e
    def test_monitoring_and_analysis_scenario(self, configured_processor, temp_project_root):
        """Test system monitoring and analysis capabilities"""
        
        # Create historical data for analysis
        database = VoiceDatabase(temp_project_root)
        analyzer = VoiceAnalyzer(temp_project_root)
        
        # Simulate processing history over several days
        from src.voice_task_manager.models.voice_file import VoiceFile
        
        base_time = datetime.now() - timedelta(days=7)
        
        for day in range(7):
            for file_num in range(3):  # 3 files per day
                file_id = f'history_{day}_{file_num}'
                voice_file = VoiceFile(
                    file_id=file_id,
                    discovered_at=base_time + timedelta(days=day, hours=file_num),
                    file_size=100000 + day * 10000 + file_num * 5000
                )
                
                if day < 6:  # Most files successful
                    voice_file.mark_completed(
                        f'Historical transcript {day}_{file_num}',
                        f'https://notion.so/task-{file_id}'
                    )
                else:  # Some recent failures
                    if file_num == 2:
                        voice_file.mark_failed('Recent processing error')
                    else:
                        voice_file.mark_completed(
                            f'Recent transcript {day}_{file_num}',
                            f'https://notion.so/task-{file_id}'
                        )
                
                database.save_voice_file(voice_file)
        
        # Generate analysis report
        analysis_report = analyzer.generate_analysis(
            today_only=False,
            include_errors=True
        )
        
        # Verify analysis contains expected information
        assert 'VOICE PROCESSING STATISTICS' in analysis_report
        assert 'Total Files:' in analysis_report
        assert 'Success Rate:' in analysis_report
        assert 'ERROR SUMMARY' in analysis_report
        
        # Test JSON export for external monitoring
        json_analysis = analyzer.generate_analysis(export_format='json')
        analysis_data = json.loads(json_analysis)
        
        assert 'database_stats' in analysis_data
        assert 'run_history' in analysis_data
        assert 'summary' in analysis_data
        
        # Verify statistics are reasonable
        db_stats = analysis_data['database_stats']
        assert db_stats['total_files'] == 21  # 7 days * 3 files
        assert db_stats['completed_files'] == 20  # All but 1 failed
        assert db_stats['failed_files'] == 1
        
        # Test trend analysis
        trend_analysis = analyzer.get_trend_analysis(days_back=7)
        
        assert 'daily_breakdown' in trend_analysis
        assert 'summary' in trend_analysis
        assert trend_analysis['total_runs'] >= 0
        
        # Verify daily breakdown
        daily_breakdown = trend_analysis['daily_breakdown']
        assert len(daily_breakdown) <= 7  # Up to 7 days
    
    @pytest.mark.e2e
    def test_high_volume_scenario(self, configured_processor, temp_project_root):
        """Test system behavior under high volume processing"""
        
        with patch('src.voice_task_manager.integrations.google_drive.GoogleDriveIntegration') as mock_drive, \
             patch('src.voice_task_manager.core.transcription.VoiceTranscriber') as mock_transcriber, \
             patch('src.voice_task_manager.integrations.notion.NotionIntegration') as mock_notion:
            
            # Mock high volume of files (50 files)
            mock_drive_instance = Mock()
            high_volume_files = [
                {
                    'id': f'volume_test_{i:03d}',
                    'name': f'volume_file_{i:03d}.m4a',
                    'size': str(75000 + i * 1000),
                    'createdTime': f'2025-01-24T{10 + (i // 10)}:{(i % 10) * 6}:00Z'
                }
                for i in range(50)
            ]
            
            mock_drive_instance.list_audio_files.return_value = {
                'success': True,
                'files': high_volume_files
            }
            
            # Mock downloads with realistic timing
            def mock_download(file_id, local_path):
                # Simulate occasional network delays/failures
                file_num = int(file_id.split('_')[-1])
                if file_num % 23 == 0:  # ~4% failure rate
                    return {'success': False, 'error': 'Download timeout'}
                    
                return {
                    'success': True,
                    'file_path': str(local_path),
                    'file_size': 100000
                }
            
            mock_drive_instance.download_file.side_effect = mock_download
            mock_drive.return_value = mock_drive_instance
            
            # Mock transcription with rate limiting simulation
            mock_transcriber_instance = Mock()
            transcription_count = 0
            
            def mock_transcribe(file_path):
                nonlocal transcription_count
                transcription_count += 1
                
                # Simulate API rate limits periodically
                if transcription_count % 20 == 0:
                    return {
                        'success': False,
                        'error': 'Rate limit exceeded'
                    }
                
                return {
                    'success': True,
                    'transcript': f'High volume transcript {transcription_count}',
                    'processing_time': 5.0 + (transcription_count % 10) * 0.5
                }
            
            mock_transcriber_instance.transcribe_audio.side_effect = mock_transcribe
            mock_transcriber.return_value = mock_transcriber_instance
            
            # Mock Notion with bulk operation limits
            mock_notion_instance = Mock()
            notion_count = 0
            
            def mock_create_task(task_data):
                nonlocal notion_count
                notion_count += 1
                
                # Simulate occasional server errors under load
                if notion_count % 15 == 0:
                    return {
                        'success': False,
                        'error': 'Server temporarily unavailable',
                        'status_code': 503
                    }
                
                return {
                    'success': True,
                    'task_id': f'volume_task_{notion_count:03d}',
                    'task_url': f'https://notion.so/volume-task-{notion_count:03d}'
                }
            
            mock_notion_instance.create_task.side_effect = mock_create_task
            mock_notion.return_value = mock_notion_instance
            
            # Execute high volume processing with timing
            start_time = time.time()
            result = configured_processor.process_all_files()
            processing_time = time.time() - start_time
            
            # Verify high volume handling
            assert result['processed_count'] == 50
            assert result['success_count'] > 30  # Expect majority success despite errors
            assert result['error_count'] > 0     # Some errors expected at this volume
            
            # Verify reasonable performance scaling
            avg_time_per_file = processing_time / result['processed_count']
            assert avg_time_per_file < 10  # Average less than 10 seconds per file
            
            # Verify database can handle volume
            database = VoiceDatabase(temp_project_root)
            volume_stats = database.get_processing_stats()
            
            assert volume_stats['total_files'] == 50
            assert volume_stats['success_rate'] > 60  # At least 60% success rate
            
            # Verify system remains responsive after high volume
            post_volume_stats = database.get_processing_stats()
            assert post_volume_stats is not None  # Database still responsive
    
    @pytest.mark.e2e
    def test_notification_scenario(self, configured_processor, temp_project_root):
        """Test notification system in realistic usage scenario"""
        
        # Initialize notification system
        notification_system = VoiceNotificationSystem(temp_project_root)
        
        with patch('src.voice_task_manager.integrations.google_drive.GoogleDriveIntegration') as mock_drive, \
             patch('src.voice_task_manager.core.transcription.VoiceTranscriber') as mock_transcriber, \
             patch('src.voice_task_manager.integrations.notion.NotionIntegration') as mock_notion, \
             patch('subprocess.run') as mock_subprocess:
            
            # Mock processing workflow
            mock_drive_instance = Mock()
            mock_drive_instance.list_audio_files.return_value = {
                'success': True,
                'files': [
                    {'id': 'notify_success', 'name': 'success.m4a'},
                    {'id': 'notify_failure', 'name': 'failure.m4a'}
                ]
            }
            
            def mock_download(file_id, local_path):
                if file_id == 'notify_success':
                    return {'success': True, 'file_path': str(local_path)}
                else:
                    return {'success': False, 'error': 'Download failed for notification test'}
            
            mock_drive_instance.download_file.side_effect = mock_download
            mock_drive.return_value = mock_drive_instance
            
            # Mock transcription
            mock_transcriber_instance = Mock()
            mock_transcriber_instance.transcribe_audio.return_value = {
                'success': True,
                'transcript': 'Important meeting reminder: quarterly review scheduled for next week'
            }
            mock_transcriber.return_value = mock_transcriber_instance
            
            # Mock Notion
            mock_notion_instance = Mock()
            mock_notion_instance.create_task.return_value = {
                'success': True,
                'task_id': 'notification_task',
                'task_url': 'https://notion.so/notification-task'
            }
            mock_notion.return_value = mock_notion_instance
            
            # Mock desktop notifications
            mock_subprocess.return_value = Mock(returncode=0)
            
            # Execute processing
            result = configured_processor.process_all_files()
            
            # Verify notifications were triggered
            assert result['processed_count'] == 2
            assert result['success_count'] == 1  # Only success file completed
            assert result['error_count'] == 1    # Failure file had error
            
            # Test notification system directly
            test_results = notification_system.test_notifications()
            
            # Should have attempted desktop and console notifications
            assert 'desktop' in test_results or 'console' in test_results
            
            # Test daily summary notification
            summary_result = notification_system.notify_daily_summary()
            
            # Should generate summary based on today's activity
            assert summary_result is not None
    
    @pytest.mark.e2e
    def test_configuration_and_setup_scenario(self, temp_project_root):
        """Test complete system setup and configuration scenario"""
        
        from src.voice_task_manager.utils.config import SystemSetup, SystemStatus
        
        # Initialize setup system
        setup_system = SystemSetup(temp_project_root)
        
        # Test initial setup
        setup_result = setup_system.run_full_setup()
        
        # Verify setup process
        assert setup_result['steps_completed'] >= 3
        assert 'setup_summary' in setup_result
        
        # Verify directories were created
        required_dirs = ['data', 'logs', 'temp']
        for dir_name in required_dirs:
            assert (temp_project_root / dir_name).exists()
        
        # Test system status after setup
        status_checker = SystemStatus(temp_project_root)
        
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_key',
            'NOTION_TOKEN': 'test_token',
            'NOTION_TASKS_DB': 'test_db'
        }):
            status_result = status_checker.get_system_status(detailed=True)
            
            # Should show system is properly configured
            assert 'SYSTEM STATUS' in status_result
            assert 'Environment:' in status_result
            assert 'Database:' in status_result
            
            # Test JSON status format
            json_status = status_checker.get_system_status(json_format=True)
            status_data = json.loads(json_status)
            
            assert 'overall_status' in status_data
            assert 'components' in status_data
            assert status_data['overall_status'] in ['HEALTHY', 'WARNING', 'CRITICAL']
        
        # Test system status without proper environment
        with patch.dict(os.environ, {}, clear=True):
            status_result_no_env = status_checker.get_system_status()
            
            # Should show warnings about missing environment variables
            assert 'WARNING' in status_result_no_env or 'CRITICAL' in status_result_no_env