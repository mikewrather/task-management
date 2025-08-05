"""
Parameter Validation and Help System

Provides intelligent parameter validation with helpful error messages and suggestions.
Implements the context-aware parameter validation described in the planning document.
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from difflib import get_close_matches
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# from ..integrations.notion import NotionClient  # Removed - using pure GraphRAG now
from ..utils.logging import VoiceLogger


class ParameterValidationError(Exception):
    """Custom exception for parameter validation errors with helpful suggestions"""
    
    def __init__(self, message: str, valid_options: List[str], examples: List[str] = None):
        self.message = message
        self.valid_options = valid_options
        self.examples = examples or []
        super().__init__(message)


class ParameterValidator:
    """
    Parameter validation system with intelligent help and suggestions
    
    Provides context-aware validation for CLI parameters with helpful error messages,
    fuzzy matching suggestions, and dynamic option fetching from Notion databases.
    """
    
    def __init__(self, logger: VoiceLogger = None):
        self.logger = logger
        self.console = Console()
        
        # Cache for valid options to avoid repeated API calls
        self._option_cache: Dict[str, Dict[str, List[str]]] = {}
        self._cache_timestamp: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=30)  # Cache valid for 30 minutes
    
    def validate_status(self, status: str, database_type: str = 'tasks') -> str:
        """
        Validate status parameter for tasks, projects, or areas
        
        Args:
            status: Status value to validate
            database_type: Type of database ('tasks', 'projects', 'areas')
            
        Returns:
            Validated status value
            
        Raises:
            ParameterValidationError: If status is invalid
        """
        valid_statuses = self._get_valid_statuses(database_type)
        
        if status in valid_statuses:
            return status
        
        # Try fuzzy matching
        suggestions = get_close_matches(status, valid_statuses, n=1, cutoff=0.6)
        
        examples = [
            f"vtm list {database_type} --status=\"{valid_statuses[0]}\"",
            f"vtm filter {database_type} --status=\"{valid_statuses[1] if len(valid_statuses) > 1 else valid_statuses[0]}\""
        ]
        
        error_msg = f"'{status}' is not a valid {database_type} status."
        if suggestions:
            error_msg += f" Did you mean '{suggestions[0]}'?"
        
        raise ParameterValidationError(error_msg, valid_statuses, examples)
    
    def validate_priority(self, priority: str) -> str:
        """
        Validate priority parameter
        
        Args:
            priority: Priority value to validate
            
        Returns:
            Validated priority value
            
        Raises:
            ParameterValidationError: If priority is invalid
        """
        valid_priorities = ["Low", "Medium", "High", "Urgent"]
        
        if priority in valid_priorities:
            return priority
        
        # Try case-insensitive match
        priority_lower = priority.lower()
        for valid_priority in valid_priorities:
            if valid_priority.lower() == priority_lower:
                return valid_priority
        
        # Try fuzzy matching
        suggestions = get_close_matches(priority, valid_priorities, n=1, cutoff=0.6)
        
        examples = [
            "vtm filter tasks --priority=\"High,Urgent\"",
            "vtm list tasks --priority=\"Medium\""
        ]
        
        error_msg = f"'{priority}' is not a valid priority level."
        if suggestions:
            error_msg += f" Did you mean '{suggestions[0]}'?"
        
        raise ParameterValidationError(error_msg, valid_priorities, examples)
    
    def validate_energy(self, energy: str) -> str:
        """
        Validate energy parameter
        
        Args:
            energy: Energy value to validate
            
        Returns:
            Validated energy value
            
        Raises:
            ParameterValidationError: If energy is invalid
        """
        valid_energies = ["Low", "Medium", "High", "Extreme"]
        
        if energy in valid_energies:
            return energy
        
        # Try case-insensitive match
        energy_lower = energy.lower()
        for valid_energy in valid_energies:
            if valid_energy.lower() == energy_lower:
                return valid_energy
        
        # Try fuzzy matching
        suggestions = get_close_matches(energy, valid_energies, n=1, cutoff=0.6)
        
        examples = [
            "vtm list tasks --energy=\"High\" --status=\"Next Action\"",
            "vtm filter tasks --energy=\"Low,Medium\""
        ]
        
        error_msg = f"'{energy}' is not a valid energy level."
        if suggestions:
            error_msg += f" Did you mean '{suggestions[0]}'?"
        
        raise ParameterValidationError(error_msg, valid_energies, examples)
    
    def validate_context(self, context: str) -> str:
        """
        Validate context parameter
        
        Args:
            context: Context value to validate
            
        Returns:
            Validated context value
            
        Raises:
            ParameterValidationError: If context is invalid
        """
        valid_contexts = self._get_valid_contexts()
        
        if context in valid_contexts:
            return context
        
        # Try case-insensitive match
        context_lower = context.lower()
        for valid_context in valid_contexts:
            if valid_context.lower() == context_lower:
                return valid_context
        
        # Try fuzzy matching
        suggestions = get_close_matches(context, valid_contexts, n=1, cutoff=0.6)
        
        examples = [
            "vtm filter tasks --context=\"voice,Computer\"",
            "vtm list tasks --context=\"Phone\""
        ]
        
        error_msg = f"'{context}' is not a valid context."
        if suggestions:
            error_msg += f" Did you mean '{suggestions[0]}'?"
        
        raise ParameterValidationError(error_msg, valid_contexts, examples)
    
    def validate_date(self, date_str: str) -> datetime:
        """
        Validate and parse date parameter with natural language support
        
        Args:
            date_str: Date string to validate and parse
            
        Returns:
            Parsed datetime object
            
        Raises:
            ParameterValidationError: If date format is invalid
        """
        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        # Try natural language parsing
        parsed_date = self._parse_natural_date(date_str)
        if parsed_date:
            return parsed_date
        
        valid_formats = [
            "ISO format: 2025-07-25",
            "Relative: \"7 days ago\", \"last week\", \"yesterday\"",
            "Keywords: \"today\", \"tomorrow\""
        ]
        
        examples = [
            "vtm filter tasks --created-after=\"last week\"",
            "vtm list tasks --due-before=\"today\""
        ]
        
        error_msg = f"Could not parse date '{date_str}'."
        raise ParameterValidationError(error_msg, valid_formats, examples)
    
    def display_validation_error(self, error: ParameterValidationError) -> None:
        """
        Display a formatted validation error with helpful suggestions
        
        Args:
            error: ParameterValidationError to display
        """
        # Error message
        self.console.print(f"❌ Error: {error.message}", style="red")
        self.console.print()
        
        # Valid options
        if error.valid_options:
            self.console.print("✅ Valid options:", style="green")
            
            if len(error.valid_options) > 10:
                # Group options for better display
                self._display_grouped_options(error.valid_options)
            else:
                for option in error.valid_options:
                    # Try to infer context from error message
                    context = None
                    if "priority" in error.message.lower():
                        context = "priority"
                    elif "energy" in error.message.lower():
                        context = "energy"
                    
                    description = self._get_option_description(option, context)
                    if description:
                        self.console.print(f"  • {option} ({description})", style="dim")
                    else:
                        self.console.print(f"  • {option}", style="dim")
        
        self.console.print()
        
        # Examples
        if error.examples:
            self.console.print("💡 Examples:", style="blue")
            for example in error.examples:
                self.console.print(f"  {example}", style="cyan")
    
    def get_help_for_parameter(self, parameter: str, database_type: str = 'tasks') -> None:
        """
        Display comprehensive help for a specific parameter
        
        Args:
            parameter: Parameter name to show help for
            database_type: Database type for context
        """
        help_methods = {
            'status': lambda: self._show_status_help(database_type),
            'priority': self._show_priority_help,
            'energy': self._show_energy_help,
            'context': self._show_context_help,
            'date': self._show_date_help
        }
        
        if parameter in help_methods:
            help_methods[parameter]()
        else:
            self.console.print(f"❌ No help available for parameter: {parameter}", style="red")
    
    def _get_valid_statuses(self, database_type: str) -> List[str]:
        """Get valid status options for a database type"""
        if database_type == 'tasks':
            return ["Inbox", "Next Action", "Waiting On", "Someday", "Completed"]
        elif database_type == 'projects':
            return ["Inbox", "Not Started", "In Progress", "On Hold", "Completed"]
        elif database_type == 'areas':
            return ["Inbox", "Not Started", "In Progress", "On Hold", "Completed"]
        else:
            return []
    
    def _get_valid_contexts(self) -> List[str]:
        """Get valid context options from cache or Notion API"""
        cache_key = 'contexts'
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            return self._option_cache['tasks'][cache_key]
        
        # Fallback to known contexts if API unavailable
        contexts = [
            "Phone", "Computer", "Home", "Email", "Online Shopping",
            "Digital Marketing", "Mobile Development", "Infrastructure", 
            "voice", "voice-created", "auto-processed", "needs-review", "test"
        ]
        
        # GraphRAG integration could be added here to fetch dynamic contexts
        # For now, use static list of known contexts
        
        # Update cache
        if 'tasks' not in self._option_cache:
            self._option_cache['tasks'] = {}
        self._option_cache['tasks'][cache_key] = contexts
        self._cache_timestamp[f"tasks.{cache_key}"] = datetime.now()
        
        return contexts
    
    def _parse_natural_date(self, date_str: str) -> Optional[datetime]:
        """Parse natural language date expressions"""
        date_str = date_str.lower().strip()
        now = datetime.now()
        
        # Today/tomorrow/yesterday
        if date_str == 'today':
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_str == 'tomorrow':
            return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_str == 'yesterday':
            return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # X days ago
        days_ago_match = re.match(r'(\d+)\s+days?\s+ago', date_str)
        if days_ago_match:
            days = int(days_ago_match.group(1))
            return (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Last week/month
        if date_str == 'last week':
            return (now - timedelta(weeks=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_str == 'last month':
            return (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        return None
    
    def _is_cache_valid(self, cache_key: str, database_type: str = 'tasks') -> bool:
        """Check if cached options are still valid"""
        full_key = f"{database_type}.{cache_key}"
        
        if full_key not in self._cache_timestamp:
            return False
        
        if database_type not in self._option_cache:
            return False
        
        if cache_key not in self._option_cache[database_type]:
            return False
        
        cache_time = self._cache_timestamp[full_key]
        return datetime.now() - cache_time < self._cache_ttl
    
    def _get_option_description(self, option: str, context: str = None) -> Optional[str]:
        """Get description for an option value"""
        descriptions = {
            # Status descriptions
            "Inbox": "new, unprocessed items",
            "Next Action": "ready to work on",
            "Waiting On": "blocked by external dependencies",
            "Someday": "future consideration",
            "Completed": "finished items",
            "Not Started": "approved but not begun",
            "In Progress": "currently active",
            "On Hold": "temporarily paused",
            
            # Priority descriptions
            "Low_priority": "when time allows",
            "Medium_priority": "normal priority - default",
            "High_priority": "important, soon",
            "Urgent_priority": "immediate attention required",
            
            # Energy descriptions
            "Low_energy": "light, routine tasks",
            "Medium_energy": "moderate effort",
            "High_energy": "significant concentration needed",
            "Extreme_energy": "high focus, complex work"
        }
        
        # Try context-specific lookup first
        if context:
            context_key = f"{option}_{context}"
            if context_key in descriptions:
                return descriptions[context_key]
        
        # Fallback to generic lookup
        return descriptions.get(option)
    
    def _display_grouped_options(self, options: List[str]) -> None:
        """Display options grouped by category"""
        # For contexts, group them logically
        if all(ctx in ["Phone", "Computer", "Home", "Email", "Online Shopping",
                      "Digital Marketing", "Mobile Development", "Infrastructure", 
                      "voice", "voice-created", "auto-processed", "needs-review", "test"] for ctx in options):
            
            groups = {
                "Location-based": ["Phone", "Computer", "Home"],
                "Action-based": ["Email", "Online Shopping"],
                "Domain-based": ["Digital Marketing", "Mobile Development", "Infrastructure"],
                "System-generated": ["voice", "voice-created", "auto-processed", "needs-review", "test"]
            }
            
            for group_name, group_options in groups.items():
                valid_in_group = [opt for opt in group_options if opt in options]
                if valid_in_group:
                    self.console.print(f"  {group_name}: {', '.join(valid_in_group)}", style="dim")
        else:
            # Default ungrouped display
            for option in options:
                self.console.print(f"  • {option}", style="dim")
    
    def _show_status_help(self, database_type: str) -> None:
        """Show detailed help for status parameter"""
        statuses = self._get_valid_statuses(database_type)
        
        table = Table(title=f"{database_type.title()} Status Options")
        table.add_column("Status", style="cyan")
        table.add_column("Description", style="dim")
        
        for status in statuses:
            description = self._get_option_description(status) or ""
            table.add_row(status, description)
        
        self.console.print(table)
    
    def _show_priority_help(self) -> None:
        """Show detailed help for priority parameter"""
        priorities = ["Low", "Medium", "High", "Urgent"]
        
        table = Table(title="Priority Levels")
        table.add_column("Priority", style="cyan")
        table.add_column("Description", style="dim")
        
        for priority in priorities:
            description = self._get_option_description(priority) or ""
            table.add_row(priority, description)
        
        self.console.print(table)
    
    def _show_energy_help(self) -> None:
        """Show detailed help for energy parameter"""
        energies = ["Low", "Medium", "High", "Extreme"]
        
        table = Table(title="Energy Levels")
        table.add_column("Energy", style="cyan")
        table.add_column("Description", style="dim")
        
        for energy in energies:
            description = self._get_option_description(energy) or ""
            table.add_row(energy, description)
        
        self.console.print(table)
    
    def _show_context_help(self) -> None:
        """Show detailed help for context parameter"""
        contexts = self._get_valid_contexts()
        
        self.console.print(Panel.fit("Available Contexts", style="blue"))
        self._display_grouped_options(contexts)
    
    def _show_date_help(self) -> None:
        """Show detailed help for date parameters"""
        formats = [
            ("ISO Format", "2025-07-25", "Standard date format"),
            ("Relative Days", "7 days ago", "Number of days in the past"),
            ("Keywords", "today, tomorrow, yesterday", "Common date references"),
            ("Relative Periods", "last week, last month", "Recent time periods")
        ]
        
        table = Table(title="Date Format Options")
        table.add_column("Format Type", style="cyan")
        table.add_column("Example", style="green")
        table.add_column("Description", style="dim")
        
        for format_type, example, description in formats:
            table.add_row(format_type, example, description)
        
        self.console.print(table)