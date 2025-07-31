"""Tests for voice task manager CLI commands"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
import json

from voice_task_manager.cli import main, status, analyze, setup, cleanup, process


class TestCLICommands:
    """Test cases for CLI command functionality"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Create required subdirectories
            (temp_path / 'data').mkdir()
            (temp_path / 'logs').mkdir()
            yield temp_path
    
    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()
    
    def test_main_command_help(self, runner):
        """Test main command help output"""
        result = runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert 'Voice Task Manager' in result.output
        assert 'Commands:' in result.output
    
    @patch('src.voice_task_manager.cli.SystemStatus')
    def test_status_command_basic(self, mock_status_class, runner):
        """Test basic status command"""
        # Mock SystemStatus
        mock_status = Mock()
        mock_status.get_system_status.return_value = "System Status: HEALTHY"
        mock_status_class.return_value = mock_status
        
        result = runner.invoke(status)
        
        assert result.exit_code == 0
        assert "System Status: HEALTHY" in result.output
        mock_status.get_system_status.assert_called_once_with(detailed=False, json_format=False)
    
    @patch('src.voice_task_manager.cli.SystemStatus')
    def test_status_command_detailed(self, mock_status_class, runner):
        """Test detailed status command"""
        # Mock SystemStatus
        mock_status = Mock()
        mock_status.get_system_status.return_value = "Detailed System Status"
        mock_status_class.return_value = mock_status
        
        result = runner.invoke(status, ['--detailed'])
        
        assert result.exit_code == 0
        mock_status.get_system_status.assert_called_once_with(detailed=True, json_format=False)
    
    @patch('src.voice_task_manager.cli.SystemStatus')
    def test_status_command_json(self, mock_status_class, runner):
        """Test status command with JSON output"""
        # Mock SystemStatus
        mock_status = Mock()
        mock_status.get_system_status.return_value = '{"status": "HEALTHY"}'
        mock_status_class.return_value = mock_status
        
        result = runner.invoke(status, ['--json'])
        
        assert result.exit_code == 0
        # Should be valid JSON
        json.loads(result.output.strip())
        mock_status.get_system_status.assert_called_once_with(detailed=False, json_format=True)
    
    @patch('src.voice_task_manager.cli.SystemStatus')
    def test_status_command_error_handling(self, mock_status_class, runner):
        """Test status command error handling"""
        # Mock SystemStatus to raise exception
        mock_status_class.side_effect = Exception("Status check failed")
        
        result = runner.invoke(status)
        
        assert result.exit_code == 1
        assert "Error checking system status" in result.output
    
    @patch('src.voice_task_manager.cli.VoiceAnalyzer')
    def test_analyze_command_basic(self, mock_analyzer_class, runner):
        """Test basic analyze command"""
        # Mock VoiceAnalyzer
        mock_analyzer = Mock()
        mock_analyzer.generate_analysis.return_value = "Analysis Report"
        mock_analyzer_class.return_value = mock_analyzer
        
        result = runner.invoke(analyze)
        
        assert result.exit_code == 0
        assert "Analysis Report" in result.output
        mock_analyzer.generate_analysis.assert_called_once_with(
            today_only=False, include_errors=False, export_format=None
        )
    
    @patch('src.voice_task_manager.cli.VoiceAnalyzer')
    def test_analyze_command_today_only(self, mock_analyzer_class, runner):
        """Test analyze command with today-only flag"""
        # Mock VoiceAnalyzer
        mock_analyzer = Mock()
        mock_analyzer.generate_analysis.return_value = "Today's Analysis"
        mock_analyzer_class.return_value = mock_analyzer
        
        result = runner.invoke(analyze, ['--today'])
        
        assert result.exit_code == 0
        mock_analyzer.generate_analysis.assert_called_once_with(
            today_only=True, include_errors=False, export_format=None
        )
    
    @patch('src.voice_task_manager.cli.VoiceAnalyzer')
    def test_analyze_command_with_errors(self, mock_analyzer_class, runner):
        """Test analyze command with error details"""
        # Mock VoiceAnalyzer
        mock_analyzer = Mock()
        mock_analyzer.generate_analysis.return_value = "Analysis with Errors"
        mock_analyzer_class.return_value = mock_analyzer
        
        result = runner.invoke(analyze, ['--errors'])
        
        assert result.exit_code == 0
        mock_analyzer.generate_analysis.assert_called_once_with(
            today_only=False, include_errors=True, export_format=None
        )
    
    @patch('src.voice_task_manager.cli.VoiceAnalyzer')
    def test_analyze_command_export_json(self, mock_analyzer_class, runner):
        """Test analyze command with JSON export"""
        # Mock VoiceAnalyzer
        mock_analyzer = Mock()
        mock_analyzer.generate_analysis.return_value = '{"analysis": "data"}'
        mock_analyzer_class.return_value = mock_analyzer
        
        result = runner.invoke(analyze, ['--export', 'json'])
        
        assert result.exit_code == 0
        mock_analyzer.generate_analysis.assert_called_once_with(
            today_only=False, include_errors=False, export_format='json'
        )
    
    @patch('src.voice_task_manager.cli.VoiceAnalyzer')
    def test_analyze_command_error_handling(self, mock_analyzer_class, runner):
        """Test analyze command error handling"""
        # Mock VoiceAnalyzer to raise exception
        mock_analyzer_class.side_effect = Exception("Analysis failed")
        
        result = runner.invoke(analyze)
        
        assert result.exit_code == 1
        assert "Error generating analysis" in result.output
    
    @patch('src.voice_task_manager.cli.SystemSetup')
    def test_setup_command_basic(self, mock_setup_class, runner):
        """Test basic setup command"""
        # Mock SystemSetup
        mock_setup = Mock()
        mock_setup.run_full_setup.return_value = {
            'success': True,
            'steps_completed': 5,
            'setup_summary': {}
        }
        mock_setup.generate_setup_report.return_value = "Setup completed successfully"
        mock_setup_class.return_value = mock_setup
        
        result = runner.invoke(setup)
        
        assert result.exit_code == 0
        assert "Setup completed successfully" in result.output
    
    @patch('src.voice_task_manager.cli.SystemSetup')
    def test_setup_command_force(self, mock_setup_class, runner):
        """Test setup command with force flag"""
        # Mock SystemSetup
        mock_setup = Mock()
        mock_setup.cleanup_failed_setup.return_value = {'success': True}
        mock_setup.run_full_setup.return_value = {
            'success': True,
            'steps_completed': 5,
            'setup_summary': {}
        }
        mock_setup.generate_setup_report.return_value = "Forced setup completed"
        mock_setup_class.return_value = mock_setup
        
        result = runner.invoke(setup, ['--force'])
        
        assert result.exit_code == 0
        mock_setup.cleanup_failed_setup.assert_called_once()
    
    @patch('src.voice_task_manager.cli.SystemSetup')
    def test_setup_command_error_handling(self, mock_setup_class, runner):
        """Test setup command error handling"""
        # Mock SystemSetup to raise exception
        mock_setup_class.side_effect = Exception("Setup failed")
        
        result = runner.invoke(setup)
        
        assert result.exit_code == 1
        assert "Error during setup" in result.output
    
    @patch('src.voice_task_manager.cli.VoiceCleanup')
    def test_cleanup_command_basic(self, mock_cleanup_class, runner):
        """Test basic cleanup command"""
        # Mock VoiceCleanup
        mock_cleanup = Mock()
        mock_cleanup.run_all_cleanup.return_value = {
            'success': True,
            'total_deleted': 10
        }
        mock_cleanup.generate_cleanup_report.return_value = "Cleanup completed: 10 files removed"
        mock_cleanup_class.return_value = mock_cleanup
        
        result = runner.invoke(cleanup)
        
        assert result.exit_code == 0
        assert "Cleanup completed: 10 files removed" in result.output
    
    @patch('src.voice_task_manager.cli.VoiceCleanup')
    def test_cleanup_command_dry_run(self, mock_cleanup_class, runner):
        """Test cleanup command with dry run"""
        # Mock VoiceCleanup
        mock_cleanup = Mock()
        mock_cleanup.get_cleanup_stats.return_value = {
            'temp_files_count': 5,
            'log_files_count': 3,
            'total_cleanable_size': 1024000
        }
        mock_cleanup_class.return_value = mock_cleanup
        
        result = runner.invoke(cleanup, ['--dry-run'])
        
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        mock_cleanup.get_cleanup_stats.assert_called_once()
        # Should not call actual cleanup
        mock_cleanup.run_all_cleanup.assert_not_called()
    
    @patch('src.voice_task_manager.cli.VoiceCleanup')
    def test_cleanup_command_error_handling(self, mock_cleanup_class, runner):
        """Test cleanup command error handling"""
        # Mock VoiceCleanup to raise exception
        mock_cleanup_class.side_effect = Exception("Cleanup failed")
        
        result = runner.invoke(cleanup)
        
        assert result.exit_code == 1
        assert "Error during cleanup" in result.output
    
    @patch('src.voice_task_manager.cli.VoiceNotificationSystem')
    def test_test_command_notifications(self, mock_notification_class, runner):
        """Test test command for notifications"""
        # Mock VoiceNotificationSystem
        mock_notifications = Mock()
        mock_notifications.test_notifications.return_value = {
            'desktop': True,
            'console': True,
            'log': True
        }
        mock_notification_class.return_value = mock_notifications
        
        result = runner.invoke(test, ['notifications'])
        
        assert result.exit_code == 0
        assert "Testing notifications" in result.output
        mock_notifications.test_notifications.assert_called_once()
    
    @patch('src.voice_task_manager.cli.VoiceDatabase')
    def test_test_command_database(self, mock_db_class, runner):
        """Test test command for database"""
        # Mock VoiceDatabase
        mock_db = Mock()
        mock_db.get_processing_stats.return_value = {'total_files': 5}
        mock_db_class.return_value = mock_db
        
        result = runner.invoke(test, ['database'])
        
        assert result.exit_code == 0
        assert "Testing database connection" in result.output
        mock_db.get_processing_stats.assert_called_once()
    
    @patch('openai.OpenAI')
    def test_test_command_openai(self, mock_openai_class, runner):
        """Test test command for OpenAI API"""
        # Mock OpenAI
        mock_client = Mock()
        mock_client.models.list.return_value = Mock(data=[{'id': 'gpt-3.5-turbo'}])
        mock_openai_class.return_value = mock_client
        
        result = runner.invoke(test, ['openai'])
        
        assert result.exit_code == 0
        assert "Testing OpenAI API connection" in result.output
    
    def test_test_command_invalid_component(self, runner):
        """Test test command with invalid component"""
        result = runner.invoke(test, ['invalid_component'])
        
        assert result.exit_code == 1
        assert "Unknown test component" in result.output
    
    @patch('src.voice_task_manager.cli.VoiceProcessor')
    def test_process_command_basic(self, mock_processor_class, runner):
        """Test basic process command"""
        # Mock VoiceProcessor
        mock_processor = Mock()
        mock_processor.process_all_files.return_value = {
            'processed_count': 3,
            'success_count': 2,
            'error_count': 1
        }
        mock_processor_class.return_value = mock_processor
        
        result = runner.invoke(process)
        
        assert result.exit_code == 0
        assert "Processing completed" in result.output
    
    @patch('src.voice_task_manager.cli.VoiceProcessor')
    def test_process_command_specific_file(self, mock_processor_class, runner):
        """Test process command with specific file"""
        # Mock VoiceProcessor
        mock_processor = Mock()
        mock_processor.process_file.return_value = {'success': True}
        mock_processor_class.return_value = mock_processor
        
        result = runner.invoke(process, ['--file-id', 'test_file_123'])
        
        assert result.exit_code == 0
        mock_processor.process_file.assert_called_once_with('test_file_123')
    
    @patch('src.voice_task_manager.cli.VoiceProcessor')
    def test_process_command_force_reprocess(self, mock_processor_class, runner):
        """Test process command with force reprocess"""
        # Mock VoiceProcessor
        mock_processor = Mock()
        mock_processor.process_all_files.return_value = {
            'processed_count': 5,
            'success_count': 5,
            'error_count': 0
        }
        mock_processor_class.return_value = mock_processor
        
        result = runner.invoke(process, ['--force'])
        
        assert result.exit_code == 0
        mock_processor.process_all_files.assert_called_once_with(force_reprocess=True)
    
    @patch('src.voice_task_manager.cli.VoiceProcessor')
    def test_process_command_error_handling(self, mock_processor_class, runner):
        """Test process command error handling"""
        # Mock VoiceProcessor to raise exception
        mock_processor_class.side_effect = Exception("Processing failed")
        
        result = runner.invoke(process)
        
        assert result.exit_code == 1
        assert "Error during processing" in result.output
    
    def test_click_context_passing(self, runner):
        """Test Click context passing between commands"""
        with patch('src.voice_task_manager.cli.SystemStatus') as mock_status:
            mock_status_instance = Mock()
            mock_status_instance.get_system_status.return_value = "Status OK"
            mock_status.return_value = mock_status_instance
            
            result = runner.invoke(main, ['status'])
            
            assert result.exit_code == 0
            # Verify context was passed correctly
            mock_status.assert_called_once()
    
    def test_verbose_flag_propagation(self, runner):
        """Test verbose flag propagation to subcommands"""
        with patch('src.voice_task_manager.cli.SystemStatus') as mock_status:
            mock_status_instance = Mock()
            mock_status_instance.get_system_status.return_value = "Verbose Status"
            mock_status.return_value = mock_status_instance
            
            result = runner.invoke(main, ['--verbose', 'status'])
            
            assert result.exit_code == 0
    
    def test_command_aliases(self, runner):
        """Test command aliases work correctly"""
        # These would be defined in the CLI module if aliases exist
        with patch('src.voice_task_manager.cli.SystemStatus') as mock_status:
            mock_status_instance = Mock()
            mock_status_instance.get_system_status.return_value = "Status"
            mock_status.return_value = mock_status_instance
            
            # Test full command name
            result = runner.invoke(main, ['status'])
            assert result.exit_code == 0
    
    def test_environment_variable_override(self, runner):
        """Test environment variable handling in CLI"""
        with patch.dict('os.environ', {'VOICE_TASK_PROJECT_ROOT': '/custom/path'}):
            with patch('src.voice_task_manager.cli.SystemStatus') as mock_status:
                mock_status_instance = Mock()
                mock_status_instance.get_system_status.return_value = "Custom Path Status"
                mock_status.return_value = mock_status_instance
                
                result = runner.invoke(status)
                
                assert result.exit_code == 0
    
    def test_cli_integration_workflow(self, runner):
        """Test complete CLI workflow integration"""
        with patch('src.voice_task_manager.cli.SystemSetup') as mock_setup, \
             patch('src.voice_task_manager.cli.SystemStatus') as mock_status, \
             patch('src.voice_task_manager.cli.VoiceProcessor') as mock_processor:
            
            # Mock setup
            mock_setup_instance = Mock()
            mock_setup_instance.run_full_setup.return_value = {'success': True, 'steps_completed': 5, 'setup_summary': {}}
            mock_setup_instance.generate_setup_report.return_value = "Setup OK"
            mock_setup.return_value = mock_setup_instance
            
            # Mock status
            mock_status_instance = Mock()
            mock_status_instance.get_system_status.return_value = "System Healthy"
            mock_status.return_value = mock_status_instance
            
            # Mock processor
            mock_processor_instance = Mock()
            mock_processor_instance.process_all_files.return_value = {'processed_count': 1}
            mock_processor.return_value = mock_processor_instance
            
            # Run setup -> status -> process workflow
            setup_result = runner.invoke(setup)
            assert setup_result.exit_code == 0
            
            status_result = runner.invoke(status)
            assert status_result.exit_code == 0
            
            process_result = runner.invoke(process)
            assert process_result.exit_code == 0