"""Tests for voice processing notifications system"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from voice_task_manager.utils.notifications import (
    VoiceNotificationSystem, 
    NotificationPriority, 
    NotificationChannel,
    NotificationConfig
)
from voice_task_manager.models.voice_file import VoiceFile
from voice_task_manager.models.task import Task


class TestNotificationConfig:
    """Test cases for NotificationConfig dataclass"""
    
    def test_config_defaults(self):
        """Test default configuration values"""
        config = NotificationConfig(enabled_channels=[NotificationChannel.DESKTOP])
        
        assert config.desktop_enabled is True
        assert config.email_enabled is False
        assert config.console_enabled is True
        assert config.log_enabled is True
        assert config.smtp_port == 587
        assert config.desktop_icon == "audio-headphones"
        assert config.app_name == "Voice Task Manager"
        assert config.max_transcript_length == 100


class TestVoiceNotificationSystem:
    """Test cases for VoiceNotificationSystem"""
    
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
    def notification_system(self, temp_project_root):
        """Create a VoiceNotificationSystem instance"""
        return VoiceNotificationSystem(temp_project_root)
    
    @pytest.fixture
    def sample_voice_file(self):
        """Create a sample VoiceFile for testing"""
        voice_file = VoiceFile(
            file_id="test_file_123",
            transcript="This is a test voice recording for notifications",
            file_size=1024000,
            duration_seconds=15.5
        )
        voice_file.mark_completed(
            "This is a test voice recording for notifications",
            "https://notion.so/test-task-url"
        )
        return voice_file
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample Task for testing"""
        return Task(
            task_id="test_task_123",
            title="Test Task from Voice",
            content="This is a test task created from voice recording",
            url="https://notion.so/test-task-url",
            voice_file_id="test_file_123"
        )
    
    def test_notification_system_initialization(self, temp_project_root):
        """Test notification system initialization"""
        system = VoiceNotificationSystem(temp_project_root)
        
        assert system.project_root == temp_project_root
        assert isinstance(system.config, NotificationConfig)
        assert system.notification_history == []
        assert isinstance(system.templates, dict)
    
    @patch.dict(os.environ, {
        'NOTIFICATIONS_DESKTOP_ENABLED': 'true',
        'NOTIFICATIONS_EMAIL_ENABLED': 'false',
        'NOTIFICATIONS_CONSOLE_ENABLED': 'true',
        'NOTIFICATIONS_LOG_ENABLED': 'true'
    })
    def test_config_loading_from_environment(self, temp_project_root):
        """Test loading configuration from environment variables"""
        system = VoiceNotificationSystem(temp_project_root)
        
        assert system.config.desktop_enabled is True
        assert system.config.email_enabled is False
        assert system.config.console_enabled is True
        assert system.config.log_enabled is True
        assert NotificationChannel.DESKTOP in system.config.enabled_channels
        assert NotificationChannel.CONSOLE in system.config.enabled_channels
        assert NotificationChannel.LOG in system.config.enabled_channels
    
    @patch.dict(os.environ, {
        'SMTP_SERVER': 'smtp.test.com',
        'SMTP_PORT': '465',
        'SMTP_USER': 'test@example.com',
        'SMTP_PASS': 'testpass', 
        'FROM_EMAIL': 'from@example.com',
        'NOTIFICATION_EMAIL': 'notify@example.com',
        'NOTIFICATION_ICON': 'test-icon',
        'NOTIFICATION_APP_NAME': 'Test App'
    })
    def test_config_loading_email_settings(self, temp_project_root):
        """Test loading email configuration from environment"""
        system = VoiceNotificationSystem(temp_project_root)
        
        assert system.config.smtp_server == 'smtp.test.com'
        assert system.config.smtp_port == 465
        assert system.config.smtp_user == 'test@example.com'
        assert system.config.smtp_pass == 'testpass'
        assert system.config.from_email == 'from@example.com'
        assert system.config.notification_email == 'notify@example.com'
        assert system.config.desktop_icon == 'test-icon'
        assert system.config.app_name == 'Test App'
    
    def test_templates_loading(self, notification_system):
        """Test notification templates are loaded correctly"""
        templates = notification_system.templates
        
        assert 'processing_success' in templates
        assert 'processing_error' in templates
        assert 'daily_summary' in templates
        assert 'system_health' in templates
        
        # Check template structure
        success_template = templates['processing_success']
        assert 'desktop_title' in success_template
        assert 'desktop_message' in success_template
        assert 'email_subject' in success_template
        assert 'email_body' in success_template
        assert 'console_message' in success_template
    
    @patch('subprocess.run')
    def test_send_desktop_notification_success(self, mock_subprocess, notification_system):
        """Test successful desktop notification sending"""
        mock_subprocess.return_value = Mock(returncode=0)
        
        template = {'desktop_title': 'Test Title', 'desktop_message': 'Test message'}
        variables = {}
        
        result = notification_system._send_desktop_notification(
            template, variables, NotificationPriority.NORMAL
        )
        
        assert result is True
        mock_subprocess.assert_called_once()
        
        # Check command structure
        call_args = mock_subprocess.call_args[0][0]
        assert 'notify-send' in call_args
        assert '--urgency' in call_args
        assert 'normal' in call_args
    
    @patch('subprocess.run')
    def test_send_desktop_notification_fallback(self, mock_subprocess, notification_system):
        """Test desktop notification fallback to simple notify-send"""
        # First call fails, second succeeds
        mock_subprocess.side_effect = [
            Mock(side_effect=subprocess.CalledProcessError(1, 'notify-send')),
            Mock(returncode=0)
        ]
        
        template = {'desktop_title': 'Test Title', 'desktop_message': 'Test message'}
        variables = {}
        
        result = notification_system._send_desktop_notification(
            template, variables, NotificationPriority.NORMAL
        )
        
        assert result is True
        assert mock_subprocess.call_count == 2
    
    @patch('subprocess.run')
    def test_send_desktop_notification_failure(self, mock_subprocess, notification_system):
        """Test desktop notification complete failure"""
        mock_subprocess.side_effect = Exception("Command not found")
        
        template = {'desktop_title': 'Test Title', 'desktop_message': 'Test message'}
        variables = {}
        
        result = notification_system._send_desktop_notification(
            template, variables, NotificationPriority.NORMAL
        )
        
        assert result is False
    
    @patch('smtplib.SMTP')
    @patch('src.voice_task_manager.utils.notifications.EMAIL_AVAILABLE', True)
    def test_send_email_notification_success(self, mock_smtp_class, notification_system):
        """Test successful email notification sending"""
        # Configure email settings
        notification_system.config.email_enabled = True
        notification_system.config.smtp_server = 'smtp.test.com'
        notification_system.config.smtp_user = 'test@example.com'
        notification_system.config.smtp_pass = 'testpass'
        notification_system.config.notification_email = 'notify@example.com'
        
        # Mock SMTP
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp
        
        template = {
            'email_subject': 'Test Subject',
            'email_body': 'Test email body'
        }
        variables = {}
        
        result = notification_system._send_email_notification(template, variables)
        
        assert result is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with('test@example.com', 'testpass')
        mock_smtp.send_message.assert_called_once()
        mock_smtp.quit.assert_called_once()
    
    def test_send_email_notification_not_available(self, notification_system):
        """Test email notification when email is not available"""
        notification_system.config.email_enabled = False
        
        template = {'email_subject': 'Test', 'email_body': 'Test'}
        variables = {}
        
        result = notification_system._send_email_notification(template, variables)
        
        assert result is False
    
    @patch('src.voice_task_manager.utils.notifications.EMAIL_AVAILABLE', True)
    def test_send_email_notification_missing_config(self, notification_system):
        """Test email notification with missing configuration"""
        notification_system.config.email_enabled = True
        notification_system.config.smtp_server = None  # Missing required config
        
        template = {'email_subject': 'Test', 'email_body': 'Test'}
        variables = {}
        
        result = notification_system._send_email_notification(template, variables)
        
        assert result is False
    
    @patch('src.voice_task_manager.utils.notifications.HAS_RICH', True)
    def test_send_console_notification_with_rich(self, notification_system):
        """Test console notification with Rich formatting"""
        with patch.object(notification_system, 'console') as mock_console:
            template = {'console_message': 'Test console message'}
            variables = {}
            
            result = notification_system._send_console_notification(
                template, variables, NotificationPriority.HIGH
            )
            
            assert result is True
            mock_console.print.assert_called_once()
    
    @patch('src.voice_task_manager.utils.notifications.HAS_RICH', False)
    def test_send_console_notification_plain_text(self, notification_system):
        """Test console notification without Rich (plain text)"""
        template = {'console_message': 'Test console message'}
        variables = {}
        
        with patch('builtins.print') as mock_print:
            result = notification_system._send_console_notification(
                template, variables, NotificationPriority.CRITICAL
            )
            
            assert result is True
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert '🚨' in call_args  # Critical priority prefix
            assert 'Test console message' in call_args
    
    def test_send_log_notification(self, notification_system):
        """Test log notification"""
        template = {'console_message': 'Test log message'}
        variables = {}
        
        with patch.object(notification_system.logger, 'info') as mock_log:
            result = notification_system._send_log_notification(template, variables)
            
            assert result is True
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0][0]
            assert 'Notification: Test log message' in call_args
    
    def test_truncate_text(self, notification_system):
        """Test text truncation functionality"""
        # Short text - no truncation
        short_text = "Short message"
        result = notification_system._truncate_text(short_text, 50)
        assert result == short_text
        
        # Long text - should truncate
        long_text = "A" * 100
        result = notification_system._truncate_text(long_text, 50)
        assert len(result) == 50
        assert result.endswith("...")
        assert result == "A" * 47 + "..."
    
    @patch('subprocess.run')
    def test_notify_processing_success(self, mock_subprocess, notification_system, sample_voice_file, sample_task):
        """Test processing success notification"""
        mock_subprocess.return_value = Mock(returncode=0)
        
        with patch.object(notification_system.logger, 'info'):
            results = notification_system.notify_processing_success(sample_voice_file, sample_task)
            
            # Should attempt desktop, console, and log notifications
            expected_channels = ['desktop', 'console', 'log']
            for channel in expected_channels:
                assert channel in results
            
            # Check notification history was recorded
            assert len(notification_system.notification_history) == 1
            history_entry = notification_system.notification_history[0]
            assert history_entry['template'] == 'processing_success'
            assert history_entry['priority'] == 'normal'
    
    def test_notify_processing_error(self, notification_system):
        """Test processing error notification"""
        file_id = "error_file_123"
        error_message = "Processing failed due to network error"
        
        with patch.object(notification_system.logger, 'info'):
            results = notification_system.notify_processing_error(file_id, error_message)
            
            # Should have attempted notifications
            assert isinstance(results, dict)
            
            # Check notification history
            assert len(notification_system.notification_history) == 1
            history_entry = notification_system.notification_history[0]
            assert history_entry['template'] == 'processing_error'
            assert history_entry['priority'] == 'high'
    
    @patch('src.voice_task_manager.utils.notifications.VoiceDatabase')
    def test_notify_daily_summary_no_activity(self, mock_db_class, notification_system):
        """Test daily summary notification with no activity"""
        # Mock database to return no activity
        mock_db = Mock()
        mock_db.get_processing_stats.return_value = {
            'today_processed': 0,
            'total_files': 5,
            'success_rate': 100.0
        }
        mock_db.get_all_voice_files.return_value = []
        mock_db_class.return_value = mock_db
        
        results = notification_system.notify_daily_summary()
        
        # Should skip notification when no activity
        assert results.get('skipped') is True
    
    @patch('src.voice_task_manager.utils.notifications.VoiceDatabase')
    def test_notify_daily_summary_with_activity(self, mock_db_class, notification_system):
        """Test daily summary notification with activity"""
        # Mock database to return activity
        mock_db = Mock()
        mock_db.get_processing_stats.return_value = {
            'today_processed': 3,
            'total_files': 8,
            'success_rate': 87.5
        }
        
        # Mock recent files
        recent_files = [
            VoiceFile(file_id="file1", transcript="First transcript"),
            VoiceFile(file_id="file2", transcript="Second transcript")
        ]
        for f in recent_files:
            f.processed_at = datetime.now()
        
        mock_db.get_all_voice_files.return_value = recent_files
        mock_db_class.return_value = mock_db
        
        with patch.object(notification_system.logger, 'info'):
            results = notification_system.notify_daily_summary()
            
            # Should send notifications
            assert 'skipped' not in results
            assert len(notification_system.notification_history) == 1
    
    def test_notify_system_health(self, notification_system):
        """Test system health notification"""
        status = "WARNING"
        success_rate = 85.5
        issue_count = 2
        details = "Some components need attention"
        
        with patch.object(notification_system.logger, 'info'):
            results = notification_system.notify_system_health(
                status, success_rate, issue_count, details
            )
            
            assert isinstance(results, dict)
            
            # Check notification history
            assert len(notification_system.notification_history) == 1
            history_entry = notification_system.notification_history[0]
            assert history_entry['template'] == 'system_health'
            assert history_entry['priority'] == 'high'  # WARNING maps to HIGH
    
    def test_get_processing_stats(self, notification_system):
        """Test getting processing statistics for notifications"""
        with patch.object(notification_system.database, 'get_processing_stats') as mock_stats:
            mock_stats.return_value = {
                'total_files': 10,
                'today_processed': 3,
                'success_rate': 85.0
            }
            
            with patch.object(notification_system.database, 'get_all_voice_files') as mock_files:
                mock_files.return_value = []
                
                stats = notification_system.get_processing_stats()
                
                assert stats['total_count'] == 10
                assert stats['today_count'] == 3
                assert stats['success_rate'] == 85.0
                assert stats['recent_files'] == []
    
    def test_test_notifications(self, notification_system):
        """Test the test notifications functionality"""
        with patch.object(notification_system, '_send_notification') as mock_send:
            mock_send.return_value = {'desktop': True, 'console': True}
            
            results = notification_system.test_notifications()
            
            assert isinstance(results, dict)
            mock_send.assert_called_once()
            
            # Check that test variables were used
            call_args = mock_send.call_args
            assert call_args[0][0] == 'processing_success'  # template name
            assert 'file_id' in call_args[0][1]  # variables
            assert call_args[0][1]['file_id'] == 'test_file_123'
    
    def test_get_notification_history(self, notification_system):
        """Test getting notification history"""
        # Add some mock history
        now = datetime.now()
        notification_system.notification_history = [
            {
                'timestamp': now - timedelta(hours=2),
                'template': 'processing_success',
                'priority': 'normal'
            },
            {
                'timestamp': now - timedelta(hours=25),  # Older than 24h
                'template': 'processing_error',
                'priority': 'high'
            },
            {
                'timestamp': now - timedelta(minutes=30),
                'template': 'daily_summary',
                'priority': 'low'
            }
        ]
        
        # Get last 24 hours (default)
        recent = notification_system.get_notification_history()
        assert len(recent) == 2  # Should exclude the 25-hour-old entry
        
        # Get last 48 hours
        extended = notification_system.get_notification_history(hours_back=48)
        assert len(extended) == 3  # Should include all entries
    
    def test_get_notification_status(self, notification_system):
        """Test getting notification system status"""
        status = notification_system.get_notification_status()
        
        assert isinstance(status, str)
        assert "Notification System Status" in status
        assert "Enabled Channels:" in status
        assert "Desktop:" in status
        assert "Email:" in status
        assert "Console:" in status
        assert "Logging:" in status
        assert "Recent notifications:" in status
    
    def test_notification_priority_enum(self):
        """Test NotificationPriority enum values"""
        assert NotificationPriority.LOW.value == "low"
        assert NotificationPriority.NORMAL.value == "normal"
        assert NotificationPriority.HIGH.value == "high"
        assert NotificationPriority.CRITICAL.value == "critical"
    
    def test_notification_channel_enum(self):
        """Test NotificationChannel enum values"""
        assert NotificationChannel.DESKTOP.value == "desktop"
        assert NotificationChannel.EMAIL.value == "email"
        assert NotificationChannel.CONSOLE.value == "console"
        assert NotificationChannel.LOG.value == "log"
    
    def test_convenience_functions(self):
        """Test convenience functions"""
        from voice_task_manager.utils.notifications import (
            get_notification_system, notify_success, notify_error, 
            send_daily_summary, test_notification_system
        )
        
        # Test get_notification_system
        system = get_notification_system()
        assert isinstance(system, VoiceNotificationSystem)
        
        # Test other convenience functions exist and are callable
        assert callable(notify_success)
        assert callable(notify_error)
        assert callable(send_daily_summary)
        assert callable(test_notification_system)