"""End-to-end tests for typical user workflows and interaction patterns"""

import pytest
import os
import tempfile
import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from src.voice_task_manager.cli import main
from src.voice_task_manager.core.processor import VoiceProcessor
from src.voice_task_manager.utils.database import VoiceDatabase


class TestUserWorkflows:
    """End-to-end tests simulating typical user interaction workflows"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a complete user environment"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create user project structure
            for dir_name in ['data', 'logs', 'temp', 'cache']:
                (temp_path / dir_name).mkdir()
            
            # Create user configuration
            user_config = {
                'user_preferences': {
                    'notification_enabled': True,
                    'auto_cleanup': True,
                    'detailed_logging': False
                },
                'processing_settings': {
                    'max_retries': 3,
                    'timeout_seconds': 30,
                    'batch_size': 10
                }
            }
            
            config_file = temp_path / 'data' / 'user_config.json'
            config_file.write_text(json.dumps(user_config, indent=2))
            
            yield temp_path
    
    @pytest.fixture
    def cli_runner(self):
        """Create a CLI test runner"""
        return CliRunner()
    
    @pytest.mark.e2e
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'user_openai_key',
        'NOTION_TOKEN': 'user_notion_token',
        'NOTION_TASKS_DB': 'user_db_123',
        'GOOGLE_DRIVE_FOLDER_ID': 'user_folder_123'
    })
    def test_new_user_onboarding_workflow(self, cli_runner, temp_project_root):
        """Test complete new user onboarding experience"""
        
        # Step 1: User runs setup command
        with patch('src.voice_task_manager.utils.config.SystemSetup') as mock_setup_class:
            mock_setup = Mock()
            mock_setup.run_full_setup.return_value = {
                'success': True,
                'steps_completed': 5,
                'setup_summary': {
                    'directories': {'success': True},
                    'database': {'success': True},
                    'environment': {'success': True},
                    'logging': {'success': True},
                    'api_connections': {'success': True}
                }
            }
            mock_setup.generate_setup_report.return_value = """
SYSTEM SETUP REPORT
==================

✅ Setup completed successfully!

Steps completed: 5/5

Directory Structure: ✅ Created
Database: ✅ Initialized  
Environment: ✅ Validated
Logging: ✅ Configured
API Connections: ✅ Tested

Your Voice Task Manager is ready to use!

Next steps:
1. Run 'voice-task-manager status' to verify system health
2. Run 'voice-task-manager process' to start processing voice files
3. Run 'voice-task-manager analyze' to view processing statistics
"""
            mock_setup_class.return_value = mock_setup
            
            setup_result = cli_runner.invoke(main, ['setup'])
            
            assert setup_result.exit_code == 0
            assert "Setup completed successfully!" in setup_result.output
            assert "Next steps:" in setup_result.output
        
        # Step 2: User checks system status
        with patch('src.voice_task_manager.utils.config.SystemStatus') as mock_status_class:
            mock_status = Mock()
            mock_status.get_system_status.return_value = """
VOICE TASK MANAGER - SYSTEM STATUS
==================================

Overall System Health: ✅ HEALTHY

Environment: ✅ HEALTHY
- OpenAI API Key: ✅ Found
- Notion Token: ✅ Found  
- Notion Database ID: ✅ Found
- Google Drive Folder ID: ✅ Found

Database: ✅ HEALTHY
- Connection: ✅ Active
- Total files: 0
- Processed today: 0

Directories: ✅ HEALTHY
- Data directory: ✅ Writable
- Logs directory: ✅ Writable
- Temp directory: ✅ Writable

