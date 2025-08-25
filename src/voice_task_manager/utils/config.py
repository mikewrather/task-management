"""
Configuration Management for Voice Task Manager
Enhanced configuration management and system integration utilities.

This module provides:
- System status monitoring and health checks
- Environment configuration validation
- Cron job management and setup
- Service dependency checking
- Configuration migration and setup utilities
"""

import os
import subprocess
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from ..utils.logging import VoiceLogger
from ..utils.database import VoiceDatabase

def get_claude_path() -> str:
    """
    Get the Claude CLI executable path.
    
    First checks CLAUDE_CLI_PATH environment variable, then tries common locations.
    
    Returns:
        str: Path to Claude CLI executable
        
    Raises:
        FileNotFoundError: If Claude CLI cannot be found
    """
    # Check environment variable first
    if claude_path := os.getenv("CLAUDE_CLI_PATH"):
        if Path(claude_path).exists():
            return claude_path
        # Log warning but continue to check other paths
        print(f"Warning: CLAUDE_CLI_PATH set to '{claude_path}' but file doesn't exist")
    
    # Try common installation locations
    paths_to_try = [
        "/home/mike/.claude/local/claude",  # Current working location
        "/home/mike/.nvm/versions/node/v24.2.0/bin/claude",  # Old NVM location
        Path.home() / ".claude" / "local" / "claude",  # User's local installation
        Path.home() / ".local" / "bin" / "claude",  # Alternative local bin
    ]
    
    for path in paths_to_try:
        path = Path(path)
        if path.exists() and path.is_file():
            return str(path)
    
    # If nothing found, raise informative error
    raise FileNotFoundError(
        "Claude CLI not found. Please either:\n"
        "1. Set CLAUDE_CLI_PATH environment variable to the Claude executable path\n"
        "2. Install Claude CLI to one of the standard locations:\n"
        f"   - {paths_to_try[0]}\n"
        f"   - {Path.home() / '.claude' / 'local' / 'claude'}"
    )

