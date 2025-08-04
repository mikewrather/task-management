"""
Voice Processing Daemon
Long-running service for continuous voice file processing
"""

import os
import signal
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from ..core.processor_v2 import VoiceProcessorV2
from ..utils.logging import VoiceLogger
from ..utils.notifications import VoiceNotificationSystem
from .session_manager import ClaudeSessionManager, AuthStatus


class SimpleNotifier:
    """Simple notification adapter for daemon"""
    
    def __init__(self, notification_system: 'VoiceNotificationSystem'):
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


class ServiceState(Enum):
    """Service states"""
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ServiceStats:
    """Service statistics"""
    start_time: datetime
    last_run: Optional[datetime] = None
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    files_processed: int = 0
    last_error: Optional[str] = None


class VoiceProcessingDaemon(threading.Thread):
    """
    Voice processing daemon that runs continuously
    
    Features:
    - Periodic voice file processing
    - Claude OAuth monitoring
    - Graceful shutdown
    - Health monitoring
    - Automatic fallback when OAuth expires
    """
    
    def __init__(
        self,
        interval_seconds: int = 300,  # 5 minutes default
        project_root: Optional[Path] = None,
        daemon: bool = True
    ):
        """
        Initialize the voice processing daemon
        
        Args:
            interval_seconds: Processing interval in seconds
            project_root: Project root directory
            daemon: Run as daemon thread
        """
        super().__init__(daemon=daemon)
        
        self.interval = interval_seconds
        self.project_root = project_root or Path(__file__).parent.parent.parent.parent
        
        # Core components
        self.logger = VoiceLogger()
        self.session_manager = ClaudeSessionManager(self.logger)
        self.processor = VoiceProcessorV2(self.project_root)
        self.notifier = SimpleNotifier(VoiceNotificationSystem())
        
        # Service state
        self.state = ServiceState.STOPPED
        self.stats = ServiceStats(start_time=datetime.now())
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
        # PID file for process management
        self.pid_file = self.project_root / "data" / "voice-daemon.pid"
        
    def run(self):
        """Main service loop"""
        self.state = ServiceState.STARTING
        self.logger.info("Voice processing daemon starting", 
                        interval=self.interval,
                        pid=os.getpid())
        
        try:
            # Write PID file
            self._write_pid_file()
            
            # Initial OAuth check
            session_info = self.session_manager.check_and_notify(force=True)
            self._log_session_status(session_info)
            
            # Send startup notification
            self.notifier.send_notification(
                title="Voice Processing Service Started",
                message=f"Processing every {self.interval//60} minutes"
            )
            
            self.state = ServiceState.RUNNING
            
            # Main processing loop
            while not self._stop_event.is_set():
                # Check if paused
                if self._pause_event.is_set():
                    self.state = ServiceState.PAUSED
                    time.sleep(1)
                    continue
                    
                self.state = ServiceState.RUNNING
                
                try:
                    # Run processing cycle
                    self._process_cycle()
                    
                except Exception as e:
                    self.logger.error("Processing cycle failed", exception=e)
                    self.stats.failed_runs += 1
                    self.stats.last_error = str(e)
                    
                # Wait for next cycle or stop signal
                self._stop_event.wait(self.interval)
                
        except Exception as e:
            self.logger.error("Fatal daemon error", exception=e)
            self.state = ServiceState.ERROR
            self.stats.last_error = str(e)
            
        finally:
            self._cleanup()
            
    def _process_cycle(self):
        """Run one processing cycle"""
        start_time = datetime.now()
        self.stats.total_runs += 1
        
        self.logger.info("Starting processing cycle", 
                        run_number=self.stats.total_runs)
        
        # Check OAuth status periodically (every 6th run ~ 30 minutes)
        if self.stats.total_runs % 6 == 0:
            session_info = self.session_manager.check_and_notify()
            self._log_session_status(session_info)
            
            # Adjust processor based on OAuth status
            if session_info.status in [AuthStatus.EXPIRED, AuthStatus.MISSING]:
                self.processor.use_claude_processor = False
                self.logger.warning("Disabling Claude processor due to auth issues")
            else:
                self.processor.use_claude_processor = True
                
        # Write health status
        self._write_health_status()
                
        # Run voice processing
        try:
            result = self.processor.run_automation()
            
            if result['success']:
                self.stats.successful_runs += 1
                self.stats.files_processed += result.get('processed', 0)
                
                # Log summary
                self.logger.info("Processing cycle completed",
                               files_processed=result.get('processed', 0),
                               total_found=result.get('total_found', 0),
                               duration=(datetime.now() - start_time).total_seconds())
                               
            else:
                self.stats.failed_runs += 1
                self.stats.last_error = result.get('error', 'Unknown error')
                
        except Exception as e:
            self.logger.error("Voice processing failed", exception=e)
            self.stats.failed_runs += 1
            self.stats.last_error = str(e)
            raise
            
        finally:
            self.stats.last_run = datetime.now()
            
    def _log_session_status(self, session_info):
        """Log Claude session status"""
        self.logger.info("Claude session status",
                        status=session_info.status.value,
                        expiry=session_info.expiry_estimate.isoformat() if session_info.expiry_estimate else None,
                        error=session_info.error)
                        
    def stop(self, timeout: Optional[float] = 30.0):
        """
        Stop the daemon gracefully
        
        Args:
            timeout: Maximum time to wait for shutdown
        """
        self.logger.info("Stopping voice processing daemon")
        self.state = ServiceState.STOPPING
        self._stop_event.set()
        
        if self.is_alive():
            self.join(timeout)
            
        if self.is_alive():
            self.logger.warning("Daemon did not stop cleanly within timeout")
            
    def pause(self):
        """Pause processing"""
        self.logger.info("Pausing voice processing")
        self._pause_event.set()
        
    def resume(self):
        """Resume processing"""
        self.logger.info("Resuming voice processing")
        self._pause_event.clear()
        
    def get_health(self) -> Dict[str, Any]:
        """
        Get service health information
        
        Returns:
            Dictionary with health status
        """
        now = datetime.now()
        uptime = now - self.stats.start_time
        
        # Determine health status
        if self.state == ServiceState.ERROR:
            health = "unhealthy"
        elif self.state != ServiceState.RUNNING:
            health = "degraded"
        elif self.stats.failed_runs > self.stats.successful_runs:
            health = "degraded"
        else:
            health = "healthy"
            
        # Get Claude status
        claude_status = "unknown"
        if hasattr(self, 'session_manager'):
            session_info = self.session_manager.get_session_info()
            claude_status = session_info.status.value
            
        return {
            "status": health,
            "state": self.state.value,
            "uptime_seconds": int(uptime.total_seconds()),
            "stats": {
                "total_runs": self.stats.total_runs,
                "successful_runs": self.stats.successful_runs,
                "failed_runs": self.stats.failed_runs,
                "files_processed": self.stats.files_processed,
                "last_run": self.stats.last_run.isoformat() if self.stats.last_run else None,
                "last_error": self.stats.last_error
            },
            "claude_status": claude_status,
            "config": {
                "interval_seconds": self.interval,
                "claude_enabled": self.processor.use_claude_processor
            }
        }
        
    def _write_pid_file(self):
        """Write PID file for process management"""
        self.pid_file.parent.mkdir(exist_ok=True)
        self.pid_file.write_text(str(os.getpid()))
        
    def _write_health_status(self):
        """Write health status to file for external monitoring"""
        try:
            health_file = self.project_root / "data" / "voice-daemon-health.json"
            health_data = self.get_health()
            health_data['timestamp'] = datetime.now().isoformat()
            
            import json
            health_file.write_text(json.dumps(health_data, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to write health status: {e}")
        
    def _cleanup(self):
        """Clean up resources on shutdown"""
        self.state = ServiceState.STOPPED
        
        # Remove PID file
        if self.pid_file.exists():
            self.pid_file.unlink()
            
        # Send shutdown notification
        self.notifier.send_notification(
            title="Voice Processing Service Stopped",
            message=f"Processed {self.stats.files_processed} files in {self.stats.total_runs} runs"
        )
        
        self.logger.info("Voice processing daemon stopped",
                        total_runs=self.stats.total_runs,
                        files_processed=self.stats.files_processed)