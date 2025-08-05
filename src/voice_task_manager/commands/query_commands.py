"""
Query Commands for CLI

Implements the list, search, and filter commands for querying Notion data
with intelligent parameter validation and help system.
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..core.parameter_validator import ParameterValidator, ParameterValidationError
# from ..integrations.notion import # NotionClient  # Removed - using pure GraphRAG now  # Removed - using pure GraphRAG now
from ..models.task import Task
# from ..models.notion_project import # NotionProject  # Removed - using pure GraphRAG now  # Removed - using pure GraphRAG now
# from ..models.notion_area import # NotionArea  # Removed - using pure GraphRAG now  # Removed - using pure GraphRAG now
from ..utils.logging import VoiceLogger


console = Console()


def _load_environment():
    """Load environment variables from .env file"""
    project_root = Path(__file__).parent.parent.parent.parent
    env_file = project_root / '.env'
    
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    try:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
                    except ValueError:
                        continue


@click.group()
def query():
    """Query and list Notion data"""
    pass


@query.command()
@click.option('--status', help='Filter by status')
@click.option('--context', help='Filter by context (comma-separated)')
@click.option('--project', help='Filter by project name or ID')
@click.option('--area', help='Filter by area name or ID')
@click.option('--priority', help='Filter by priority level')
@click.option('--energy', help='Filter by energy level')
@click.option('--format', 'output_format', 
              type=click.Choice(['json', 'table', 'rich'], case_sensitive=False),
              default='rich', help='Output format')
@click.option('--limit', type=int, default=50, help='Maximum number of results')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.pass_context
def tasks(ctx, status, context, project, area, priority, energy, output_format, limit, verbose):
    """
    List tasks from Notion Tasks database
    
    Examples:
      vtm list tasks --status="Next Action"
      vtm list tasks --context="voice,Computer" --priority="High"
      vtm list tasks --format=json
    """
    try:
        # Load environment variables
        _load_environment()
        
        # Initialize components
        logger = VoiceLogger()
        notion_client = # NotionClient  # Removed - using pure GraphRAG now(logger=logger)
        validator = ParameterValidator(notion_client, logger)
        
        if verbose:
            console.print("🔍 Querying Notion Tasks database...", style="dim")
        
        # Build query filters
        query_filters = {}
        
        # Validate and add status filter
        if status:
            try:
                validated_status = validator.validate_status(status, 'tasks')
                query_filters['status'] = validated_status
            except ParameterValidationError as e:
                validator.display_validation_error(e)
                sys.exit(1)
        
        # Validate and add priority filter
        if priority:
            try:
                validated_priority = validator.validate_priority(priority)
                query_filters['priority'] = validated_priority
            except ParameterValidationError as e:
                validator.display_validation_error(e)
                sys.exit(1)
        
        # Validate and add energy filter
        if energy:
            try:
                validated_energy = validator.validate_energy(energy)
                query_filters['energy'] = validated_energy
            except ParameterValidationError as e:
                validator.display_validation_error(e)
                sys.exit(1)
        
        # Validate and add context filter
        if context:
            try:
                contexts = [ctx.strip() for ctx in context.split(',')]
                validated_contexts = [validator.validate_context(ctx) for ctx in contexts]
                query_filters['contexts'] = validated_contexts
            except ParameterValidationError as e:
                validator.display_validation_error(e)
                sys.exit(1)
        
        # Add other filters (these don't need special validation yet)
        if project:
            query_filters['project'] = project
        if area:
            query_filters['area'] = area
        
        # Execute query
        start_time = datetime.now()
        tasks = _query_tasks(notion_client, query_filters, limit, verbose)
        query_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Display results
        _display_task_results(tasks, output_format, query_time, query_filters, verbose)
        
    except Exception as e:
        console.print(f"❌ Error executing query: {str(e)}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)


@query.command()
@click.option('--status', help='Filter by status')
@click.option('--area', help='Filter by area name or ID')
@click.option('--priority', help='Filter by priority level')
@click.option('--active-only', is_flag=True, help='Show only active projects')
@click.option('--format', 'output_format',
              type=click.Choice(['json', 'table', 'rich'], case_sensitive=False),
              default='rich', help='Output format')
@click.option('--limit', type=int, default=50, help='Maximum number of results')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.pass_context
def projects(ctx, status, area, priority, active_only, output_format, limit, verbose):
    """
    List projects from Notion Projects database
    
    Examples:
      vtm list projects --status="In Progress"
      vtm list projects --active-only --format=json
    """
    try:
        # Load environment variables
        _load_environment()
        
        # Initialize components
        logger = VoiceLogger()
        notion_client = # NotionClient  # Removed - using pure GraphRAG now(logger=logger)
        validator = ParameterValidator(notion_client, logger)
        
        if verbose:
            console.print("🔍 Querying Notion Projects database...", style="dim")
        
        # Build query filters
        query_filters = {}
        
        # Validate and add status filter
        if status:
            try:
                validated_status = validator.validate_status(status, 'projects')
                query_filters['status'] = validated_status
            except ParameterValidationError as e:
                validator.display_validation_error(e)
                sys.exit(1)
        
        # Validate and add priority filter
        if priority:
            try:
                validated_priority = validator.validate_priority(priority)
                query_filters['priority'] = validated_priority
            except ParameterValidationError as e:
                validator.display_validation_error(e)
                sys.exit(1)
        
        # Add other filters
        if area:
            query_filters['area'] = area
        if active_only:
            query_filters['active_only'] = True
        
        # Execute query
        start_time = datetime.now()
        projects = _query_projects(notion_client, query_filters, limit, verbose)
        query_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Display results
        _display_project_results(projects, output_format, query_time, query_filters, verbose)
        
    except Exception as e:
        console.print(f"❌ Error executing query: {str(e)}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)


@query.command()
@click.option('--status', help='Filter by status')
@click.option('--priority', help='Filter by priority level')
@click.option('--format', 'output_format',
              type=click.Choice(['json', 'table', 'rich'], case_sensitive=False),
              default='rich', help='Output format')
@click.option('--limit', type=int, default=50, help='Maximum number of results')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.pass_context
def areas(ctx, status, priority, output_format, limit, verbose):
    """
    List areas from Notion Areas database
    
    Examples:
      vtm list areas --status="In Progress"
      vtm list areas --format=json
    """
    try:
        # Load environment variables
        _load_environment()
        
        # Initialize components
        logger = VoiceLogger()
        notion_client = # NotionClient  # Removed - using pure GraphRAG now(logger=logger)
        validator = ParameterValidator(notion_client, logger)
        
        if verbose:
            console.print("🔍 Querying Notion Areas database...", style="dim")
        
        # Build query filters
        query_filters = {}
        
        # Validate and add status filter
        if status:
            try:
                validated_status = validator.validate_status(status, 'areas')
                query_filters['status'] = validated_status
            except ParameterValidationError as e:
                validator.display_validation_error(e)
                sys.exit(1)
        
        # Validate and add priority filter
        if priority:
            try:
                validated_priority = validator.validate_priority(priority)
                query_filters['priority'] = validated_priority
            except ParameterValidationError as e:
                validator.display_validation_error(e)
                sys.exit(1)
        
        # Execute query
        start_time = datetime.now()
        areas = _query_areas(notion_client, query_filters, limit, verbose)
        query_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Display results
        _display_area_results(areas, output_format, query_time, query_filters, verbose)
        
    except Exception as e:
        console.print(f"❌ Error executing query: {str(e)}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)


# Helper functions for querying

def _query_tasks(notion_client: # NotionClient  # Removed - using pure GraphRAG now, filters: Dict[str, Any], limit: int, verbose: bool) -> List[Task]:
    """Query tasks from Notion with filters"""
    if verbose:
        console.print(f"  Applied filters: {filters}", style="dim")
        console.print(f"  Result limit: {limit}", style="dim")
    
    # Build Notion API filter from our simplified filters
    notion_filter = _build_task_filter(filters)
    
    # Query Notion
    return notion_client.query_tasks(notion_filter, limit)


def _query_projects(notion_client: # NotionClient  # Removed - using pure GraphRAG now, filters: Dict[str, Any], limit: int, verbose: bool) -> List[# NotionProject  # Removed - using pure GraphRAG now]:
    """Query projects from Notion with filters"""
    if verbose:
        console.print(f"  Applied filters: {filters}", style="dim")
        console.print(f"  Result limit: {limit}", style="dim")
    
    # Build Notion API filter from our simplified filters
    notion_filter = _build_project_filter(filters)
    
    # Query Notion
    return notion_client.query_projects(notion_filter, limit)


def _query_areas(notion_client: # NotionClient  # Removed - using pure GraphRAG now, filters: Dict[str, Any], limit: int, verbose: bool) -> List[# NotionArea  # Removed - using pure GraphRAG now]:
    """Query areas from Notion with filters"""
    if verbose:
        console.print(f"  Applied filters: {filters}", style="dim")
        console.print(f"  Result limit: {limit}", style="dim")
    
    # Build Notion API filter from our simplified filters
    notion_filter = _build_area_filter(filters)
    
    # Query Notion
    return notion_client.query_areas(notion_filter, limit)


# Helper functions for displaying results

def _display_task_results(tasks: List[Task], output_format: str, query_time: float, 
                         filters: Dict[str, Any], verbose: bool) -> None:
    """Display task query results in specified format"""
    
    if output_format == 'json':
        result = {
            "success": True,
            "data": [task.to_dict() for task in tasks],
            "metadata": {
                "total_count": len(tasks),
                "query_time_ms": round(query_time, 2),
                "filters_applied": filters,
                "cached": False
            },
            "timestamp": datetime.now().isoformat()
        }
        console.print(json.dumps(result, indent=2))
        
    elif output_format == 'table':
        table = Table(title=f"Tasks ({len(tasks)} results)")
        table.add_column("Name", style="cyan", max_width=40)
        table.add_column("Status", style="green")
        table.add_column("Priority", style="yellow")
        table.add_column("Context", style="blue")
        
        for task in tasks[:20]:  # Limit table display
            contexts = ', '.join(task.contexts) if hasattr(task, 'contexts') else ''
            table.add_row(
                task.title[:37] + "..." if len(task.title) > 40 else task.title,
                task.status,
                getattr(task, 'priority', ''),
                contexts[:20] + "..." if len(contexts) > 20 else contexts
            )
        
        console.print(table)
        
        if verbose:
            console.print(f"\n🕒 Query completed in {query_time:.2f}ms", style="dim")
            
    else:  # rich format
        if not tasks:
            console.print("📭 No tasks found matching the criteria", style="yellow")
            return
        
        console.print(f"📋 Found {len(tasks)} tasks", style="green")
        
        for i, task in enumerate(tasks[:10], 1):  # Show first 10 in rich format
            panel_content = f"**Status:** {task.status}\n"
            if hasattr(task, 'priority'):
                panel_content += f"**Priority:** {task.priority}\n"
            if hasattr(task, 'contexts'):
                panel_content += f"**Contexts:** {', '.join(task.contexts)}\n"
            
            console.print(Panel(
                panel_content,
                title=f"{i}. {task.title[:50]}{'...' if len(task.title) > 50 else ''}",
                title_align="left"
            ))
        
        if len(tasks) > 10:
            console.print(f"\n... and {len(tasks) - 10} more tasks", style="dim")
        
        if verbose:
            console.print(f"\n🕒 Query completed in {query_time:.2f}ms", style="dim")


def _display_project_results(projects: List[# NotionProject  # Removed - using pure GraphRAG now], output_format: str, query_time: float,
                           filters: Dict[str, Any], verbose: bool) -> None:
    """Display project query results in specified format"""
    
    if output_format == 'json':
        result = {
            "success": True,
            "data": [project.to_dict() for project in projects],
            "metadata": {
                "total_count": len(projects),
                "query_time_ms": round(query_time, 2),
                "filters_applied": filters,
                "cached": False
            },
            "timestamp": datetime.now().isoformat()
        }
        console.print(json.dumps(result, indent=2))
        
    elif output_format == 'table':
        table = Table(title=f"Projects ({len(projects)} results)")
        table.add_column("Name", style="cyan", max_width=40)
        table.add_column("Status", style="green")
        table.add_column("Priority", style="yellow")
        table.add_column("Progress", style="blue")
        
        for project in projects[:20]:
            progress = f"{project.completion_percentage():.0%}" if project.completion_percentage() else "0%"
            table.add_row(
                project.name[:37] + "..." if len(project.name) > 40 else project.name,
                project.status,
                project.priority,
                progress
            )
        
        console.print(table)
        
        if verbose:
            console.print(f"\n🕒 Query completed in {query_time:.2f}ms", style="dim")
            
    else:  # rich format
        if not projects:
            console.print("📭 No projects found matching the criteria", style="yellow")
            return
        
        console.print(f"🗂️ Found {len(projects)} projects", style="green")
        
        for i, project in enumerate(projects[:10], 1):
            panel_content = f"**Status:** {project.status}\n"
            panel_content += f"**Priority:** {project.priority}\n"
            if project.progress:
                panel_content += f"**Progress:** {project.completion_percentage():.0%}\n"
            
            console.print(Panel(
                panel_content,
                title=f"{i}. {project.name[:50]}{'...' if len(project.name) > 50 else ''}",
                title_align="left"
            ))
        
        if len(projects) > 10:
            console.print(f"\n... and {len(projects) - 10} more projects", style="dim")
        
        if verbose:
            console.print(f"\n🕒 Query completed in {query_time:.2f}ms", style="dim")


def _display_area_results(areas: List[# NotionArea  # Removed - using pure GraphRAG now], output_format: str, query_time: float,
                         filters: Dict[str, Any], verbose: bool) -> None:
    """Display area query results in specified format"""
    
    if output_format == 'json':
        result = {
            "success": True,
            "data": [area.to_dict() for area in areas],
            "metadata": {
                "total_count": len(areas),
                "query_time_ms": round(query_time, 2),
                "filters_applied": filters,
                "cached": False
            },
            "timestamp": datetime.now().isoformat()
        }
        console.print(json.dumps(result, indent=2))
        
    elif output_format == 'table':
        table = Table(title=f"Areas ({len(areas)} results)")
        table.add_column("Name", style="cyan", max_width=40)
        table.add_column("Status", style="green")
        table.add_column("Priority", style="yellow")
        table.add_column("Progress", style="blue")
        
        for area in areas[:20]:
            progress = f"{area.completion_percentage():.0%}" if area.completion_percentage() else "0%"
            table.add_row(
                area.name[:37] + "..." if len(area.name) > 40 else area.name,
                area.status,
                area.priority,
                progress
            )
        
        console.print(table)
        
        if verbose:
            console.print(f"\n🕒 Query completed in {query_time:.2f}ms", style="dim")
            
    else:  # rich format
        if not areas:
            console.print("📭 No areas found matching the criteria", style="yellow")
            return
        
        console.print(f"🗂️ Found {len(areas)} areas", style="green")
        
        for i, area in enumerate(areas[:10], 1):
            panel_content = f"**Status:** {area.status}\n"
            panel_content += f"**Priority:** {area.priority}\n"
            if area.progress:
                panel_content += f"**Progress:** {area.completion_percentage():.0%}\n"
            
            console.print(Panel(
                panel_content,
                title=f"{i}. {area.name[:50]}{'...' if len(area.name) > 50 else ''}",
                title_align="left"
            ))
        
        if len(areas) > 10:
            console.print(f"\n... and {len(areas) - 10} more areas", style="dim")
        
        if verbose:
            console.print(f"\n🕒 Query completed in {query_time:.2f}ms", style="dim")


# Filter building functions

def _build_task_filter(filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build Notion API filter for tasks from simplified filter dict"""
    if not filters:
        return None
    
    filter_conditions = []
    
    # Status filter
    if 'status' in filters:
        filter_conditions.append({
            "property": "Status",
            "status": {
                "equals": filters['status']
            }
        })
    
    # Priority filter
    if 'priority' in filters:
        filter_conditions.append({
            "property": "Priority", 
            "select": {
                "equals": filters['priority']
            }
        })
    
    # Energy filter
    if 'energy' in filters:
        filter_conditions.append({
            "property": "Energy",
            "select": {
                "equals": filters['energy']
            }
        })
    
    # Context filter (multi-select)
    if 'contexts' in filters:
        for context in filters['contexts']:
            filter_conditions.append({
                "property": "Contexts",
                "multi_select": {
                    "contains": context
                }
            })
    
    # Project filter (relation)
    if 'project' in filters:
        # This would need to be enhanced to handle project name lookups
        pass
    
    # Area filter (relation)
    if 'area' in filters:
        # This would need to be enhanced to handle area name lookups
        pass
    
    # Combine conditions with AND
    if len(filter_conditions) == 1:
        return filter_conditions[0]
    elif len(filter_conditions) > 1:
        return {"and": filter_conditions}
    
    return None


