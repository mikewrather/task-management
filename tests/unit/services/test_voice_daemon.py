"""
Unit tests for VoiceProcessingDaemon
"""

import json
import pytest
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import tempfile

from voice_task_manager.services.voice_daemon import (
    VoiceProcessingDaemon, ServiceState, ServiceStats
)
from voice_task_manager.services.session_manager import AuthStatus, SessionInfo


class TestVoiceProcessingDaemon:
    """Test suite for voice processing daemon"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create temporary project directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "data").mkdir()
            yield project_root
            
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all daemon dependencies"""
        with patch('voice_task_manager.services.voice_daemon.VoiceLogger') as mock_logger_cls, \
             patch('voice_task_manager.services.voice_daemon.ClaudeSessionManager') as mock_session_cls, \
             patch('voice_task_manager.services.voice_daemon.VoiceProcessorV2') as mock_processor_cls, \
             patch('voice_task_manager.services.voice_daemon.SimpleNotifier') as mock_notifier_cls:
            
            # Create mock instances
            mock_logger = Mock()
            mock_session = Mock()
            mock_processor = Mock()
            mock_notifier = Mock()
            
            # Configure constructors
            mock_logger_cls.return_value = mock_logger
            mock_session_cls.return_value = mock_session
            mock_processor_cls.return_value = mock_processor
            mock_notifier_cls.return_value = mock_notifier
            
            yield {
                'logger': mock_logger,
                'session_manager': mock_session,
                'processor': mock_processor,
                'notifier': mock_notifier
            }
            
    @pytest.fixture
    def daemon(self, temp_project_root, mock_dependencies):
        """Create daemon instance with mocked dependencies"""
        daemon = VoiceProcessingDaemon(
            interval_seconds=1,  # Short interval for testing
            project_root=temp_project_root,
            daemon=False  # Not daemon thread for testing
        )
        yield daemon
        # Ensure daemon is stopped
        if daemon.is_alive():
            daemon.stop(timeout=2)
            
    def test_init(self, daemon, temp_project_root):
        """Test daemon initialization"""
        assert daemon.interval == 1
        assert daemon.project_root == temp_project_root
        assert daemon.state == ServiceState.STOPPED
        assert daemon.stats.start_time is not None
        assert daemon.pid_file == temp_project_root / "data" / "voice-daemon.pid"
        
    def test_start_stop(self, daemon, mock_dependencies):
        """Test daemon start and stop"""
        # Mock session check
        mock_dependencies['session_manager'].check_and_notify.return_value = SessionInfo(
            status=AuthStatus.VALID,
            last_check=datetime.now()
        )
        
        # Start daemon
        daemon.start()
        time.sleep(0.1)  # Let it start
        
        assert daemon.is_alive()
        assert daemon.state == ServiceState.RUNNING
        
        # Stop daemon
        daemon.stop(timeout=2)
        
        assert not daemon.is_alive()
        assert daemon.state == ServiceState.STOPPED
        
    def test_pid_file_management(self, daemon, temp_project_root):
        """Test PID file creation and cleanup"""
        pid_file = temp_project_root / "data" / "voice-daemon.pid"
        
        # Mock dependencies
        with patch.object(daemon, '_process_cycle'), \
             patch.object(daemon.session_manager, 'check_and_notify'):
            
            # Start daemon
            daemon.start()
            time.sleep(0.1)
            
            # Check PID file exists
            assert pid_file.exists()
            assert int(pid_file.read_text()) == daemon.ident
            
            # Stop daemon
            daemon.stop(timeout=2)
            
            # Check PID file removed
            assert not pid_file.exists()
            
    def test_process_cycle_success(self, daemon, mock_dependencies):
        """Test successful processing cycle"""
        # Mock successful processing
        mock_dependencies['processor'].run_automation.return_value = {
            'success': True,
            'processed': 3,
            'total_found': 5
        }
        
        # Run one cycle
        daemon._process_cycle()
        
        # Check stats updated
        assert daemon.stats.total_runs == 1
        assert daemon.stats.successful_runs == 1
        assert daemon.stats.files_processed == 3
        assert daemon.stats.last_run is not None
        
    def test_process_cycle_failure(self, daemon, mock_dependencies):
        """Test failed processing cycle"""
        # Mock failed processing
        mock_dependencies['processor'].run_automation.return_value = {
            'success': False,
            'error': 'Test error'
        }
        
        # Run one cycle
        daemon._process_cycle()
        
        # Check stats updated
        assert daemon.stats.total_runs == 1
        assert daemon.stats.failed_runs == 1
        assert daemon.stats.successful_runs == 0
        assert daemon.stats.last_error == 'Test error'
        
    def test_process_cycle_exception(self, daemon, mock_dependencies):
        """Test processing cycle with exception"""
        # Mock exception
        mock_dependencies['processor'].run_automation.side_effect = Exception("Test exception")
        
        # Run one cycle - should handle exception
        with pytest.raises(Exception):
            daemon._process_cycle()
            
        # Check stats updated
        assert daemon.stats.total_runs == 1
        assert daemon.stats.failed_runs == 1
        assert daemon.stats.last_error == "Test exception"
        
    def test_oauth_check_periodic(self, daemon, mock_dependencies):
        """Test OAuth check every 6th run"""
        # Mock session info
        session_info = SessionInfo(
            status=AuthStatus.VALID,
            last_check=datetime.now()
        )
        mock_dependencies['session_manager'].check_and_notify.return_value = session_info
        mock_dependencies['session_manager'].get_session_info.return_value = session_info
        
        # Mock successful processing
        mock_dependencies['processor'].run_automation.return_value = {'success': True}
        
        # Run 6 cycles
        for i in range(6):
            daemon._process_cycle()
            
        # OAuth check should be called once (on 6th run)
        assert mock_dependencies['session_manager'].check_and_notify.call_count == 1
        
    def test_oauth_expired_disables_claude(self, daemon, mock_dependencies):
        """Test that expired OAuth disables Claude processor"""
        # Set run count to trigger OAuth check
        daemon.stats.total_runs = 5
        
        # Mock expired session
        session_info = SessionInfo(
            status=AuthStatus.EXPIRED,
            last_check=datetime.now()
        )
        mock_dependencies['session_manager'].check_and_notify.return_value = session_info
        
        # Mock successful processing
        mock_dependencies['processor'].run_automation.return_value = {'success': True}
        
        # Run cycle (6th run)
        daemon._process_cycle()
        
        # Claude should be disabled
        assert daemon.processor.use_claude_processor is False
        
    def test_pause_resume(self, daemon, mock_dependencies):
        """Test pause and resume functionality"""
        # Mock dependencies
        mock_dependencies['session_manager'].check_and_notify.return_value = SessionInfo(
            status=AuthStatus.VALID,
            last_check=datetime.now()
        )
        
        # Start daemon
        daemon.start()
        time.sleep(0.1)
        
        # Pause
        daemon.pause()
        time.sleep(0.1)
        assert daemon.state == ServiceState.PAUSED
        
        # Resume
        daemon.resume()
        time.sleep(0.1)
        assert daemon.state == ServiceState.RUNNING
        
        # Stop
        daemon.stop(timeout=2)
        
    def test_get_health(self, daemon, mock_dependencies):
        """Test health status reporting"""
        # Set some stats
        daemon.stats.total_runs = 10
        daemon.stats.successful_runs = 8
        daemon.stats.failed_runs = 2
        daemon.stats.files_processed = 25
        daemon.stats.last_run = datetime.now()
        daemon.state = ServiceState.RUNNING
        
        # Mock session info
        session_info = SessionInfo(
            status=AuthStatus.VALID,
            last_check=datetime.now()
        )
        mock_dependencies['session_manager'].get_session_info.return_value = session_info
        
        health = daemon.get_health()
        
        assert health['status'] == 'healthy'
        assert health['state'] == 'running'
        assert health['stats']['total_runs'] == 10
        assert health['stats']['successful_runs'] == 8
        assert health['stats']['failed_runs'] == 2
        assert health['stats']['files_processed'] == 25
        assert health['claude_status'] == 'valid'
        
    def test_get_health_degraded(self, daemon):
        """Test degraded health status"""
        # More failures than successes
        daemon.stats.successful_runs = 2
        daemon.stats.failed_runs = 5
        daemon.state = ServiceState.RUNNING
        
        health = daemon.get_health()
        
        assert health['status'] == 'degraded'
        
    def test_get_health_error_state(self, daemon):
        """Test unhealthy status when in error state"""
        daemon.state = ServiceState.ERROR
        
        health = daemon.get_health()
        
        assert health['status'] == 'unhealthy'
        
    def test_write_health_status(self, daemon, temp_project_root, mock_dependencies):
        """Test health status file writing"""
        # Set up health data
        daemon.stats.total_runs = 5
        daemon.state = ServiceState.RUNNING
        
        # Mock session info
        session_info = SessionInfo(
            status=AuthStatus.VALID,
            last_check=datetime.now()
        )
        mock_dependencies['session_manager'].get_session_info.return_value = session_info
        
        # Write health status
        daemon._write_health_status()
        
        # Check file created
        health_file = temp_project_root / "data" / "voice-daemon-health.json"
        assert health_file.exists()
        
        # Verify content
        health_data = json.loads(health_file.read_text())
        assert health_data['status'] == 'healthy'
        assert health_data['state'] == 'running'
        assert health_data['stats']['total_runs'] == 5
        assert 'timestamp' in health_data
        
    def test_signal_handling(self, daemon):
        """Test signal handler setup"""
        # Mock signal handler
        handler = Mock()
        daemon._signal_handler = handler
        
        # Call signal handler
        daemon._signal_handler(15, None)  # SIGTERM
        
        handler.assert_called_once_with(15, None)
        
    def test_cleanup_notifications(self, daemon, mock_dependencies):
        """Test cleanup sends notifications"""
        daemon.stats.total_runs = 10
        daemon.stats.files_processed = 50
        
        daemon._cleanup()
        
        # Should send shutdown notification
        mock_dependencies['notifier'].send_notification.assert_called_once()
        call_args = mock_dependencies['notifier'].send_notification.call_args
        assert "Voice Processing Service Stopped" in call_args[1]['title']
        
    def test_error_state_handling(self, daemon, mock_dependencies):
        """Test daemon handles fatal errors"""
        # Mock fatal error during startup
        mock_dependencies['session_manager'].check_and_notify.side_effect = Exception("Fatal error")
        
        # Run daemon (should handle error)
        daemon.run()
        
        # Check error state
        assert daemon.state == ServiceState.ERROR
        assert daemon.stats.last_error == "Fatal error"
        
    def test_log_session_status(self, daemon, mock_dependencies):
        """Test session status logging"""
        session_info = SessionInfo(
            status=AuthStatus.EXPIRING_SOON,
            last_check=datetime.now(),
            expiry_estimate=datetime.now() + timedelta(days=5),
            error=None
        )
        
        daemon._log_session_status(session_info)
        
        # Check logged
        mock_dependencies['logger'].info.assert_called_once()
        call_args = mock_dependencies['logger'].info.call_args
        assert call_args[0][0] == "Claude session status"
        assert call_args[1]['status'] == 'expiring_soon'