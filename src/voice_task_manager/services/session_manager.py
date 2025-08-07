"""
Claude Session Manager
Monitors and manages Claude OAuth authentication state
"""

import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ..utils.logging import VoiceLogger
from ..utils.notifications import VoiceNotificationSystem


class SimpleNotifier:
    """Simple notification adapter"""
    
    def __init__(self, notification_system: VoiceNotificationSystem):
        self.system = notification_system
    
    def send_notification(self, title: str, message: str, priority: str = "normal"):
        """Send a desktop notification"""
        try:
            # Use the desktop notification method with a simple template
            template = {"title": title, "body": message}
            variables = {}
            return self.system._send_desktop_notification(template, variables, priority)
        except Exception:
            # Fallback to console output
            print(f"[{title}] {message}")
            return True


class AuthStatus(Enum):
    """Authentication status levels"""
    VALID = "valid"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    MISSING = "missing"
    UNKNOWN = "unknown"


@dataclass
class SessionInfo:
    """Claude session information"""
    status: AuthStatus
    last_check: datetime
    last_successful_use: Optional[datetime] = None
    expiry_estimate: Optional[datetime] = None
    credentials_path: Optional[Path] = None
    error: Optional[str] = None


class ClaudeSessionManager:
    """
    Manages Claude OAuth session lifecycle
    
    Features:
    - Monitor OAuth token validity
    - Track successful Claude executions
    - Alert when re-authentication needed
    - Provide fallback recommendations
    """
    
    def __init__(self, logger: Optional[VoiceLogger] = None):
        """Initialize session manager"""
        self.logger = logger or VoiceLogger()
        self.notifier = SimpleNotifier(VoiceNotificationSystem())
        
        # Claude credentials location
        self.credentials_path = Path.home() / ".claude" / ".credentials.json"
        
        # Session tracking
        self.last_check: Optional[datetime] = None
        self.last_successful_use: Optional[datetime] = None
        self.check_interval = timedelta(minutes=30)
        
        # OAuth typically expires in 30-90 days
        self.expiry_warning_days = 7
        self.estimated_token_lifetime = timedelta(days=30)
        
    def get_session_info(self) -> SessionInfo:
        """
        Get current session information
        
        Returns:
            SessionInfo with current authentication status
        """
        now = datetime.now()
        
        # Check if credentials file exists
        if not self.credentials_path.exists():
            return SessionInfo(
                status=AuthStatus.MISSING,
                last_check=now,
                error="Claude credentials file not found"
            )
            
        try:
            # Read credentials file
            with open(self.credentials_path, 'r') as f:
                credentials = json.load(f)
                
            # Check if OAuth data exists
            if 'claudeAiOauth' not in credentials:
                return SessionInfo(
                    status=AuthStatus.MISSING,
                    last_check=now,
                    credentials_path=self.credentials_path,
                    error="OAuth data not found in credentials"
                )
                
            # Get file modification time as proxy for last auth
            auth_time = datetime.fromtimestamp(self.credentials_path.stat().st_mtime)
            
            # Estimate expiry based on typical OAuth lifetime
            expiry_estimate = auth_time + self.estimated_token_lifetime
            
            # Determine status
            if now > expiry_estimate:
                status = AuthStatus.EXPIRED
            elif now > expiry_estimate - timedelta(days=self.expiry_warning_days):
                status = AuthStatus.EXPIRING_SOON
            else:
                status = AuthStatus.VALID
                
            return SessionInfo(
                status=status,
                last_check=now,
                last_successful_use=self.last_successful_use,
                expiry_estimate=expiry_estimate,
                credentials_path=self.credentials_path
            )
            
        except Exception as e:
            self.logger.error(f"Failed to read Claude credentials: {e}")
            return SessionInfo(
                status=AuthStatus.UNKNOWN,
                last_check=now,
                error=str(e)
            )
            
    def test_claude_execution(self) -> Tuple[bool, Optional[str]]:
        """
        Test if Claude can be executed successfully
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Simple test command
            claude_path = "/home/mike/.claude/local/claude"
            cmd = [
                claude_path,
                "-p", "Return only: OK",
                "--dangerously-skip-permissions",
                "--output-format", "json"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, "HOME": str(Path.home())}
            )
            
            if result.returncode == 0:
                self.last_successful_use = datetime.now()
                return True, None
            else:
                error = result.stderr or result.stdout or "Unknown error"
                return False, error
                
        except subprocess.TimeoutExpired:
            return False, "Claude execution timed out"
        except Exception as e:
            return False, str(e)
            
    def check_and_notify(self, force: bool = False) -> SessionInfo:
        """
        Check session status and notify if action needed
        
        Args:
            force: Force check even if recently checked
            
        Returns:
            Current session information
        """
        now = datetime.now()
        
        # Skip if recently checked (unless forced)
        if not force and self.last_check:
            if now - self.last_check < self.check_interval:
                return self.get_session_info()
                
        # Get current status
        info = self.get_session_info()
        self.last_check = now
        
        # Test actual execution
        success, error = self.test_claude_execution()
        
        if not success:
            # Override status if execution fails
            info.status = AuthStatus.EXPIRED
            info.error = error
            
        # Send notifications based on status
        if info.status == AuthStatus.EXPIRED:
            self._notify_expired(info)
        elif info.status == AuthStatus.EXPIRING_SOON:
            self._notify_expiring(info)
        elif info.status == AuthStatus.MISSING:
            self._notify_missing(info)
            
        return info
        
    def _notify_expired(self, info: SessionInfo):
        """Send notification for expired session"""
        message = (
            "⚠️ Claude OAuth session has expired!\n\n"
            "Voice processing will fall back to simple parsing.\n"
            "To restore AI categorization:\n"
            "1. Run: claude login\n"
            "2. Complete browser authentication\n"
            "3. Restart the voice processing service"
        )
        
        self.notifier.send_notification(
            title="Claude Authentication Expired",
            message=message,
            priority="critical"
        )
        
        self.logger.warning("Claude OAuth expired", session_info=info.__dict__)
        
    def _notify_expiring(self, info: SessionInfo):
        """Send notification for expiring session"""
        days_left = (info.expiry_estimate - datetime.now()).days if info.expiry_estimate else 0
        
        message = (
            f"⏰ Claude OAuth expires in ~{days_left} days\n\n"
            "Consider re-authenticating soon to avoid interruption:\n"
            "Run: claude login"
        )
        
        self.notifier.send_notification(
            title="Claude Authentication Expiring",
            message=message,
            priority="normal"
        )
        
        self.logger.info("Claude OAuth expiring soon", days_left=days_left)
        
    def _notify_missing(self, info: SessionInfo):
        """Send notification for missing credentials"""
        message = (
            "🔐 Claude not authenticated\n\n"
            "To enable AI task categorization:\n"
            "1. Run: claude login\n"
            "2. Complete browser authentication"
        )
        
        self.notifier.send_notification(
            title="Claude Authentication Required",
            message=message,
            priority="normal"
        )
        
        self.logger.warning("Claude credentials missing")
        
    def can_use_claude(self) -> bool:
        """
        Quick check if Claude is likely usable
        
        Returns:
            True if Claude should be attempted, False otherwise
        """
        info = self.get_session_info()
        return info.status in [AuthStatus.VALID, AuthStatus.EXPIRING_SOON]