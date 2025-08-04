#!/usr/bin/env python3
"""
Voice Processing Service Entry Point
Manages the voice processing daemon with proper signal handling
"""

import sys
import os
import signal
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from voice_task_manager.services import VoiceProcessingDaemon
from voice_task_manager.utils.logging import VoiceLogger


class ServiceManager:
    """Manages the voice processing service lifecycle"""
    
    def __init__(self):
        self.logger = VoiceLogger()
        self.daemon = None
        self.pid_file = project_root / "data" / "voice-daemon.pid"
        
    def start(self, interval: int = 300, foreground: bool = False):
        """Start the service"""
        # Check if already running
        if self._is_running():
            print("Service is already running")
            return 1
            
        print(f"Starting voice processing service (interval: {interval}s)")
        
        # Create and start daemon
        self.daemon = VoiceProcessingDaemon(
            interval_seconds=interval,
            project_root=project_root,
            daemon=not foreground
        )
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Start the daemon
        self.daemon.start()
        
        if foreground:
            # Run in foreground (for systemd)
            try:
                self.daemon.join()
            except KeyboardInterrupt:
                self.logger.info("Received keyboard interrupt")
                self.stop()
        else:
            print(f"Service started with PID: {os.getpid()}")
            
        return 0
        
    def stop(self):
        """Stop the service"""
        if not self._is_running():
            print("Service is not running")
            return 1
            
        pid = self._get_pid()
        if pid:
            print(f"Stopping service (PID: {pid})")
            try:
                os.kill(pid, signal.SIGTERM)
                print("Service stopped")
                return 0
            except ProcessLookupError:
                print("Service process not found")
                # Clean up stale PID file
                if self.pid_file.exists():
                    self.pid_file.unlink()
                return 1
        else:
            if self.daemon:
                self.daemon.stop()
                print("Service stopped")
                return 0
                
        return 1
        
    def restart(self, interval: int = 300):
        """Restart the service"""
        print("Restarting service...")
        self.stop()
        return self.start(interval)
        
    def status(self):
        """Check service status"""
        if not self._is_running():
            print("Service is not running")
            return 1
            
        pid = self._get_pid()
        print(f"Service is running (PID: {pid})")
        
        # Try to get health status
        health_file = project_root / "data" / "voice-daemon-health.json"
        if health_file.exists():
            try:
                with open(health_file) as f:
                    health = json.load(f)
                    
                print(f"\nHealth Status: {health['status']}")
                print(f"State: {health['state']}")
                print(f"Uptime: {health['uptime_seconds']}s")
                print(f"Total Runs: {health['stats']['total_runs']}")
                print(f"Files Processed: {health['stats']['files_processed']}")
                print(f"Claude Status: {health['claude_status']}")
                
            except Exception as e:
                self.logger.error(f"Failed to read health status: {e}")
                
        return 0
        
    def health(self):
        """Get detailed health information"""
        if not self._is_running():
            health = {
                "status": "stopped",
                "timestamp": datetime.now().isoformat(),
                "error": "Service is not running"
            }
        else:
            # Read health from daemon (would need IPC in production)
            health_file = project_root / "data" / "voice-daemon-health.json"
            if health_file.exists():
                try:
                    with open(health_file) as f:
                        health = json.load(f)
                except Exception:
                    health = {"status": "unknown", "error": "Failed to read health"}
            else:
                health = {"status": "running", "pid": self._get_pid()}
                
        print(json.dumps(health, indent=2))
        return 0
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}")
        if self.daemon:
            self.daemon.stop()
            
    def _is_running(self) -> bool:
        """Check if service is running"""
        pid = self._get_pid()
        if pid:
            try:
                # Check if process exists
                os.kill(pid, 0)
                return True
            except ProcessLookupError:
                # Clean up stale PID file
                if self.pid_file.exists():
                    self.pid_file.unlink()
                return False
        return False
        
    def _get_pid(self) -> int:
        """Get service PID from file"""
        if self.pid_file.exists():
            try:
                return int(self.pid_file.read_text().strip())
            except Exception:
                return None
        return None


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Voice Processing Service Manager"
    )
    
    parser.add_argument(
        'command',
        choices=['start', 'stop', 'restart', 'status', 'health'],
        help='Service command'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Processing interval in seconds (default: 300)'
    )
    
    parser.add_argument(
        '--foreground',
        action='store_true',
        help='Run in foreground (for systemd)'
    )
    
    args = parser.parse_args()
    
    manager = ServiceManager()
    
    if args.command == 'start':
        return manager.start(args.interval, args.foreground)
    elif args.command == 'stop':
        return manager.stop()
    elif args.command == 'restart':
        return manager.restart(args.interval)
    elif args.command == 'status':
        return manager.status()
    elif args.command == 'health':
        return manager.health()
        

if __name__ == '__main__':
    sys.exit(main())