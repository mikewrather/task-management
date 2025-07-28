"""
Voice Processing Notifications System
Enhanced notification management for voice processing events.

This module replaces notification-system.py with enhanced features:
- Centralized notification management with configurable channels
- Rich console output and structured logging
- Better error handling and fallback mechanisms
- Support for multiple notification types and priorities
- Integration with the new database system and models
- Template-based notification content generation
"""

import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass

# Email imports - handle gracefully if not available
try:
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from ..utils.logging import VoiceLogger
from ..utils.database import VoiceDatabase
from ..models.voice_file import VoiceFile
from ..models.task import NotionTask

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal" 
    HIGH = "high"
    CRITICAL = "critical"

class NotificationChannel(Enum):
    """Available notification channels"""
    DESKTOP = "desktop"
    EMAIL = "email"
    CONSOLE = "console"
    LOG = "log"

@dataclass
class NotificationConfig:
    """Configuration for notification system"""
    enabled_channels: List[NotificationChannel]
    email_enabled: bool = False
    desktop_enabled: bool = True
    console_enabled: bool = True
    log_enabled: bool = True
    
    # Email configuration
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None
    from_email: Optional[str] = None
    notification_email: Optional[str] = None
    
    # Desktop notification settings
    desktop_icon: str = "audio-headphones"
    app_name: str = "Voice Task Manager"
    
    # Content settings
    max_transcript_length: int = 100
    max_desktop_length: int = 200

