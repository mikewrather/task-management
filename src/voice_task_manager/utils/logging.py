"""
Voice Processing Logging System
Enhanced centralized logging utilities for the voice task management system.

Features:
- Structured console and file logging with color support
- JSON-formatted run summaries for analysis
- Log rotation and maintenance
- Error tracking and reporting
- Performance metrics collection
- SQLite deprecation warning fixes
- Rich console output integration

Log Files:
- voice-automation.log: Detailed processing logs with timestamps
- cron-run-history.log: JSON-formatted run summaries for analysis
- voice-errors.log: Dedicated error tracking

Usage:
    from voice_task_manager.utils.logging import VoiceLogger
    
    logger = VoiceLogger()
    logger.info("Processing started")
    logger.error("Failed to process file", file_id="abc123")
    logger.log_run_summary(files_found=5, files_processed=3, errors=1, duration=15.2)
"""

import json
import os
import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Union
import traceback

# Suppress SQLite deprecation warnings for Python 3.12+
warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlite3")

try:
    from rich.console import Console
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

class VoiceLogger:
    """Enhanced centralized logging system for voice processing automation"""
    
    def __init__(self, project_root: Optional[Union[str, Path]] = None):
        """
        Initialize the enhanced logging system
        
        Args:
            project_root: Root directory of the project (auto-detected if None)
        """
        if project_root is None:
            # Auto-detect project root from package location
            self.project_root = Path(__file__).parent.parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # Ensure logs directory exists
        self.log_dir = self.project_root / 'logs'
        self.log_dir.mkdir(exist_ok=True)
        
        # Define log file paths
        self.main_log = self.log_dir / 'voice-automation.log'
        self.run_history_log = self.log_dir / 'cron-run-history.log'
        self.error_log = self.log_dir / 'voice-errors.log'
        
        # Initialize rich console if available
        self.console = Console() if HAS_RICH else None
        
        # Initialize run context
        self.run_start_time = None
        self.current_run_data = {
            'files_found': 0,
            'files_processed': 0,
            'errors': 0,
            'warnings': 0
        }
    
    def start_run(self) -> None:
        """Mark the start of a processing run"""
        self.run_start_time = datetime.now()
        self.current_run_data = {
            'files_found': 0,
            'files_processed': 0,
            'errors': 0,
            'warnings': 0
        }
        self.info("🚀 Starting automated voice processing run")
    
    def _format_message(self, level: str, message: str, **kwargs) -> str:
        """Format a log message with timestamp and optional context"""
        timestamp = datetime.now().isoformat()
        
        # Add context data if provided
        context_str = ""
        if kwargs:
            context_parts = [f"{k}={v}" for k, v in kwargs.items()]
            context_str = f" [{', '.join(context_parts)}]"
        
        return f"[{timestamp}] {level}: {message}{context_str}"
    
    def _write_to_file(self, filepath: Path, content: str) -> None:
        """Write content to log file with error handling"""
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(content + '\n')
        except Exception as e:
            # Fallback to console if file writing fails
            fallback_msg = f"[LOGGING ERROR] Failed to write to {filepath}: {e}"
            if self.console:
                self.console.print(fallback_msg, style="red")
            else:
                print(fallback_msg)
    
    def _print_message(self, message: str, style: Optional[str] = None) -> None:
        """Print message to console with optional Rich styling"""
        if self.console and style:
            self.console.print(message, style=style)
        else:
            print(message)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message (only in development mode)"""
        if os.getenv('DEBUG', '').lower() in ('1', 'true', 'yes'):
            formatted = self._format_message("DEBUG", message, **kwargs)
            self._print_message(formatted, "dim")
            self._write_to_file(self.main_log, formatted)
    
    def info(self, message: str, **kwargs) -> None:
        """Log informational message"""
        formatted = self._format_message("INFO", message, **kwargs)
        self._print_message(formatted)
        self._write_to_file(self.main_log, formatted)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self.current_run_data['warnings'] += 1
        formatted = self._format_message("⚠️  WARN", message, **kwargs)
        self._print_message(formatted, "yellow")
        self._write_to_file(self.main_log, formatted)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """
        Log error message with optional exception details
        
        Args:
            message: Error description
            exception: Exception object (if available)
            **kwargs: Additional context (e.g., file_id, url, etc.)
        """
        self.current_run_data['errors'] += 1
        
        # Format main error message
        formatted = self._format_message("❌ ERROR", message, **kwargs)
        self._print_message(formatted, "red")
        self._write_to_file(self.main_log, formatted)
        
        # Log to dedicated error file with more detail
        error_detail = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'context': kwargs,
            'exception_type': type(exception).__name__ if exception else None,
            'exception_message': str(exception) if exception else None,
            'traceback': traceback.format_exc() if exception else None
        }
        
        self._write_to_file(self.error_log, json.dumps(error_detail))
    
    def success(self, message: str, **kwargs) -> None:
        """Log success message"""
        formatted = self._format_message("✅ SUCCESS", message, **kwargs)
        self._print_message(formatted, "green")
        self._write_to_file(self.main_log, formatted)
    
    def update_run_stats(self, files_found: Optional[int] = None, 
                        files_processed: Optional[int] = None) -> None:
        """Update current run statistics"""
        if files_found is not None:
            self.current_run_data['files_found'] = files_found
        if files_processed is not None:
            self.current_run_data['files_processed'] = files_processed
    
    def log_run_summary(self, files_found: Optional[int] = None, 
                       files_processed: Optional[int] = None, 
                       errors: Optional[int] = None, 
                       warnings: Optional[int] = None, 
                       additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Log a comprehensive run summary
        
        Args:
            files_found: Number of files discovered (uses tracked value if None)
            files_processed: Number of files successfully processed (uses tracked value if None)
            errors: Number of errors encountered (uses tracked value if None)
            warnings: Number of warnings encountered (uses tracked value if None)
            additional_data: Additional metrics to include
            
        Returns:
            Dictionary containing the complete run summary
        """
        if self.run_start_time is None:
            self.run_start_time = datetime.now()
        
        # Use provided values or fall back to tracked values
        final_files_found = files_found if files_found is not None else self.current_run_data['files_found']
        final_files_processed = files_processed if files_processed is not None else self.current_run_data['files_processed']
        final_errors = errors if errors is not None else self.current_run_data['errors']
        final_warnings = warnings if warnings is not None else self.current_run_data['warnings']
        
        # Calculate run duration
        duration_seconds = (datetime.now() - self.run_start_time).total_seconds()
        
        # Determine run status
        if final_errors > 0:
            status = 'failed' if final_files_processed == 0 else 'partial'
        else:
            status = 'success'
        
        # Build comprehensive summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'run_duration_seconds': round(duration_seconds, 2),
            'status': status,
            'files_found': final_files_found,
            'files_processed': final_files_processed,
            'processing_success_rate': round(final_files_processed / max(final_files_found, 1) * 100, 1),
            'errors': final_errors,
            'warnings': final_warnings,
            'system_health': self._calculate_system_health(status, final_errors, final_warnings)
        }
        
        # Add any additional data
        if additional_data:
            summary.update(additional_data)
        
        # Write JSON summary to run history log
        self._write_to_file(self.run_history_log, json.dumps(summary))
        
        # Log human-readable summary with rich styling
        status_emoji = {'success': '✅', 'partial': '⚠️ ', 'failed': '❌'}
        emoji = status_emoji.get(status, '❓')
        
        readable_summary = (
            f"{emoji} RUN SUMMARY: "
            f"Found={final_files_found}, Processed={final_files_processed}, "
            f"Errors={final_errors}, Warnings={final_warnings}, "
            f"Duration={duration_seconds:.1f}s, Success Rate={summary['processing_success_rate']:.1f}%"
        )
        
        # Color the summary based on status
        style = {
            'success': 'green',
            'partial': 'yellow', 
            'failed': 'red'
        }.get(status, None)
        
        self._print_message(readable_summary, style)
        self._write_to_file(self.main_log, self._format_message("SUMMARY", readable_summary))
        
        return summary
    
    def _calculate_system_health(self, status: str, errors: int, warnings: int) -> str:
        """Calculate overall system health indicator"""
        if status == 'success' and errors == 0 and warnings <= 1:
            return 'healthy'
        elif status in ['success', 'partial'] and errors <= 2:
            return 'warning'
        else:
            return 'critical'
    
    def get_log_files_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about log files"""
        info = {}
        
        for name, path in [
            ('main_log', self.main_log),
            ('run_history', self.run_history_log),
            ('error_log', self.error_log)
        ]:
            if path.exists():
                stat = path.stat()
                info[name] = {
                    'path': str(path),
                    'size_bytes': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'exists': True
                }
            else:
                info[name] = {
                    'path': str(path),
                    'exists': False
                }
        
        return info
    
    def rotate_logs(self, max_size_mb: float = 10.0, keep_backups: int = 5) -> None:
        """
        Rotate log files if they exceed size limit
        
        Args:
            max_size_mb: Maximum log file size in MB before rotation
            keep_backups: Number of backup files to keep
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        
        for log_file in [self.main_log, self.error_log]:
            if log_file.exists() and log_file.stat().st_size > max_size_bytes:
                self._rotate_single_log(log_file, keep_backups)
    
    def _rotate_single_log(self, log_file: Path, keep_backups: int) -> None:
        """Rotate a single log file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = log_file.with_name(f"{log_file.stem}_{timestamp}{log_file.suffix}")
        
        try:
            # Move current log to backup
            log_file.rename(backup_file)
            
            # Clean up old backups
            pattern = f"{log_file.stem}_*{log_file.suffix}"
            backup_files = sorted(log_file.parent.glob(pattern))
            
            if len(backup_files) > keep_backups:
                for old_backup in backup_files[:-keep_backups]:
                    old_backup.unlink()
            
            self.info(f"Rotated log file: {log_file.name} -> {backup_file.name}")
            
        except Exception as e:
            self.error(f"Failed to rotate log file {log_file}", exception=e)

# Convenience functions for easier import and usage
def get_logger(project_root: Optional[Union[str, Path]] = None) -> VoiceLogger:
    """Get a VoiceLogger instance"""
    return VoiceLogger(project_root)

# Legacy compatibility functions for migration period
def log(message: str) -> None:
    """Legacy compatibility function - creates temporary logger"""
    logger = get_logger()
    logger.info(message)

def log_run_summary(files_found: int, files_processed: int, errors: int, 
                   duration_seconds: float) -> Dict[str, Any]:
    """Legacy compatibility function - creates temporary logger"""
    logger = get_logger()
    return logger.log_run_summary(files_found, files_processed, errors, 0, 
                                 {'duration_seconds': duration_seconds})