System is ready for voice processing!
"""
            mock_status_class.return_value = mock_status
            
            status_result = cli_runner.invoke(main, ['status'])
            
            assert status_result.exit_code == 0
            assert "HEALTHY" in status_result.output
            assert "ready for voice processing" in status_result.output
        
        # Step 3: User runs first processing session
        with patch('src.voice_task_manager.core.processor.VoiceProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process_all_files.return_value = {
                'success': True,
                'processed_count': 0,
                'success_count': 0,
                'error_count': 0,
                'skipped_count': 0,
                'message': 'No new voice files found. Upload some voice recordings to your Google Drive folder to get started!'
            }
            mock_processor_class.return_value = mock_processor
            
            process_result = cli_runner.invoke(main, ['process'])
            
            assert process_result.exit_code == 0
            assert "No new voice files found" in process_result.output
            assert "Upload some voice recordings" in process_result.output
    
    @pytest.mark.e2e
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'user_key',
        'NOTION_TOKEN': 'user_token',
        'NOTION_TASKS_DB': 'user_db',
        'GOOGLE_DRIVE_FOLDER_ID': 'user_folder'
    })
    def test_daily_user_workflow(self, cli_runner, temp_project_root):
        """Test typical daily user workflow"""
        
        # Step 1: User checks status in the morning
        with patch('src.voice_task_manager.utils.config.SystemStatus') as mock_status_class:
            mock_status = Mock()
            mock_status.get_system_status.return_value = """
VOICE TASK MANAGER - SYSTEM STATUS
Overall System Health: ✅ HEALTHY
Recent activity: 3 files processed yesterday
"""
            mock_status_class.return_value = mock_status
            
            morning_status = cli_runner.invoke(main, ['status'])
            assert morning_status.exit_code == 0
            assert "HEALTHY" in morning_status.output
        
        # Step 2: User processes new voice files
        with patch('src.voice_task_manager.core.processor.VoiceProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process_all_files.return_value = {
                'success': True,
                'processed_count': 4,
                'success_count': 4,
                'error_count': 0,
                'skipped_count': 1,
                'processing_summary': {
                    'new_tasks_created': 4,
                    'total_processing_time': 45.2,
                    'avg_confidence': 0.91
                }
            }
            mock_processor_class.return_value = mock_processor
            
            process_result = cli_runner.invoke(main, ['process'])
            
            assert process_result.exit_code == 0
            assert "Processing completed" in process_result.output
            assert "4 files processed" in process_result.output or "processed: 4" in process_result.output
        
        # Step 3: User reviews daily analysis
        with patch('src.voice_task_manager.core.analyzer.VoiceAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.generate_analysis.return_value = """
VOICE PROCESSING ANALYSIS - Today's Activity
============================================

Files processed today: 4
Success rate: 100%
Average processing time: 11.3 seconds

Recent Tasks Created:
• Review quarterly budget and prepare finance summary
• Schedule team meeting for project status update  
• Follow up with client regarding contract renewal
• Create presentation for board meeting next week

System Performance:
Processing efficiency: Excellent
API response times: Normal
Error rate: 0%

All systems operating normally!
"""
            mock_analyzer_class.return_value = mock_analyzer
            
            analysis_result = cli_runner.invoke(main, ['analyze', '--today'])
            
            assert analysis_result.exit_code == 0
            assert "Today's Activity" in analysis_result.output
            assert "4" in analysis_result.output
            assert "100%" in analysis_result.output
    
    @pytest.mark.e2e
    def test_troubleshooting_workflow(self, cli_runner, temp_project_root):
        """Test user troubleshooting workflow when things go wrong"""
        
        # Step 1: User notices processing failed
        with patch('src.voice_task_manager.core.processor.VoiceProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process_all_files.return_value = {
                'success': False,
                'processed_count': 5,
                'success_count': 2,
                'error_count': 3,
                'errors': [
                    'OpenAI API rate limit exceeded',
                    'Notion API authentication failed',
                    'Google Drive file not accessible'
                ]
            }
            mock_processor_class.return_value = mock_processor
            
            failed_process = cli_runner.invoke(main, ['process'])
            
            assert failed_process.exit_code == 1
            assert "Error" in failed_process.output or "Failed" in failed_process.output
        
        # Step 2: User checks detailed system status
        with patch('src.voice_task_manager.utils.config.SystemStatus') as mock_status_class:
            mock_status = Mock()
            mock_status.get_system_status.return_value = """
VOICE TASK MANAGER - SYSTEM STATUS (DETAILED)
============================================

Overall System Health: ⚠️ WARNING

Environment: ⚠️ WARNING
- OpenAI API Key: ✅ Found
- Notion Token: ❌ Invalid or expired
- API Connectivity: ⚠️ Rate limits detected