class VoiceNotificationSystem:
    """Enhanced notification system for voice processing events"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the notification system
        
        Args:
            project_root: Project root directory (auto-detected if None)
        """
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.logger = VoiceLogger(self.project_root)
        self.database = VoiceDatabase(self.project_root)
        self.console = Console() if HAS_RICH else None
        
        # Load configuration from environment
        self.config = self._load_config()
        
        # Notification history for rate limiting and deduplication
        self.notification_history: List[Dict[str, Any]] = []
        
        # Load notification templates
        self.templates = self._load_templates()
    
    def _load_config(self) -> NotificationConfig:
        """Load notification configuration from environment variables"""
        # Determine enabled channels
        channels = []
        if os.getenv('NOTIFICATIONS_DESKTOP_ENABLED', 'true').lower() in ('true', '1', 'yes'):
            channels.append(NotificationChannel.DESKTOP)
        if os.getenv('NOTIFICATIONS_EMAIL_ENABLED', 'false').lower() in ('true', '1', 'yes') and EMAIL_AVAILABLE:
            channels.append(NotificationChannel.EMAIL)
        if os.getenv('NOTIFICATIONS_CONSOLE_ENABLED', 'true').lower() in ('true', '1', 'yes'):
            channels.append(NotificationChannel.CONSOLE)
        if os.getenv('NOTIFICATIONS_LOG_ENABLED', 'true').lower() in ('true', '1', 'yes'):
            channels.append(NotificationChannel.LOG)
        
        return NotificationConfig(
            enabled_channels=channels,
            email_enabled=EMAIL_AVAILABLE and os.getenv('NOTIFICATIONS_EMAIL_ENABLED', 'false').lower() in ('true', '1', 'yes'),
            desktop_enabled=os.getenv('NOTIFICATIONS_DESKTOP_ENABLED', 'true').lower() in ('true', '1', 'yes'),
            console_enabled=os.getenv('NOTIFICATIONS_CONSOLE_ENABLED', 'true').lower() in ('true', '1', 'yes'),
            log_enabled=os.getenv('NOTIFICATIONS_LOG_ENABLED', 'true').lower() in ('true', '1', 'yes'),
            
            # Email settings
            smtp_server=os.getenv('SMTP_SERVER'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            smtp_user=os.getenv('SMTP_USER'),
            smtp_pass=os.getenv('SMTP_PASS'),
            from_email=os.getenv('FROM_EMAIL'),
            notification_email=os.getenv('NOTIFICATION_EMAIL'),
            
            # Desktop settings
            desktop_icon=os.getenv('NOTIFICATION_ICON', 'audio-headphones'),
            app_name=os.getenv('NOTIFICATION_APP_NAME', 'Voice Task Manager'),
            
            # Content settings
            max_transcript_length=int(os.getenv('NOTIFICATION_MAX_TRANSCRIPT_LENGTH', '100')),
            max_desktop_length=int(os.getenv('NOTIFICATION_MAX_DESKTOP_LENGTH', '200'))
        )
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Load notification message templates"""
        return {
            'processing_success': {
                'desktop_title': '🎤 Voice Note Processed',
                'desktop_message': 'Created task: {short_transcript}',
                'email_subject': 'Voice Note Processed Successfully',
                'email_body': '''Your voice note has been processed and added to Notion:

Transcript: {transcript}

Task URL: {task_url}

File ID: {file_id}
Processed at: {processed_at}

---
Voice Task Management System''',
                'console_message': '✅ Successfully processed voice note: {short_transcript}'
            },
            'processing_error': {
                'desktop_title': '❌ Voice Processing Error',
                'desktop_message': 'Failed to process: {file_id}',
                'email_subject': 'Voice Processing Error',
                'email_body': '''Voice processing encountered an error:

File ID: {file_id}
Error: {error_message}
Timestamp: {timestamp}

Please check the logs for more details.

---
Voice Task Management System''',
                'console_message': '❌ Processing error for {file_id}: {error_message}'
            },
            'daily_summary': {
                'desktop_title': '📊 Daily Voice Summary',
                'desktop_message': 'Processed {count} files today',
                'email_subject': 'Daily Voice Processing Summary',
                'email_body': '''Daily Voice Processing Summary

Today: {today_count} files processed
Total: {total_count} files processed

Recent Activity:
{recent_activity}

📋 View all tasks: https://www.notion.so/183267fb-e1c1-4b3b-a42a-5ac1ab8353eb

---
Voice Task Management System''',
                'console_message': '📊 Daily summary: {today_count} files processed today'
            },
            'system_health': {
                'desktop_title': '🔧 System Health Alert',
                'desktop_message': 'Status: {status}',
                'email_subject': 'Voice System Health Alert',
                'email_body': '''System Health Report

Status: {status}
Success Rate: {success_rate}%
Recent Issues: {issue_count}

Details:
{details}

---
Voice Task Management System''',
                'console_message': '🔧 System health: {status} ({success_rate}% success rate)'
            }
        }
    
    def notify_processing_success(self, voice_file: VoiceFile, task: Optional[NotionTask] = None) -> Dict[str, bool]:
        """
        Send notifications when a file is successfully processed
        
        Args:
            voice_file: The processed voice file
            task: The created Notion task (optional)
            
        Returns:
            Dictionary with success status for each notification channel
        """
        # Prepare template variables
        short_transcript = self._truncate_text(voice_file.transcript or "", self.config.max_transcript_length)
        variables = {
            'file_id': voice_file.file_id,
            'transcript': voice_file.transcript or "No transcript",
            'short_transcript': short_transcript,
            'task_url': task.url if task else voice_file.task_url or "No URL",
            'processed_at': voice_file.processed_at.strftime('%Y-%m-%d %H:%M:%S') if voice_file.processed_at else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self._send_notification(
            'processing_success',
            variables,
            priority=NotificationPriority.NORMAL
        )
    
    def notify_processing_error(self, file_id: str, error_message: str) -> Dict[str, bool]:
        """
        Send notifications when processing fails
        
        Args:
            file_id: The file ID that failed
            error_message: The error message
            
        Returns:
            Dictionary with success status for each notification channel
        """
        variables = {
            'file_id': file_id,
            'error_message': error_message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self._send_notification(
            'processing_error',
            variables,
            priority=NotificationPriority.HIGH
        )
    
    def notify_daily_summary(self) -> Dict[str, bool]:
        """
        Send daily processing summary
        
        Returns:
            Dictionary with success status for each notification channel
        """
        stats = self.get_processing_stats()
        
        if stats['today_count'] == 0:
            # Don't send summary if no activity
            return {'skipped': True}
        
        # Format recent activity
        recent_activity = []
        for file in stats['recent_files'][:5]:
            timestamp = file.processed_at.strftime('%H:%M') if file.processed_at else 'Unknown'
            short_transcript = self._truncate_text(file.transcript or "", 50)
            recent_activity.append(f"  • {timestamp}: {short_transcript}")
        
        variables = {
            'today_count': stats['today_count'],
            'total_count': stats['total_count'],
            'count': stats['today_count'],  # For desktop message
            'recent_activity': '\n'.join(recent_activity) if recent_activity else "No recent activity"
        }
        
        return self._send_notification(
            'daily_summary',
            variables,
            priority=NotificationPriority.LOW
        )
    
    def notify_system_health(self, status: str, success_rate: float, issue_count: int, details: str) -> Dict[str, bool]:
        """
        Send system health notifications
        
        Args:
            status: System status (HEALTHY, WARNING, CRITICAL)
            success_rate: Current success rate percentage
            issue_count: Number of recent issues
            details: Detailed status information
            
        Returns:
            Dictionary with success status for each notification channel
        """
        priority = NotificationPriority.NORMAL
        if status == "CRITICAL":
            priority = NotificationPriority.CRITICAL
        elif status == "WARNING":
            priority = NotificationPriority.HIGH
        
        variables = {
            'status': status,
            'success_rate': success_rate,
            'issue_count': issue_count,
            'details': details
        }
        
        return self._send_notification(
            'system_health',
            variables,
            priority=priority
        )
    
    def _send_notification(self, template_name: str, variables: Dict[str, Any], 
                          priority: NotificationPriority = NotificationPriority.NORMAL) -> Dict[str, bool]:
        """
        Send notification using configured channels
        
        Args:
            template_name: Name of the template to use
            variables: Template variables
            priority: Notification priority
            
        Returns:
            Dictionary with success status for each channel
        """
        results = {}
        template = self.templates.get(template_name, {})
        
        # Desktop notification
        if NotificationChannel.DESKTOP in self.config.enabled_channels and self.config.desktop_enabled:
            results['desktop'] = self._send_desktop_notification(template, variables, priority)
        
        # Email notification
        if NotificationChannel.EMAIL in self.config.enabled_channels and self.config.email_enabled:
            results['email'] = self._send_email_notification(template, variables)
        
        # Console notification
        if NotificationChannel.CONSOLE in self.config.enabled_channels and self.config.console_enabled:
            results['console'] = self._send_console_notification(template, variables, priority)
        
        # Log notification
        if NotificationChannel.LOG in self.config.enabled_channels and self.config.log_enabled:
            results['log'] = self._send_log_notification(template, variables)
        
        # Record notification in history
        self.notification_history.append({
            'timestamp': datetime.now(),
            'template': template_name,
            'priority': priority.value,
            'results': results
        })
        
        return results
    
    def _send_desktop_notification(self, template: Dict[str, str], variables: Dict[str, Any], 
                                  priority: NotificationPriority) -> bool:
        """Send desktop notification using notify-send"""
        try:
            title = template.get('desktop_title', 'Voice Task Manager').format(**variables)
            message = template.get('desktop_message', 'Notification').format(**variables)
            
            # Truncate message for desktop display
            message = self._truncate_text(message, self.config.max_desktop_length)
            
            # Map priority to urgency
            urgency_map = {
                NotificationPriority.LOW: "low",
                NotificationPriority.NORMAL: "normal",
                NotificationPriority.HIGH: "normal", 
                NotificationPriority.CRITICAL: "critical"
            }
            urgency = urgency_map.get(priority, "normal")
            
            # Try full featured notify-send first
            subprocess.run([
                'notify-send', 
                '--urgency', urgency,
                '--icon', self.config.desktop_icon,
                '--app-name', self.config.app_name,
                title, 
                message
            ], check=True, capture_output=True)
            
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: try simpler notify-send
            try:
                title = template.get('desktop_title', 'Voice Task Manager').format(**variables)
                message = template.get('desktop_message', 'Notification').format(**variables)
                message = self._truncate_text(message, self.config.max_desktop_length)
                
                subprocess.run(['notify-send', title, message], check=True, capture_output=True)
                return True
            except:
                return False
    
    def _send_email_notification(self, template: Dict[str, str], variables: Dict[str, Any]) -> bool:
        """Send email notification"""
        if not EMAIL_AVAILABLE or not self.config.email_enabled:
            return False
        
        try:
            # Check required email configuration
            if not all([
                self.config.smtp_server,
                self.config.smtp_user, 
                self.config.smtp_pass,
                self.config.notification_email
            ]):
                return False
            
            subject = template.get('email_subject', 'Voice Task Manager Notification').format(**variables)
            body = template.get('email_body', 'Notification from Voice Task Manager').format(**variables)
            
            msg = MimeMultipart()
            msg['From'] = self.config.from_email or self.config.smtp_user
            msg['To'] = self.config.notification_email
            msg['Subject'] = subject
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.smtp_user, self.config.smtp_pass)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Email notification failed: {e}")
            return False
    
    def _send_console_notification(self, template: Dict[str, str], variables: Dict[str, Any],
                                  priority: NotificationPriority) -> bool:
        """Send console notification using Rich if available"""
        try:
            message = template.get('console_message', 'Notification').format(**variables)
            
            if self.console and HAS_RICH:
                # Use Rich for formatted output
                style_map = {
                    NotificationPriority.LOW: "dim",
                    NotificationPriority.NORMAL: "white",
                    NotificationPriority.HIGH: "yellow",
                    NotificationPriority.CRITICAL: "red bold"
                }
                style = style_map.get(priority, "white")
                
                if priority == NotificationPriority.CRITICAL:
                    # Use panel for critical notifications
                    panel = Panel(
                        Text(message, style=style),
                        title="Critical Alert",
                        border_style="red"
                    )
                    self.console.print(panel)
                else:
                    self.console.print(f"📢 {message}", style=style)
            else:
                # Fallback to simple print
                priority_prefix = {
                    NotificationPriority.LOW: "📢",
                    NotificationPriority.NORMAL: "📢",
                    NotificationPriority.HIGH: "⚠️ ",
                    NotificationPriority.CRITICAL: "🚨"
                }
                prefix = priority_prefix.get(priority, "📢")
                print(f"{prefix} {message}")
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Console notification failed: {e}")
            return False
    
    def _send_log_notification(self, template: Dict[str, str], variables: Dict[str, Any]) -> bool:
        """Send log notification"""
        try:
            message = template.get('console_message', 'Notification').format(**variables)
            self.logger.info(f"Notification: {message}")
            return True
        except Exception as e:
            self.logger.warning(f"Log notification failed: {e}")
            return False
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to maximum length with ellipsis"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics for notifications"""
        # Get database stats
        db_stats = self.database.get_processing_stats()
        
        # Get recent files
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_files = []
        
        try:
            all_files = self.database.get_all_voice_files(status='completed', limit=50)
            recent_files = [f for f in all_files if f.processed_at and f.processed_at >= recent_cutoff]
        except Exception:
            recent_files = []
        
        return {
            'total_count': db_stats['total_files'],
            'today_count': db_stats['today_processed'],
            'success_rate': db_stats['success_rate'],
            'recent_files': recent_files
        }
    
    def test_notifications(self) -> Dict[str, bool]:
        """Test all notification channels"""
        test_variables = {
            'file_id': 'test_file_123',
            'transcript': 'This is a test notification from the Voice Task Manager system.',
            'short_transcript': 'This is a test notification...',
            'task_url': 'https://notion.so/test-task',
            'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': 'Test error message',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self._send_notification(
            'processing_success',
            test_variables,
            priority=NotificationPriority.NORMAL
        )
    
    def get_notification_history(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Get recent notification history"""
        cutoff = datetime.now() - timedelta(hours=hours_back)
        return [n for n in self.notification_history if n['timestamp'] >= cutoff]
    
    def get_notification_status(self) -> str:
        """Get formatted notification system status"""
        enabled_channels = [ch.value for ch in self.config.enabled_channels]
        
        status_lines = [
            f"📢 Notification System Status",
            f"Enabled Channels: {', '.join(enabled_channels)}",
            f"Desktop: {'✅' if self.config.desktop_enabled else '❌'}",
            f"Email: {'✅' if self.config.email_enabled else '❌'} ({'Available' if EMAIL_AVAILABLE else 'Not Available'})",
            f"Console: {'✅' if self.config.console_enabled else '❌'}",
            f"Logging: {'✅' if self.config.log_enabled else '❌'}",
            f"Recent notifications: {len(self.get_notification_history())} in last 24h"
        ]
        
        if self.config.email_enabled:
            status_lines.extend([
                f"SMTP Server: {self.config.smtp_server or 'Not configured'}",
                f"Notification Email: {self.config.notification_email or 'Not configured'}"
            ])
        
        return '\n'.join(status_lines)

# Convenience functions for easy access
def get_notification_system(project_root: Optional[Path] = None) -> VoiceNotificationSystem:
    """Get a VoiceNotificationSystem instance"""
    return VoiceNotificationSystem(project_root)

def notify_success(voice_file: VoiceFile, task: Optional[NotionTask] = None) -> Dict[str, bool]:
    """Quick success notification"""
    system = get_notification_system()
    return system.notify_processing_success(voice_file, task)

def notify_error(file_id: str, error_message: str) -> Dict[str, bool]:
    """Quick error notification"""
    system = get_notification_system()
    return system.notify_processing_error(file_id, error_message)

def send_daily_summary() -> Dict[str, bool]:
    """Quick daily summary"""
    system = get_notification_system()
    return system.notify_daily_summary()

def test_notification_system() -> Dict[str, bool]:
    """Quick test of notification system"""
    system = get_notification_system()
    return system.test_notifications()