class ServiceStatus(Enum):
    """Service status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"  
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class SystemComponent:
    """Represents a system component with status"""
    name: str
    status: ServiceStatus
    message: str
    details: Optional[str] = None
    last_check: Optional[datetime] = None

class SystemStatus:
    """System status monitoring and health checks"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize system status checker
        
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
        
        # Key file paths
        self.log_file = self.project_root / 'logs' / 'cron-voice.log'
        self.run_history_log = self.project_root / 'logs' / 'cron-run-history.log'
        self.env_file = self.project_root / '.env'
        self.venv_dir = self.project_root / 'venv'
        self.data_dir = self.project_root / 'data'
        
    def get_system_status(self, detailed: bool = False, json_format: bool = False) -> str:
        """
        Get comprehensive system status
        
        Args:
            detailed: Include detailed information
            json_format: Return as JSON string
            
        Returns:
            Formatted system status report
        """
        components = self._check_all_components(detailed)
        
        if json_format:
            return self._format_json_status(components, detailed)
        else:
            return self._format_text_status(components, detailed)
    
    def _check_all_components(self, detailed: bool = False) -> List[SystemComponent]:
        """Check status of all system components"""
        components = []
        
        # Cron job status
        components.append(self._check_cron_status())
        
        # Environment configuration
        components.append(self._check_environment())
        
        # Virtual environment
        components.append(self._check_virtual_environment())
        
        # Database status
        components.append(self._check_database())
        
        # Recent activity
        components.append(self._check_recent_activity())
        
        # Log files
        components.append(self._check_log_files())
        
        if detailed:
            # API connectivity (if keys are available)
            components.extend(self._check_api_connectivity())
            
            # File system permissions
            components.append(self._check_file_permissions())
            
            # System resources
            components.append(self._check_system_resources())
        
        return components
    
    def _check_cron_status(self) -> SystemComponent:
        """Check cron job status"""
        try:
            # Check if cron job exists
            result = subprocess.run(
                ['crontab', '-l'], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                crontab_content = result.stdout
                if 'voice-cron-wrapper' in crontab_content or 'vtm-cron-wrapper' in crontab_content or 'vtm process' in crontab_content:
                    # Extract the cron line for analysis
                    cron_lines = [line for line in crontab_content.split('\n') 
                                 if 'voice-cron-wrapper' in line or 'vtm-cron-wrapper' in line or 'vtm process' in line]
                    
                    if cron_lines:
                        # Calculate next run time (approximate)
                        next_run = self._calculate_next_cron_run(cron_lines[0])
                        message = f"Active (runs every 5 minutes)"
                        details = f"Next run: ~{next_run}" if next_run else "Schedule detected"
                        return SystemComponent(
                            name="Cron Job", 
                            status=ServiceStatus.HEALTHY,
                            message=message,
                            details=details
                        )
                else:
                    return SystemComponent(
                        name="Cron Job",
                        status=ServiceStatus.CRITICAL,
                        message="Cron job not found",
                        details="Use 'vtm setup --cron' to install"
                    )
            else:
                return SystemComponent(
                    name="Cron Job",
                    status=ServiceStatus.WARNING,
                    message="Cannot check crontab",
                    details="Permission issue or cron not available"
                )
                
        except FileNotFoundError:
            return SystemComponent(
                name="Cron Job",
                status=ServiceStatus.CRITICAL,
                message="Cron service not available",
                details="Install cron service"
            )
        except Exception as e:
            return SystemComponent(
                name="Cron Job",
                status=ServiceStatus.UNKNOWN,
                message="Check failed",
                details=str(e)
            )
    
    def _check_environment(self) -> SystemComponent:
        """Check environment configuration"""
        if not self.env_file.exists():
            return SystemComponent(
                name="Environment",
                status=ServiceStatus.CRITICAL,
                message=".env file missing",
                details="Create .env file with API keys"
            )
        
        # Check for required environment variables
        required_vars = [
            'OPENAI_API_KEY',
            'NOTION_TOKEN', 
            'GOOGLE_DRIVE_FOLDER_ID'
        ]
        
        missing_vars = []
        try:
            # Load .env file manually to check contents
            with open(self.env_file) as f:
                env_content = f.read()
                
            for var in required_vars:
                if f"{var}=" not in env_content or f"{var}=" in env_content and not env_content.split(f"{var}=")[1].split('\n')[0].strip():
                    missing_vars.append(var)
            
            if missing_vars:
                return SystemComponent(
                    name="Environment",
                    status=ServiceStatus.WARNING,
                    message=f"{len(missing_vars)} required variables missing",
                    details=f"Missing: {', '.join(missing_vars)}"
                )
            else:
                return SystemComponent(
                    name="Environment",
                    status=ServiceStatus.HEALTHY,
                    message="All required variables present",
                    details=f"Found {len(required_vars)} required variables"
                )
                
        except Exception as e:
            return SystemComponent(
                name="Environment",
                status=ServiceStatus.WARNING,
                message="Cannot validate .env file",
                details=str(e)
            )
    
    def _check_virtual_environment(self) -> SystemComponent:
        """Check virtual environment status"""
        if not self.venv_dir.exists():
            return SystemComponent(
                name="Virtual Environment",
                status=ServiceStatus.CRITICAL,
                message="Virtual environment missing",
                details="Run 'python -m venv venv' to create"
            )
        
        # Check if activate script exists
        activate_script = self.venv_dir / 'bin' / 'activate'
        if not activate_script.exists():
            return SystemComponent(
                name="Virtual Environment",
                status=ServiceStatus.WARNING,
                message="Virtual environment incomplete",
                details="Missing activation script"
            )
        
        # Check if key dependencies are installed
        try:
            python_path = self.venv_dir / 'bin' / 'python'
            if python_path.exists():
                # Try to import key packages
                result = subprocess.run([
                    str(python_path), '-c', 
                    'import openai, requests, click, rich; print("OK")'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    return SystemComponent(
                        name="Virtual Environment",
                        status=ServiceStatus.HEALTHY,
                        message="Ready with dependencies",
                        details="All key packages available"
                    )
                else:
                    return SystemComponent(
                        name="Virtual Environment",
                        status=ServiceStatus.WARNING,
                        message="Missing dependencies",
                        details="Run 'pip install -r requirements.txt'"
                    )
            else:
                return SystemComponent(
                    name="Virtual Environment",
                    status=ServiceStatus.WARNING,
                    message="Python interpreter not found",
                    details="Virtual environment may be corrupted"
                )
                
        except Exception as e:
            return SystemComponent(
                name="Virtual Environment",
                status=ServiceStatus.UNKNOWN,
                message="Cannot check dependencies",
                details=str(e)
            )
    
    def _check_database(self) -> SystemComponent:
        """Check database status and integrity"""
        try:
            stats = self.database.get_processing_stats()
            
            # Check for data integrity issues
            if stats['total_files'] < 0:
                return SystemComponent(
                    name="Database",
                    status=ServiceStatus.CRITICAL,
                    message="Data corruption detected",
                    details="Database contains invalid data"
                )
            
            # Check for recent processing
            if stats['today_processed'] > 0:
                status = ServiceStatus.HEALTHY
                message = f"Active ({stats['total_files']} total files)"
                details = f"{stats['today_processed']} processed today, {stats['success_rate']:.1f}% success rate"
            elif stats['total_files'] > 0:
                status = ServiceStatus.WARNING
                message = f"No recent activity ({stats['total_files']} total files)"
                details = f"Last processing: check logs for details"
            else:
                status = ServiceStatus.WARNING
                message = "No data - system hasn't processed files yet"
                details = "Database is empty but functional"
            
            return SystemComponent(
                name="Database",
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return SystemComponent(
                name="Database",
                status=ServiceStatus.CRITICAL,
                message="Database access failed",
                details=str(e)
            )
    
    def _check_recent_activity(self) -> SystemComponent:
        """Check recent processing activity from logs"""
        try:
            if not self.log_file.exists():
                return SystemComponent(
                    name="Recent Activity",
                    status=ServiceStatus.WARNING,
                    message="No log file found",
                    details="System may not have run yet"
                )
            
            # Read last few log entries
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            
            if not lines:
                return SystemComponent(
                    name="Recent Activity",
                    status=ServiceStatus.WARNING,
                    message="Log file is empty",
                    details="No recorded activity"
                )
            
            # Find most recent activity
            recent_lines = lines[-50:]  # Last 50 lines
            processing_lines = [line for line in recent_lines if 'Starting automated' in line or 'processed' in line]
            
            if processing_lines:
                latest_line = processing_lines[-1]
                # Extract timestamp if available
                if '[' in latest_line and ']' in latest_line:
                    timestamp_str = latest_line.split('[')[1].split(']')[0]
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        age = datetime.now() - timestamp
                        
                        if age.total_seconds() < 600:  # Less than 10 minutes
                            status = ServiceStatus.HEALTHY
                            message = "Active processing"
                        elif age.total_seconds() < 3600:  # Less than 1 hour
                            status = ServiceStatus.WARNING
                            message = "Recent activity"
                        else:
                            status = ServiceStatus.WARNING
                            message = "Stale activity"
                        
                        details = f"Last activity: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({int(age.total_seconds()/60)} minutes ago)"
                        
                    except (ValueError, IndexError):
                        status = ServiceStatus.UNKNOWN
                        message = "Cannot parse log timestamps"
                        details = "Log format may have changed"
                else:
                    status = ServiceStatus.UNKNOWN
                    message = "Recent activity detected"
                    details = "Cannot parse timestamp"
            else:
                status = ServiceStatus.WARNING
                message = "No processing activity found"
                details = "Logs exist but no processing records found"
            
            return SystemComponent(
                name="Recent Activity",
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return SystemComponent(
                name="Recent Activity",
                status=ServiceStatus.UNKNOWN,
                message="Cannot read log files",
                details=str(e)
            )
    
    def _check_log_files(self) -> SystemComponent:
        """Check log file status and disk usage"""
        try:
            log_dir = self.project_root / 'logs'
            if not log_dir.exists():
                return SystemComponent(
                    name="Log Files",
                    status=ServiceStatus.WARNING,
                    message="Log directory missing",
                    details="Will be created on first run"
                )
            
            # Check log file sizes
            log_files = list(log_dir.glob('*.log'))
            if not log_files:
                return SystemComponent(
                    name="Log Files",
                    status=ServiceStatus.WARNING,
                    message="No log files found",
                    details="System may not have run yet"
                )
            
            total_size = sum(f.stat().st_size for f in log_files)
            total_size_mb = total_size / (1024 * 1024)
            
            if total_size_mb > 100:  # More than 100MB
                status = ServiceStatus.WARNING
                message = f"Large log files ({total_size_mb:.1f}MB)"
                details = "Consider log rotation"
            elif total_size_mb > 10:  # More than 10MB
                status = ServiceStatus.HEALTHY
                message = f"Normal log size ({total_size_mb:.1f}MB)"
                details = f"{len(log_files)} log files"
            else:
                status = ServiceStatus.HEALTHY
                message = f"Minimal logs ({total_size_mb:.1f}MB)"
                details = f"{len(log_files)} log files"
            
            return SystemComponent(
                name="Log Files",
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return SystemComponent(
                name="Log Files",
                status=ServiceStatus.UNKNOWN,
                message="Cannot check log files",
                details=str(e)
            )
    
    def _check_api_connectivity(self) -> List[SystemComponent]:
        """Check API connectivity (detailed mode only)"""
        components = []
        
        # OpenAI API check
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            try:
                import openai
                client = openai.OpenAI(api_key=openai_key)
                # Test with a minimal request
                response = client.models.list()
                components.append(SystemComponent(
                    name="OpenAI API",
                    status=ServiceStatus.HEALTHY,
                    message="Connected",
                    details="API key valid"
                ))
            except Exception as e:
                components.append(SystemComponent(
                    name="OpenAI API",
                    status=ServiceStatus.CRITICAL,
                    message="Connection failed",
                    details=str(e)
                ))
        else:
            components.append(SystemComponent(
                name="OpenAI API",
                status=ServiceStatus.WARNING,
                message="No API key configured",
                details="Set OPENAI_API_KEY in .env"
            ))
        
        # Notion API check
        notion_key = os.getenv('NOTION_TOKEN')
        if notion_key:
            try:
                import requests
                headers = {
                    'Authorization': f'Bearer {notion_key}',
                    'Notion-Version': '2022-06-28'
                }
                response = requests.get('https://api.notion.com/v1/users/me', headers=headers, timeout=10)
                if response.status_code == 200:
                    components.append(SystemComponent(
                        name="Notion API",
                        status=ServiceStatus.HEALTHY,
                        message="Connected",
                        details="API key valid"
                    ))
                else:
                    components.append(SystemComponent(
                        name="Notion API",
                        status=ServiceStatus.CRITICAL,
                        message=f"API error ({response.status_code})",
                        details="Invalid API key or permissions"
                    ))
            except Exception as e:
                components.append(SystemComponent(
                    name="Notion API",
                    status=ServiceStatus.CRITICAL,
                    message="Connection failed",
                    details=str(e)
                ))
        else:
            components.append(SystemComponent(
                name="Notion API",
                status=ServiceStatus.WARNING,
                message="No API key configured",
                details="Set NOTION_TOKEN in .env"
            ))
        
        return components
    
    def _check_file_permissions(self) -> SystemComponent:
        """Check file system permissions"""
        try:
            # Check write permissions for key directories
            test_dirs = [
                self.project_root / 'logs',
                self.project_root / 'data'
            ]
            
            permission_issues = []
            for test_dir in test_dirs:
                if test_dir.exists():
                    # Try to write a test file
                    test_file = test_dir / '.permission_test'
                    try:
                        test_file.write_text('test')
                        test_file.unlink()  # Clean up
                    except PermissionError:
                        permission_issues.append(str(test_dir))
                        
            if permission_issues:
                return SystemComponent(
                    name="File Permissions",
                    status=ServiceStatus.CRITICAL,
                    message="Permission denied",
                    details=f"Cannot write to: {', '.join(permission_issues)}"
                )
            else:
                return SystemComponent(
                    name="File Permissions",
                    status=ServiceStatus.HEALTHY,
                    message="All permissions OK",
                    details="Can write to logs and data directories"
                )
                
        except Exception as e:
            return SystemComponent(
                name="File Permissions",
                status=ServiceStatus.UNKNOWN,
                message="Permission check failed",
                details=str(e)
            )
    
    def _check_system_resources(self) -> SystemComponent:
        """Check system resource usage"""
        try:
            import shutil
            
            # Check disk space
            total, used, free = shutil.disk_usage(self.project_root)
            free_gb = free / (1024**3)
            
            if free_gb < 0.1:  # Less than 100MB
                status = ServiceStatus.CRITICAL
                message = f"Very low disk space ({free_gb:.1f}GB free)"
            elif free_gb < 1:  # Less than 1GB
                status = ServiceStatus.WARNING
                message = f"Low disk space ({free_gb:.1f}GB free)"
            else:
                status = ServiceStatus.HEALTHY
                message = f"Sufficient disk space ({free_gb:.1f}GB free)"
            
            return SystemComponent(
                name="System Resources",
                status=status,
                message=message,
                details=f"Total: {total/(1024**3):.1f}GB, Used: {used/(1024**3):.1f}GB"
            )
            
        except Exception as e:
            return SystemComponent(
                name="System Resources",
                status=ServiceStatus.UNKNOWN,
                message="Resource check failed",
                details=str(e)
            )
    
    def _calculate_next_cron_run(self, cron_line: str) -> Optional[str]:
        """Calculate approximate next cron run time"""
        try:
            # Simple calculation for */5 * * * * pattern
            if '*/5' in cron_line:
                now = datetime.now()
                current_minute = now.minute
                next_minute = ((current_minute // 5) + 1) * 5
                if next_minute >= 60:
                    next_hour = now.hour + 1
                    next_minute = 0
                else:
                    next_hour = now.hour
                
                return f"{next_hour:02d}:{next_minute:02d}"
        except:
            pass
        return None
    
    def _format_text_status(self, components: List[SystemComponent], detailed: bool) -> str:
        """Format status as text output"""
        if self.console and HAS_RICH:
            return self._format_rich_status(components, detailed)
        else:
            return self._format_plain_status(components, detailed)
    
    def _format_rich_status(self, components: List[SystemComponent], detailed: bool) -> str:
        """Format status with Rich formatting"""
        from io import StringIO
        output = StringIO()
        
        # Create a string buffer to capture Rich output
        temp_console = Console(file=output, width=80)
        
        # Header
        temp_console.print("🎤 Voice Task Manager System Status", style="bold blue")
        temp_console.print(f"Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
        temp_console.print()
        
        # Status table
        table = Table(title="System Components", show_header=True, header_style="bold cyan")
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Status", width=12)
        table.add_column("Message", width=30)
        
        if detailed:
            table.add_column("Details", style="dim", width=25)
        
        for component in components:
            # Status styling
            if component.status == ServiceStatus.HEALTHY:
                status_text = "✅ Healthy"
                status_style = "green"
            elif component.status == ServiceStatus.WARNING:
                status_text = "⚠️  Warning"
                status_style = "yellow"
            elif component.status == ServiceStatus.CRITICAL:
                status_text = "❌ Critical"
                status_style = "red"
            else:
                status_text = "❓ Unknown"
                status_style = "dim"
            
            row = [
                component.name,
                Text(status_text, style=status_style),
                component.message
            ]
            
            if detailed and component.details:
                row.append(component.details)
            elif detailed:
                row.append("-")
            
            table.add_row(*row)
        
        temp_console.print(table)
        temp_console.print()
        
        # Overall health summary
        healthy_count = sum(1 for c in components if c.status == ServiceStatus.HEALTHY)
        warning_count = sum(1 for c in components if c.status == ServiceStatus.WARNING)
        critical_count = sum(1 for c in components if c.status == ServiceStatus.CRITICAL)
        
        if critical_count > 0:
            overall_status = "🔴 CRITICAL"
            overall_style = "red bold"
        elif warning_count > 0:
            overall_status = "🟡 WARNING"
            overall_style = "yellow bold"
        else:
            overall_status = "🟢 HEALTHY"
            overall_style = "green bold"
        
        temp_console.print(f"Overall Status: {Text(overall_status, style=overall_style)}")
        temp_console.print(f"Components: {healthy_count} healthy, {warning_count} warnings, {critical_count} critical")
        
        # Quick commands
        temp_console.print()
        temp_console.print("🛠️  Quick Commands:", style="bold")
        temp_console.print("   📝 View logs:     tail -f logs/cron-voice.log")
        temp_console.print("   🧪 Test manually: vtm process --dry-run")
        temp_console.print("   📊 View stats:    vtm analyze --stats")
        temp_console.print("   🔧 Setup cron:    vtm setup --cron")
        
        return output.getvalue()
    
    def _format_plain_status(self, components: List[SystemComponent], detailed: bool) -> str:
        """Format status as plain text"""
        lines = []
        lines.append("🎤 Voice Task Manager System Status")
        lines.append("=" * 50)
        lines.append(f"Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        for component in components:
            if component.status == ServiceStatus.HEALTHY:
                status_icon = "✅"
            elif component.status == ServiceStatus.WARNING:
                status_icon = "⚠️ "
            elif component.status == ServiceStatus.CRITICAL:
                status_icon = "❌"
            else:
                status_icon = "❓"
            
            lines.append(f"{status_icon} {component.name}: {component.message}")
            if detailed and component.details:
                lines.append(f"   {component.details}")
        
        lines.append("")
        
        # Overall status
        healthy_count = sum(1 for c in components if c.status == ServiceStatus.HEALTHY)
        warning_count = sum(1 for c in components if c.status == ServiceStatus.WARNING)
        critical_count = sum(1 for c in components if c.status == ServiceStatus.CRITICAL)
        
        if critical_count > 0:
            lines.append("🔴 Overall Status: CRITICAL")
        elif warning_count > 0:
            lines.append("🟡 Overall Status: WARNING")
        else:
            lines.append("🟢 Overall Status: HEALTHY")
        
        lines.append(f"Components: {healthy_count} healthy, {warning_count} warnings, {critical_count} critical")
        lines.append("")
        
        # Quick commands
        lines.append("🛠️  Quick Commands:")
        lines.append("   📝 View logs:     tail -f logs/cron-voice.log")
        lines.append("   🧪 Test manually: vtm process --dry-run")
        lines.append("   📊 View stats:    vtm analyze --stats")
        lines.append("   🔧 Setup cron:    vtm setup --cron")
        
        return "\n".join(lines)
    
    def _format_json_status(self, components: List[SystemComponent], detailed: bool) -> str:
        """Format status as JSON"""
        status_data = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": self._get_overall_status(components).value,
            "components": []
        }
        
        for component in components:
            component_data = {
                "name": component.name,
                "status": component.status.value,
                "message": component.message
            }
            
            if detailed and component.details:
                component_data["details"] = component.details
            
            if component.last_check:
                component_data["last_check"] = component.last_check.isoformat()
            
            status_data["components"].append(component_data)
        
        # Summary statistics
        status_data["summary"] = {
            "total_components": len(components),
            "healthy": sum(1 for c in components if c.status == ServiceStatus.HEALTHY),
            "warnings": sum(1 for c in components if c.status == ServiceStatus.WARNING),
            "critical": sum(1 for c in components if c.status == ServiceStatus.CRITICAL),
            "unknown": sum(1 for c in components if c.status == ServiceStatus.UNKNOWN)
        }
        
        return json.dumps(status_data, indent=2)
    
    def _get_overall_status(self, components: List[SystemComponent]) -> ServiceStatus:
        """Determine overall system status"""
        if any(c.status == ServiceStatus.CRITICAL for c in components):
            return ServiceStatus.CRITICAL
        elif any(c.status == ServiceStatus.WARNING for c in components):
            return ServiceStatus.WARNING
        elif any(c.status == ServiceStatus.UNKNOWN for c in components):
            return ServiceStatus.WARNING  # Treat unknown as warning
        else:
            return ServiceStatus.HEALTHY

class SystemSetup:
    """System setup and configuration management"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize system setup manager
        
        Args:
            project_root: Project root directory (auto-detected if None)
        """
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.logger = VoiceLogger(self.project_root)
        self.console = Console() if HAS_RICH else None
        
        # Key paths
        self.venv_path = self.project_root / 'venv'
        self.log_path = self.project_root / 'logs' / 'cron-voice.log'
        self.scripts_dir = self.project_root / 'scripts'
    
    def configure_cron(self) -> str:
        """Configure cron job for automated processing"""
        lines = []
        lines.append("🔧 Configuring voice processing automation...")
        lines.append(f"📁 Project root: {self.project_root}")
        lines.append(f"📝 Logs: {self.log_path}")
        lines.append("")
        
        # Ensure directories exist
        self.log_path.parent.mkdir(exist_ok=True)
        (self.project_root / 'data').mkdir(exist_ok=True)
        lines.append("✅ Created required directories")
        
        # Create modern wrapper script using vtm command
        wrapper_script = self.scripts_dir / 'vtm-cron-wrapper.sh'
        wrapper_content = f"""#!/bin/bash
# Cron wrapper for voice processing automation (modern vtm package)
# This ensures proper environment and path setup

# Set working directory
cd "{self.project_root}"

# Activate virtual environment  
source "{self.venv_path}/bin/activate"

# Export path to ensure commands are found
export PATH="$PATH:/usr/local/bin:/usr/bin:/bin"

# Run the automation using new vtm package
vtm process >> "{self.log_path}" 2>&1

# Add separator to log
echo "----------------------------------------" >> "{self.log_path}"
"""
        
        try:
            wrapper_script.write_text(wrapper_content)
            wrapper_script.chmod(0o755)
            lines.append(f"✅ Created wrapper script: {wrapper_script}")
        except Exception as e:
            lines.append(f"❌ Failed to create wrapper script: {e}")
            return "\n".join(lines)
        
        # Generate crontab entry
        cron_entry = f"""# Voice processing automation - check every 5 minutes (vtm package)
*/5 * * * * {wrapper_script}"""
        
        lines.append("")
        lines.append("📋 Cron entry to add:")
        lines.append(cron_entry)
        lines.append("")
        
        # Check if we can install automatically
        try:
            # Check current crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_crontab = result.stdout if result.returncode == 0 else ""
            
            # Check if entry already exists
            if 'vtm-cron-wrapper' in current_crontab:
                lines.append("✅ Cron job already installed (vtm package)")
                return "\n".join(lines)
            elif 'voice-cron-wrapper' in current_crontab:
                lines.append("⚠️  Old cron job detected - will replace with new vtm version")
                # Remove old entries
                old_lines = [line for line in current_crontab.split('\n') 
                           if 'voice-cron-wrapper' not in line and line.strip()]
                current_crontab = '\n'.join(old_lines)
            
            # Install new crontab
            new_crontab = current_crontab + '\n' + cron_entry if current_crontab.strip() else cron_entry
            
            # Write to temporary file and install
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                temp_file.write(new_crontab)
                temp_file_path = temp_file.name
            
            install_result = subprocess.run(['crontab', temp_file_path], capture_output=True, text=True)
            os.unlink(temp_file_path)
            
            if install_result.returncode == 0:
                lines.append("✅ Cron job installed successfully!")
                lines.append("")
                lines.append("📊 View current crontab: crontab -l")
                lines.append(f"📝 View logs: tail -f {self.log_path}")
                lines.append("🔧 Edit crontab: crontab -e")
            else:
                lines.append(f"❌ Failed to install cron job: {install_result.stderr}")
                lines.append("📋 Manual installation:")
                lines.append("1. Run: crontab -e")  
                lines.append(f"2. Add: {cron_entry}")
                
        except FileNotFoundError:
            lines.append("❌ Cron service not available")
            lines.append("Install cron service first")
        except Exception as e:
            lines.append(f"❌ Cron setup failed: {e}")
            lines.append("📋 Manual installation:")
            lines.append("1. Run: crontab -e")
            lines.append(f"2. Add: {cron_entry}")
        
        lines.append("")
        lines.append("🎯 Automation setup complete!")
        lines.append("")
        lines.append("📋 Summary:")
        lines.append("  • Checks for new voice files every 5 minutes")
        lines.append("  • Processes audio files automatically via vtm package")
        lines.append("  • Creates tasks in Notion")
        lines.append("  • Tracks processed files to avoid duplicates")
        lines.append(f"  • Logs everything to: {self.log_path}")
        lines.append("")
        lines.append("🔍 Test manually: vtm process --dry-run")
        lines.append(f"📝 Check logs: tail -f {self.log_path}")
        lines.append("📊 View cron jobs: crontab -l")
        
        return "\n".join(lines)
    
    def validate_configuration(self) -> str:
        """Validate system configuration"""
        lines = []
        lines.append("🔍 Validating system configuration...")
        lines.append("")
        
        # Use SystemStatus for comprehensive validation
        status_checker = SystemStatus(self.project_root)
        components = status_checker._check_all_components(detailed=True)
        
        # Count issues
        critical_issues = [c for c in components if c.status == ServiceStatus.CRITICAL]
        warnings = [c for c in components if c.status == ServiceStatus.WARNING]
        
        if critical_issues:
            lines.append("❌ Critical Issues Found:")
            for issue in critical_issues:
                lines.append(f"   • {issue.name}: {issue.message}")
                if issue.details:
                    lines.append(f"     {issue.details}")
            lines.append("")
        
        if warnings:
            lines.append("⚠️  Warnings:")
            for warning in warnings:
                lines.append(f"   • {warning.name}: {warning.message}")
                if warning.details:
                    lines.append(f"     {warning.details}")
            lines.append("")
        
        # Recommendations
        lines.append("💡 Recommendations:")
        if critical_issues:
            lines.append("   1. Fix critical issues before running the system")
            if any("cron" in issue.name.lower() for issue in critical_issues):
                lines.append("      → Run 'vtm setup --cron' to install cron job")
            if any("environment" in issue.name.lower() for issue in critical_issues):
                lines.append("      → Create .env file with required API keys")
            if any("virtual" in issue.name.lower() for issue in critical_issues):
                lines.append("      → Create virtual environment: python -m venv venv")
        
        if warnings:
            lines.append("   2. Address warnings for optimal performance")
            
        if not critical_issues and not warnings:
            lines.append("   ✅ System is properly configured!")
            lines.append("   🚀 Ready for automated voice processing")
        
        lines.append("")
        lines.append("🧪 Test the system: vtm process --dry-run")
        lines.append("📊 Check status: vtm status --detailed")
        
        return "\n".join(lines)
    
    def reset_configuration(self) -> str:
        """Reset configuration to defaults"""
        lines = []
        lines.append("🔄 Resetting system configuration...")
        lines.append("")
        
        reset_actions = []
        
        # Remove cron jobs
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                current_crontab = result.stdout
                voice_lines = [line for line in current_crontab.split('\n') 
                             if 'voice-cron-wrapper' not in line and 'vtm-cron-wrapper' not in line]
                
                if len(voice_lines) != len(current_crontab.split('\n')):
                    # Write cleaned crontab
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                        temp_file.write('\n'.join(voice_lines))
                        temp_file_path = temp_file.name
                    
                    subprocess.run(['crontab', temp_file_path], check=True)
                    os.unlink(temp_file_path)
                    reset_actions.append("✅ Removed voice processing cron jobs")
                else:
                    reset_actions.append("ℹ️  No voice processing cron jobs found")
        except Exception as e:
            reset_actions.append(f"⚠️  Could not modify crontab: {e}")
        
        # Clean up wrapper scripts
        wrapper_scripts = [
            self.scripts_dir / 'voice-cron-wrapper.sh',
            self.scripts_dir / 'vtm-cron-wrapper.sh'
        ]
        
        for script in wrapper_scripts:
            if script.exists():
                try:
                    script.unlink()
                    reset_actions.append(f"✅ Removed {script.name}")
                except Exception as e:
                    reset_actions.append(f"⚠️  Could not remove {script.name}: {e}")
        
        # Clean up old log files (keep recent ones)
        log_dir = self.project_root / 'logs'
        if log_dir.exists():
            try:
                old_logs = []
                for log_file in log_dir.glob('*.log'):
                    # Keep files modified in last 7 days
                    if (datetime.now().timestamp() - log_file.stat().st_mtime) > (7 * 24 * 3600):
                        old_logs.append(log_file)
                
                if old_logs:
                    for log_file in old_logs:
                        log_file.unlink()
                    reset_actions.append(f"✅ Cleaned up {len(old_logs)} old log files")
                else:
                    reset_actions.append("ℹ️  No old log files to clean up")
            except Exception as e:
                reset_actions.append(f"⚠️  Could not clean log files: {e}")
        
        lines.extend(reset_actions)
        lines.append("")
        
        if reset_actions:
            lines.append("🎯 Configuration reset complete!")
            lines.append("")
            lines.append("Next steps:")
            lines.append("   1. Configure environment: Create .env file with API keys")
            lines.append("   2. Set up automation: vtm setup --cron")
            lines.append("   3. Validate setup: vtm setup --validate")
            lines.append("   4. Test system: vtm process --dry-run")
        else:
            lines.append("ℹ️  No configuration changes needed")
        
        return "\n".join(lines)