Database: ✅ HEALTHY
- Recent errors: 3 in last hour

Recommendations:
1. Check Notion token validity
2. Verify API rate limit status
3. Review recent error logs in logs/
"""
            mock_status_class.return_value = mock_status
            
            detailed_status = cli_runner.invoke(main, ['status', '--detailed'])
            
            assert detailed_status.exit_code == 0
            assert "WARNING" in detailed_status.output
            assert "Recommendations:" in detailed_status.output
        
        # Step 3: User tests individual components
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.models.list.return_value = Mock(data=[{'id': 'whisper-1'}])
            mock_openai.return_value = mock_client
            
            openai_test = cli_runner.invoke(main, ['test', 'openai'])
            
            assert openai_test.exit_code == 0
            assert "OpenAI API connection" in openai_test.output
        
        # Step 4: User runs cleanup to resolve issues
        with patch('src.voice_task_manager.core.cleanup.VoiceCleanup') as mock_cleanup_class:
            mock_cleanup = Mock()
            mock_cleanup.run_all_cleanup.return_value = {
                'success': True,
                'total_deleted': 15,
                'temp_files_cleaned': 12,
                'old_logs_removed': 3,
                'disk_space_freed': '2.3 MB'
            }
            mock_cleanup.generate_cleanup_report.return_value = """
CLEANUP REPORT
=============

✅ Cleanup completed successfully!

Files removed: 15
- Temporary files: 12
- Old log files: 3

Disk space freed: 2.3 MB

System performance should be improved.
"""
            mock_cleanup_class.return_value = mock_cleanup
            
            cleanup_result = cli_runner.invoke(main, ['cleanup'])
            
            assert cleanup_result.exit_code == 0
            assert "Cleanup completed successfully" in cleanup_result.output
            assert "15" in cleanup_result.output
    
    @pytest.mark.e2e
    def test_power_user_workflow(self, cli_runner, temp_project_root):
        """Test advanced power user workflow with detailed analysis"""
        
        # Step 1: Power user gets comprehensive analysis
        with patch('src.voice_task_manager.core.analyzer.VoiceAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.generate_analysis.return_value = """
VOICE PROCESSING STATISTICS - COMPREHENSIVE REPORT
================================================

OVERVIEW:
Total Files: 127
Success Rate: 94.5% (120 successful, 7 failed)
Avg Processing Time: 8.7 seconds
Total Processing Time: 18.2 minutes

PERFORMANCE TRENDS:
Last 7 days: ↗️ Processing volume up 23%
Error rate: ↘️ Down from 8.1% to 5.5%
Efficiency: ✅ Stable (8.2-9.4s per file)

TOP ERROR CATEGORIES:
1. API Rate Limits: 4 occurrences
2. Audio Quality Issues: 2 occurrences  
3. Network Timeouts: 1 occurrence