def _build_project_filter(filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build Notion API filter for projects from simplified filter dict"""
    if not filters:
        return None
    
    filter_conditions = []
    
    # Status filter
    if 'status' in filters:
        filter_conditions.append({
            "property": "Status",
            "status": {
                "equals": filters['status']
            }
        })
    
    # Priority filter
    if 'priority' in filters:
        filter_conditions.append({
            "property": "Priority",
            "select": {
                "equals": filters['priority']
            }
        })
    
    # Active only filter
    if filters.get('active_only'):
        filter_conditions.extend([
            {
                "property": "Status",
                "status": {
                    "equals": "In Progress"
                }
            },
            {
                "property": "Archive",
                "checkbox": {
                    "equals": False
                }
            }
        ])
    
    # Area filter (relation)
    if 'area' in filters:
        # This would need to be enhanced to handle area name lookups
        pass
    
    # Combine conditions with AND
    if len(filter_conditions) == 1:
        return filter_conditions[0]
    elif len(filter_conditions) > 1:
        return {"and": filter_conditions}
    
    return None


def _build_area_filter(filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build Notion API filter for areas from simplified filter dict"""
    if not filters:
        return None
    
    filter_conditions = []
    
    # Status filter
    if 'status' in filters:
        filter_conditions.append({
            "property": "Status",
            "status": {
                "equals": filters['status']
            }
        })
    
    # Priority filter
    if 'priority' in filters:
        filter_conditions.append({
            "property": "Priority",
            "select": {
                "equals": filters['priority']
            }
        })
    
    # Combine conditions with AND
    if len(filter_conditions) == 1:
        return filter_conditions[0]
    elif len(filter_conditions) > 1:
        return {"and": filter_conditions}
    
    return None


@query.command()
@click.argument('task_id', required=True)
@click.option('--confirm', is_flag=True, help='Confirm deletion without interactive prompt')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without actually doing it')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.pass_context
def delete_task(ctx, task_id, confirm, dry_run, verbose):
    """
    Delete (archive) a task from Notion Tasks database
    
    Examples:
      vtm list delete-task abc123-def456-ghi789 --confirm
      vtm list delete-task abc123-def456-ghi789 --dry-run
    """
    try:
        # Load environment variables
        _load_environment()
        
        # Initialize components
        logger = VoiceLogger()
        notion_client = # NotionClient  # Removed - using pure GraphRAG now(logger=logger)
        
        if verbose:
            console.print(f"🔍 Processing delete request for task: {task_id}", style="dim")
        
        if dry_run:
            console.print("🧪 [yellow]DRY RUN MODE[/yellow] - No actual deletion will be performed")
            
            # Try to fetch the task to show what would be deleted
            try:
                task = notion_client.get_task(task_id)
                if task:
                    console.print(f"\n📋 Task to be deleted:")
                    console.print(f"   ID: {task.task_id}")
                    console.print(f"   Title: {task.title}")
                    console.print(f"   Status: {task.status}")
                    console.print(f"   Created: {task.created_at}")
                    console.print(f"\n✅ Task exists and would be archived (not permanently deleted)")
                else:
                    console.print(f"❌ Task with ID {task_id} not found")
                    sys.exit(1)
            except Exception as e:
                console.print(f"❌ Error fetching task: {str(e)}", style="red")
                sys.exit(1)
                
            return
        
        # Interactive confirmation if not provided
        if not confirm:
            # Try to fetch task details for confirmation
            try:
                task = notion_client.get_task(task_id)
                if task:
                    console.print(f"\n📋 Task to delete:")
                    console.print(f"   Title: {task.title}")
                    console.print(f"   Status: {task.status}")
                    console.print(f"   Created: {task.created_at}")
                else:
                    console.print(f"❌ Task with ID {task_id} not found")
                    sys.exit(1)
            except Exception as e:
                console.print(f"⚠️  Could not fetch task details: {str(e)}")
                console.print(f"   Proceeding with deletion of task ID: {task_id}")
            
            # Ask for confirmation
            if not click.confirm("\n⚠️  Are you sure you want to delete this task? (This will archive it in Notion)"):
                console.print("❌ Deletion cancelled")
                return
        
        # Perform the deletion
        if verbose:
            console.print("🗑️  Deleting task...", style="dim")
        
        start_time = datetime.now()
        success = notion_client.delete_task(task_id)
        operation_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if success:
            console.print(f"✅ Task {task_id} successfully deleted (archived)", style="green")
            if verbose:
                console.print(f"🕒 Operation completed in {operation_time:.2f}ms", style="dim")
        else:
            console.print(f"❌ Failed to delete task {task_id}", style="red")
            console.print("   Possible reasons:")
            console.print("   • Task ID does not exist")
            console.print("   • Task is already archived")
            console.print("   • Insufficient permissions")
            console.print("   • Network or API error")
            sys.exit(1)
        
    except Exception as e:
        console.print(f"❌ Error executing delete: {str(e)}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)