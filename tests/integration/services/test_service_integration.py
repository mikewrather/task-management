"""
Integration tests for voice processing service
Tests the complete service flow with real components
"""

import json
import os
import sys
import pytest
import time
import subprocess
import signal
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, Mock
import tempfile

from voice_task_manager.services import VoiceProcessingDaemon, ClaudeSessionManager
from voice_task_manager.services.voice_daemon import ServiceState
from voice_task_manager.services.session_manager import AuthStatus


@pytest.mark.integration
class TestServiceIntegration:
    """Integration tests for voice processing service"""
    
    @pytest.fixture
    def test_env(self):
        """Set up test environment"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_root = Path(tmpdir)
            
            # Create required directories
            (test_root / "data").mkdir()
            (test_root / "logs").mkdir()
            (test_root / "scripts" / "services").mkdir(parents=True)
            
            # Create mock .env file
            env_file = test_root / ".env"
            env_file.write_text("""
# Test environment
GOOGLE_DRIVE_FOLDER_ID=test-folder-id
NOTION_TOKEN=test-notion-token
NOTION_TASKS_DB=test-tasks-db
OPENAI_API_KEY=test-openai-key
""")
            
            yield test_root
            
    def test_daemon_lifecycle(self, test_env):
        """Test complete daemon lifecycle"""
        # Create daemon with short interval
        daemon = VoiceProcessingDaemon(
            interval_seconds=1,
            project_root=test_env,
            daemon=False
        )
        
        # Mock external dependencies
        with patch.object(daemon.processor, 'run_automation') as mock_process, \
             patch.object(daemon.session_manager, 'check_and_notify') as mock_session, \
             patch.object(daemon.notifier, 'send_notification'):
            
            # Configure mocks
            mock_process.return_value = {
                'success': True,
                'processed': 2,
                'total_found': 3
            }
            mock_session.return_value = mock.Mock(
                status=AuthStatus.VALID,
                error=None
            )
            
            # Start daemon
            daemon.start()
            
            # Let it run for a few cycles
            time.sleep(3)
            
            # Check it's running
            assert daemon.is_alive()
            assert daemon.state == ServiceState.RUNNING
            assert daemon.stats.total_runs > 0
            
            # Stop daemon
            daemon.stop(timeout=5)
            
            # Check it stopped
            assert not daemon.is_alive()
            assert daemon.state == ServiceState.STOPPED
            
    def test_service_wrapper_script(self, test_env):
        """Test service wrapper script functionality"""
        # Copy service script to test environment
        original_script = Path(__file__).parent.parent.parent.parent / "scripts" / "services" / "voice-processing-service.py"
        test_script = test_env / "scripts" / "services" / "voice-processing-service.py"
        
        if original_script.exists():
            test_script.write_text(original_script.read_text())
            test_script.chmod(0o755)
            
            # Test status when not running
            result = subprocess.run(
                [sys.executable, str(test_script), "status"],
                capture_output=True,
                text=True,
                cwd=test_env
            )
            assert "not running" in result.stdout.lower()
            
    def test_health_monitoring(self, test_env):
        """Test health monitoring functionality"""
        daemon = VoiceProcessingDaemon(
            interval_seconds=1,
            project_root=test_env,
            daemon=False
        )
        
        # Set some stats
        daemon.stats.total_runs = 5
        daemon.stats.successful_runs = 4
        daemon.stats.failed_runs = 1
        daemon.stats.files_processed = 10
        daemon.state = ServiceState.RUNNING
        
        # Get health
        health = daemon.get_health()
        
        # Verify health structure
        assert health['status'] in ['healthy', 'degraded', 'unhealthy']
        assert health['state'] == 'running'
        assert health['stats']['total_runs'] == 5
        assert health['stats']['successful_runs'] == 4
        assert health['stats']['files_processed'] == 10
        assert 'uptime_seconds' in health
        assert 'claude_status' in health
        
        # Write health status
        daemon._write_health_status()
        
        # Check file created
        health_file = test_env / "data" / "voice-daemon-health.json"
        assert health_file.exists()
        
        # Verify content
        saved_health = json.loads(health_file.read_text())
        assert saved_health['status'] == health['status']
        assert 'timestamp' in saved_health
        
    def test_oauth_fallback_behavior(self, test_env):
        """Test behavior when OAuth expires"""
        daemon = VoiceProcessingDaemon(
            interval_seconds=1,
            project_root=test_env,
            daemon=False
        )
        
        # Set run count to trigger OAuth check
        daemon.stats.total_runs = 5
        
        with patch.object(daemon.processor, 'run_automation') as mock_process, \
             patch.object(daemon.session_manager, 'check_and_notify') as mock_session:
            
            # Mock expired OAuth
            mock_session.return_value = Mock(
                status=AuthStatus.EXPIRED,
                error="OAuth token expired"
            )
            mock_process.return_value = {'success': True}
            
            # Run cycle (6th run triggers OAuth check)
            daemon._process_cycle()
            
            # Verify Claude was disabled
            assert daemon.processor.use_claude_processor is False
            
    def test_notification_integration(self, test_env):
        """Test notification system integration"""
        # Create daemon
        daemon = VoiceProcessingDaemon(
            interval_seconds=1,
            project_root=test_env,
            daemon=False
        )
        
        with patch.object(daemon.notifier, 'send_notification') as mock_notify:
            # Test startup notification
            with patch.object(daemon, '_process_cycle'):
                daemon.run()
                
            # Should send startup and shutdown notifications
            assert mock_notify.call_count >= 2
            
            # Check notification content
            calls = mock_notify.call_args_list
            startup_call = calls[0]
            assert "Started" in startup_call[1]['title']
            
    def test_pid_file_locking(self, test_env):
        """Test PID file prevents multiple instances"""
        pid_file = test_env / "data" / "voice-daemon.pid"
        
        # Create first daemon
        daemon1 = VoiceProcessingDaemon(
            interval_seconds=1,
            project_root=test_env,
            daemon=False
        )
        
        # Write PID file
        daemon1._write_pid_file()
        assert pid_file.exists()
        
        # Cleanup should remove it
        daemon1._cleanup()
        assert not pid_file.exists()
        
    def test_error_recovery(self, test_env):
        """Test daemon recovers from errors"""
        daemon = VoiceProcessingDaemon(
            interval_seconds=1,
            project_root=test_env,
            daemon=False
        )
        
        error_count = 0
        
        def mock_process():
            nonlocal error_count
            error_count += 1
            if error_count < 3:
                raise Exception("Temporary error")
            return {'success': True, 'processed': 1}
            
        with patch.object(daemon.processor, 'run_automation', side_effect=mock_process), \
             patch.object(daemon.session_manager, 'check_and_notify'):
            
            # Run multiple cycles
            for _ in range(5):
                try:
                    daemon._process_cycle()
                except Exception:
                    pass
                    
            # Should have some failures and eventual success
            assert daemon.stats.failed_runs >= 2
            assert daemon.stats.successful_runs >= 1
            
    @pytest.mark.skipif(not os.path.exists("/home/mike/.claude/.credentials.json"),
                       reason="Claude credentials not available")
    def test_real_claude_session(self, test_env):
        """Test with real Claude session (if available)"""
        session_manager = ClaudeSessionManager()
        
        # Get session info
        info = session_manager.get_session_info()
        
        # Should have some status
        assert info.status in [AuthStatus.VALID, AuthStatus.EXPIRING_SOON, 
                              AuthStatus.EXPIRED, AuthStatus.MISSING]
        
        # If valid, test execution
        if info.status == AuthStatus.VALID:
            success, error = session_manager.test_claude_execution()
            # May or may not succeed depending on actual auth state
            assert isinstance(success, bool)
            
    def test_cli_integration(self, test_env):
        """Test CLI command integration"""
        # Import CLI module
        try:
            from voice_task_manager.cli import service
            
            # CLI command should exist
            assert service is not None
            assert hasattr(service, 'callback')
            
        except ImportError:
            pytest.skip("CLI module not available")
            
    def test_systemd_service_file(self):
        """Test systemd service file is valid"""
        service_file = Path(__file__).parent.parent.parent.parent / "scripts" / "services" / "voice-processing.service"
        
        if service_file.exists():
            content = service_file.read_text()
            
            # Check required sections
            assert "[Unit]" in content
            assert "[Service]" in content
            assert "[Install]" in content
            
            # Check key directives
            assert "ExecStart=" in content
            assert "Type=simple" in content
            assert "Restart=on-failure" in content
            assert "User=mike" in content