RECOMMENDATIONS:
• Consider upgrading OpenAI API tier for higher limits
• Review audio recording quality settings
• Monitor network connectivity during peak hours
"""
            mock_analyzer_class.return_value = mock_analyzer
            
            comprehensive_analysis = cli_runner.invoke(main, ['analyze', '--errors'])
            
            assert comprehensive_analysis.exit_code == 0
            assert "COMPREHENSIVE REPORT" in comprehensive_analysis.output
            assert "94.5%" in comprehensive_analysis.output
            assert "RECOMMENDATIONS:" in comprehensive_analysis.output
        
        # Step 2: Power user exports data for external analysis
        with patch('src.voice_task_manager.core.analyzer.VoiceAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            analysis_data = {
                'export_timestamp': '2025-01-24T15:30:00Z',
                'database_stats': {
                    'total_files': 127,
                    'completed_files': 120,
                    'failed_files': 7,
                    'success_rate': 94.5
                },
                'performance_metrics': {
                    'avg_processing_time': 8.7,
                    'total_processing_time': 1092,
                    'files_per_day_avg': 18.1
                },
                'error_analysis': {
                    'rate_limits': 4,
                    'audio_quality': 2,
                    'network_issues': 1
                }
            }
            mock_analyzer.generate_analysis.return_value = json.dumps(analysis_data, indent=2)
            mock_analyzer_class.return_value = mock_analyzer
            
            json_export = cli_runner.invoke(main, ['analyze', '--export', 'json'])
            
            assert json_export.exit_code == 0
            
            # Verify valid JSON output
            exported_data = json.loads(json_export.output)
            assert 'database_stats' in exported_data
            assert 'performance_metrics' in exported_data
            assert exported_data['database_stats']['total_files'] == 127
        
        # Step 3: Power user checks system performance
        with patch('src.voice_task_manager.utils.config.SystemStatus') as mock_status_class:
            mock_status = Mock()
            status_data = {
                'timestamp': '2025-01-24T15:30:00Z',
                'overall_status': 'HEALTHY',
                'components': {
                    'environment': {'status': 'HEALTHY', 'details': 'All APIs accessible'},
                    'database': {'status': 'HEALTHY', 'total_files': 127, 'success_rate': 94.5},
                    'disk_space': {'status': 'HEALTHY', 'usage_percent': 23.4},
                    'api_performance': {
                        'openai_avg_response': 2.3,
                        'notion_avg_response': 1.8,
                        'drive_avg_response': 3.1
                    }
                }
            }
            mock_status.get_system_status.return_value = json.dumps(status_data, indent=2)
            mock_status_class.return_value = mock_status
            
            json_status = cli_runner.invoke(main, ['status', '--json'])
            
            assert json_status.exit_code == 0
            
            # Verify structured status data
            status_result = json.loads(json_status.output)
            assert status_result['overall_status'] == 'HEALTHY'
            assert 'api_performance' in status_result['components']
    
    @pytest.mark.e2e
    def test_automation_integration_workflow(self, cli_runner, temp_project_root):
        """Test workflow for users integrating with automation systems"""
        
        # Step 1: Automated system checks if processing is needed
        with patch('src.voice_task_manager.core.processor.VoiceProcessor') as mock_processor_class:
            mock_processor = Mock()
            
            # Mock check for new files
            mock_processor.check_for_new_files.return_value = {
                'new_files_count': 3,
                'new_files': [
                    {'id': 'auto_1', 'name': 'meeting_notes.m4a'},
                    {'id': 'auto_2', 'name': 'voice_memo.m4a'},
                    {'id': 'auto_3', 'name': 'task_reminder.m4a'}
                ]
            }
            mock_processor_class.return_value = mock_processor
            
            # Simulate automated check (would be done via script/cron)
            processor = VoiceProcessor(temp_project_root)
            new_files_check = processor.check_for_new_files()
            
            assert new_files_check['new_files_count'] == 3
            assert len(new_files_check['new_files']) == 3
        
        # Step 2: Automated processing with JSON output for parsing
        with patch('src.voice_task_manager.core.processor.VoiceProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process_all_files.return_value = {
                'success': True,
                'processed_count': 3,
                'success_count': 3,
                'error_count': 0,
                'processing_time': 26.7,
                'created_tasks': [
                    {'task_id': 'auto_task_1', 'url': 'https://notion.so/auto-task-1'},
                    {'task_id': 'auto_task_2', 'url': 'https://notion.so/auto-task-2'},
                    {'task_id': 'auto_task_3', 'url': 'https://notion.so/auto-task-3'}
                ]
            }
            mock_processor_class.return_value = mock_processor
            
            # Simulate automated processing call
            automated_process = cli_runner.invoke(main, ['process', '--quiet'])
            
            # Should complete successfully for automation
            assert automated_process.exit_code == 0
        
        # Step 3: Automated system retrieves processing status
        with patch('src.voice_task_manager.utils.config.SystemStatus') as mock_status_class:
            mock_status = Mock()
            automation_status = {
                'timestamp': '2025-01-24T16:00:00Z',
                'overall_status': 'HEALTHY',
                'last_processing': {
                    'timestamp': '2025-01-24T15:55:00Z',
                    'files_processed': 3,
                    'success': True,
                    'duration_seconds': 26.7
                },
                'system_metrics': {
                    'uptime_hours': 168,
                    'total_files_processed': 130,
                    'success_rate_7_days': 94.5,
                    'avg_processing_time': 8.9
                }
            }
            mock_status.get_system_status.return_value = json.dumps(automation_status, indent=2)
            mock_status_class.return_value = mock_status
            
            status_for_automation = cli_runner.invoke(main, ['status', '--json'])
            
            assert status_for_automation.exit_code == 0
            
            # Parse for automation system
            status_data = json.loads(status_for_automation.output)
            assert status_data['overall_status'] == 'HEALTHY'
            assert status_data['last_processing']['success'] is True
    
    @pytest.mark.e2e
    def test_maintenance_workflow(self, cli_runner, temp_project_root):
        """Test user maintenance and cleanup workflow"""
        
        # Step 1: User checks what needs cleanup
        with patch('src.voice_task_manager.core.cleanup.VoiceCleanup') as mock_cleanup_class:
            mock_cleanup = Mock()
            mock_cleanup.get_cleanup_stats.return_value = {
                'temp_files_count': 23,
                'temp_files_size': 5242880,  # ~5MB
                'log_files_count': 12,
                'log_files_size': 2097152,   # ~2MB
                'total_cleanable_size': 7340032,  # ~7MB
                'oldest_temp_file_age_days': 15,
                'oldest_log_file_age_days': 30
            }
            mock_cleanup_class.return_value = mock_cleanup
            
            cleanup_preview = cli_runner.invoke(main, ['cleanup', '--dry-run'])
            
            assert cleanup_preview.exit_code == 0
            assert "DRY RUN" in cleanup_preview.output
            assert "23" in cleanup_preview.output  # temp files
            assert "7" in cleanup_preview.output   # total MB (approximately)
        
        # Step 2: User performs actual cleanup
        with patch('src.voice_task_manager.core.cleanup.VoiceCleanup') as mock_cleanup_class:
            mock_cleanup = Mock()
            mock_cleanup.run_all_cleanup.return_value = {
                'success': True,
                'total_deleted': 35,
                'database_cleanup': {'deleted_count': 0},
                'temp_cleanup': {'deleted_count': 23},
                'log_cleanup': {'deleted_count': 12},
                'cache_cleanup': {'deleted_count': 0},
                'disk_space_freed': 7340032
            }
            mock_cleanup.generate_cleanup_report.return_value = """
