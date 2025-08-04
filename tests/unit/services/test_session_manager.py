"""
Unit tests for ClaudeSessionManager
"""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import subprocess

from voice_task_manager.services.session_manager import (
    ClaudeSessionManager, AuthStatus, SessionInfo
)


class TestClaudeSessionManager:
    """Test suite for Claude session management"""
    
    @pytest.fixture
    def mock_logger(self):
        """Mock logger fixture"""
        return Mock()
        
    @pytest.fixture
    def temp_credentials_dir(self):
        """Create temporary directory for credentials"""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = Path(tmpdir) / ".claude"
            claude_dir.mkdir()
            yield claude_dir
            
    @pytest.fixture
    def session_manager(self, mock_logger, temp_credentials_dir):
        """Create session manager with mocked dependencies"""
        with patch('voice_task_manager.services.session_manager.Path.home', 
                  return_value=temp_credentials_dir.parent):
            manager = ClaudeSessionManager(logger=mock_logger)
            manager.notifier = Mock()
            return manager
            
    def test_init(self, session_manager):
        """Test session manager initialization"""
        assert session_manager.logger is not None
        assert session_manager.notifier is not None
        assert session_manager.credentials_path.name == ".credentials.json"
        assert session_manager.expiry_warning_days == 7
        assert session_manager.estimated_token_lifetime == timedelta(days=30)
        
    def test_get_session_info_missing_file(self, session_manager):
        """Test when credentials file doesn't exist"""
        info = session_manager.get_session_info()
        
        assert info.status == AuthStatus.MISSING
        assert info.error == "Claude credentials file not found"
        assert info.last_check is not None
        
    def test_get_session_info_valid_oauth(self, session_manager, temp_credentials_dir):
        """Test with valid OAuth credentials"""
        # Create credentials file
        creds_file = temp_credentials_dir / ".credentials.json"
        creds_data = {"claudeAiOauth": {"token": "test-token"}}
        creds_file.write_text(json.dumps(creds_data))
        
        # Set modification time to recent
        recent_time = datetime.now().timestamp()
        import os
        os.utime(creds_file, (recent_time, recent_time))
        
        info = session_manager.get_session_info()
        
        assert info.status == AuthStatus.VALID
        assert info.credentials_path == creds_file
        assert info.expiry_estimate is not None
        assert info.error is None
        
    def test_get_session_info_expiring_soon(self, session_manager, temp_credentials_dir):
        """Test with OAuth expiring soon"""
        # Create credentials file
        creds_file = temp_credentials_dir / ".credentials.json"
        creds_data = {"claudeAiOauth": {"token": "test-token"}}
        creds_file.write_text(json.dumps(creds_data))
        
        # Set modification time to 25 days ago (expiring in 5 days)
        old_time = (datetime.now() - timedelta(days=25)).timestamp()
        import os
        os.utime(creds_file, (old_time, old_time))
        
        info = session_manager.get_session_info()
        
        assert info.status == AuthStatus.EXPIRING_SOON
        assert info.expiry_estimate is not None
        
    def test_get_session_info_expired(self, session_manager, temp_credentials_dir):
        """Test with expired OAuth"""
        # Create credentials file
        creds_file = temp_credentials_dir / ".credentials.json"
        creds_data = {"claudeAiOauth": {"token": "test-token"}}
        creds_file.write_text(json.dumps(creds_data))
        
        # Set modification time to 35 days ago (expired)
        old_time = (datetime.now() - timedelta(days=35)).timestamp()
        import os
        os.utime(creds_file, (old_time, old_time))
        
        info = session_manager.get_session_info()
        
        assert info.status == AuthStatus.EXPIRED
        
    def test_get_session_info_missing_oauth_data(self, session_manager, temp_credentials_dir):
        """Test when credentials file exists but lacks OAuth data"""
        # Create credentials file without OAuth
        creds_file = temp_credentials_dir / ".credentials.json"
        creds_data = {"other": "data"}
        creds_file.write_text(json.dumps(creds_data))
        
        info = session_manager.get_session_info()
        
        assert info.status == AuthStatus.MISSING
        assert info.error == "OAuth data not found in credentials"
        
    def test_get_session_info_invalid_json(self, session_manager, temp_credentials_dir):
        """Test with invalid JSON in credentials file"""
        # Create invalid credentials file
        creds_file = temp_credentials_dir / ".credentials.json"
        creds_file.write_text("invalid json")
        
        info = session_manager.get_session_info()
        
        assert info.status == AuthStatus.UNKNOWN
        assert info.error is not None
        
    @patch('subprocess.run')
    def test_test_claude_execution_success(self, mock_run, session_manager):
        """Test successful Claude execution"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        success, error = session_manager.test_claude_execution()
        
        assert success is True
        assert error is None
        assert session_manager.last_successful_use is not None
        
        # Verify command
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[1] == "-p"
        assert args[2] == "Return only: OK"
        assert "--dangerously-skip-permissions" in args
        
    @patch('subprocess.run')
    def test_test_claude_execution_failure(self, mock_run, session_manager):
        """Test failed Claude execution"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Authentication failed"
        mock_result.stdout = ""
        mock_run.return_value = mock_result
        
        success, error = session_manager.test_claude_execution()
        
        assert success is False
        assert error == "Authentication failed"
        
    @patch('subprocess.run')
    def test_test_claude_execution_timeout(self, mock_run, session_manager):
        """Test Claude execution timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired('cmd', 30)
        
        success, error = session_manager.test_claude_execution()
        
        assert success is False
        assert error == "Claude execution timed out"
        
    @patch('subprocess.run')
    def test_test_claude_execution_exception(self, mock_run, session_manager):
        """Test Claude execution with exception"""
        mock_run.side_effect = Exception("Test error")
        
        success, error = session_manager.test_claude_execution()
        
        assert success is False
        assert error == "Test error"
        
    @patch.object(ClaudeSessionManager, 'get_session_info')
    @patch.object(ClaudeSessionManager, 'test_claude_execution')
    def test_check_and_notify_expired(self, mock_test, mock_get_info, session_manager):
        """Test notification for expired session"""
        # Mock expired session
        mock_info = SessionInfo(
            status=AuthStatus.VALID,
            last_check=datetime.now()
        )
        mock_get_info.return_value = mock_info
        mock_test.return_value = (False, "Auth error")
        
        info = session_manager.check_and_notify(force=True)
        
        assert info.status == AuthStatus.EXPIRED
        assert info.error == "Auth error"
        session_manager.notifier.send_notification.assert_called_once()
        
    @patch.object(ClaudeSessionManager, 'get_session_info')
    def test_check_and_notify_expiring_soon(self, mock_get_info, session_manager):
        """Test notification for expiring session"""
        # Mock expiring session
        mock_info = SessionInfo(
            status=AuthStatus.EXPIRING_SOON,
            last_check=datetime.now(),
            expiry_estimate=datetime.now() + timedelta(days=5)
        )
        mock_get_info.return_value = mock_info
        
        info = session_manager.check_and_notify(force=True)
        
        assert info.status == AuthStatus.EXPIRING_SOON
        session_manager.notifier.send_notification.assert_called_once()
        
    @patch.object(ClaudeSessionManager, 'get_session_info')
    def test_check_and_notify_missing(self, mock_get_info, session_manager):
        """Test notification for missing credentials"""
        # Mock missing credentials
        mock_info = SessionInfo(
            status=AuthStatus.MISSING,
            last_check=datetime.now()
        )
        mock_get_info.return_value = mock_info
        
        info = session_manager.check_and_notify(force=True)
        
        assert info.status == AuthStatus.MISSING
        session_manager.notifier.send_notification.assert_called_once()
        
    def test_check_and_notify_skip_recent(self, session_manager):
        """Test skipping check if recently checked"""
        # Set recent check time
        session_manager.last_check = datetime.now() - timedelta(minutes=10)
        
        with patch.object(session_manager, 'get_session_info') as mock_get:
            mock_info = SessionInfo(status=AuthStatus.VALID, last_check=datetime.now())
            mock_get.return_value = mock_info
            
            info = session_manager.check_and_notify(force=False)
            
            # Should not test execution when skipping
            assert mock_get.called
            
    @patch.object(ClaudeSessionManager, 'get_session_info')
    def test_can_use_claude_valid(self, mock_get_info, session_manager):
        """Test can_use_claude with valid status"""
        mock_info = SessionInfo(status=AuthStatus.VALID, last_check=datetime.now())
        mock_get_info.return_value = mock_info
        
        assert session_manager.can_use_claude() is True
        
    @patch.object(ClaudeSessionManager, 'get_session_info')
    def test_can_use_claude_expiring(self, mock_get_info, session_manager):
        """Test can_use_claude with expiring status"""
        mock_info = SessionInfo(status=AuthStatus.EXPIRING_SOON, last_check=datetime.now())
        mock_get_info.return_value = mock_info
        
        assert session_manager.can_use_claude() is True
        
    @patch.object(ClaudeSessionManager, 'get_session_info')
    def test_can_use_claude_expired(self, mock_get_info, session_manager):
        """Test can_use_claude with expired status"""
        mock_info = SessionInfo(status=AuthStatus.EXPIRED, last_check=datetime.now())
        mock_get_info.return_value = mock_info
        
        assert session_manager.can_use_claude() is False