CLEANUP REPORT
=============

✅ Cleanup completed successfully!

Summary:
- Total files removed: 35
- Temporary files: 23
- Old log files: 12
- Disk space freed: 7.0 MB

Database maintenance:
- Old records cleaned: 0
- Database optimized: ✅

System performance should be improved.
Your voice processing system is now optimized!
"""
            mock_cleanup_class.return_value = mock_cleanup
            
            actual_cleanup = cli_runner.invoke(main, ['cleanup'])
            
            assert actual_cleanup.exit_code == 0
            assert "✅ Cleanup completed successfully!" in actual_cleanup.output
            assert "35" in actual_cleanup.output
            assert "7.0 MB" in actual_cleanup.output
        
        # Step 3: User verifies system health after maintenance
        with patch('src.voice_task_manager.utils.config.SystemStatus') as mock_status_class:
            mock_status = Mock()
            mock_status.get_system_status.return_value = """
VOICE TASK MANAGER - SYSTEM STATUS
==================================

Overall System Health: ✅ HEALTHY

Recent Maintenance:
- Last cleanup: Just completed
- Files removed: 35
- Disk space freed: 7.0 MB

System Performance:
- Disk usage: 45% (↓ from 52%)
- Database size: Optimized
- Response times: Excellent

Environment: ✅ HEALTHY
Database: ✅ HEALTHY  
Directories: ✅ HEALTHY

System is running optimally!
"""
            mock_status_class.return_value = mock_status
            
            post_maintenance_status = cli_runner.invoke(main, ['status'])
            
            assert post_maintenance_status.exit_code == 0
            assert "HEALTHY" in post_maintenance_status.output
            assert "Recent Maintenance:" in post_maintenance_status.output
            assert "running optimally" in post_maintenance_status.output