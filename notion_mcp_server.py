#!/home/mike/development/task-management/.venv/bin/python
"""
MCP Server for Voice Task Management Notion CLI Tools

This server exposes the vtm CLI commands as MCP tools for AI agents.
Provides structured access to Notion tasks, projects, and areas.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import Context

# Initialize FastMCP server
mcp = FastMCP(
    name="Notion Task Management",
    description="Voice Task Management CLI tools exposed via MCP for AI agents"
)

# Configuration
DEFAULT_LIMIT = 50
MAX_LIMIT = 100
VTM_COMMAND = "vtm"

class MCPError(Exception):
    """Custom exception for MCP server errors"""
    pass

class CliExecutionError(MCPError):
    """Error executing CLI command"""
    pass

class ValidationError(MCPError):
    """Parameter validation error"""
    pass

def _validate_parameters(**kwargs) -> Dict[str, Any]:
    """Validate and sanitize input parameters"""
    validated = {}
    
    # Validate limit
    if 'limit' in kwargs and kwargs['limit'] is not None:
        limit = kwargs['limit']
        if not isinstance(limit, int) or limit < 1 or limit > MAX_LIMIT:
            raise ValidationError(f"Limit must be an integer between 1 and {MAX_LIMIT}")
        validated['limit'] = limit
    else:
        validated['limit'] = DEFAULT_LIMIT
    
    # Validate format
    if 'format' in kwargs and kwargs['format'] is not None:
        format_val = kwargs['format'].lower()
        if format_val not in ['json', 'table', 'rich']:
            raise ValidationError("Format must be one of: json, table, rich")
        validated['format'] = format_val
    else:
        validated['format'] = 'json'  # Default to JSON for structured output
    
    # Validate boolean parameters
    for bool_param in ['verbose', 'active_only']:
        if bool_param in kwargs and kwargs[bool_param] is not None:
            validated[bool_param] = bool(kwargs[bool_param])
    
    # Validate string parameters (basic sanitization)
    string_params = ['status', 'context', 'project', 'area', 'priority', 'energy']
    for param in string_params:
        if param in kwargs and kwargs[param] is not None:
            value = str(kwargs[param]).strip()
            if value:  # Only add non-empty strings
                # Basic sanitization - remove potentially dangerous characters
                sanitized = ''.join(c for c in value if c.isalnum() or c in ' ,-_')
                if sanitized:
                    validated[param] = sanitized
    
    return validated

def _build_cli_command(base_cmd: List[str], params: Dict[str, Any]) -> List[str]:
    """Build CLI command from validated parameters"""
    cmd = base_cmd.copy()
    
    # Add parameter flags
    for param, value in params.items():
        if param in ['limit', 'format', 'verbose']:
            # Handle special parameters
            if param == 'limit':
                cmd.extend(['--limit', str(value)])
            elif param == 'format':
                cmd.extend(['--format', value])
            elif param == 'verbose' and value:
                cmd.append('--verbose')
        elif param == 'active_only' and value:
            cmd.append('--active-only')
        elif param in ['status', 'context', 'project', 'area', 'priority', 'energy']:
            # Regular parameter flags
            cmd.extend([f'--{param}', value])
    
    return cmd

def _execute_cli_command(cmd: List[str]) -> Dict[str, Any]:
    """Execute CLI command and return structured result"""
    try:
        # Execute command with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,  # 30-second timeout
            cwd=Path(__file__).parent,  # Set working directory to project root
            env=None  # Inherit environment
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Command failed"
            raise CliExecutionError(f"CLI command failed: {error_msg}")
        
        output = result.stdout.strip()
        
        # Try to parse as JSON if format was json
        if '--format' in cmd and 'json' in cmd:
            try:
                # Clean the output by removing log lines that appear before JSON
                # Look for the first line that starts with '{' (JSON object start)
                lines = output.split('\n')
                json_start = 0
                
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith('{'):
                        json_start = i
                        break
                
                # Join lines from JSON start onward
                clean_output = '\n'.join(lines[json_start:])
                
                # Fix common JSON formatting issues from CLI output
                # The CLI sometimes outputs unescaped newlines in string values
                # This is a temporary fix until CLI output is corrected
                try:
                    return json.loads(clean_output)
                except json.JSONDecodeError:
                    # Try to fix unescaped newlines in strings
                    # This is a basic fix - split by quotes and fix content between them
                    import re
                    
                    # Replace unescaped newlines in string values (between quotes)
                    # Pattern: find quoted strings and replace newlines with \n
                    def fix_string_newlines(match):
                        string_content = match.group(1)
                        # Replace actual newlines with escaped newlines
                        fixed_content = string_content.replace('\n', '\\n').replace('\r', '\\r')
                        return f'"{fixed_content}"'
                    
                    # Find quoted strings and fix newlines in them
                    fixed_output = re.sub(r'"([^"]*)"', fix_string_newlines, clean_output)
                    
                    return json.loads(fixed_output)
            except json.JSONDecodeError as e:
                # If JSON parsing still fails, return raw output with error note
                return {
                    "success": False,
                    "error": {
                        "type": "JSONDecodeError",
                        "message": f"Failed to parse CLI output as JSON: {str(e)}",
                        "raw_output": output,
                        "cleaned_output": clean_output if 'clean_output' in locals() else None
                    },
                    "timestamp": datetime.now().isoformat()
                }
        else:
            # For non-JSON formats, wrap in structured response
            return {
                "success": True,
                "data": {"output": output},
                "metadata": {
                    "format": "text",
                    "total_count": 1,
                    "query_time_ms": 0,
                    "cached": False
                },
                "timestamp": datetime.now().isoformat()
            }
            
    except subprocess.TimeoutExpired:
        raise CliExecutionError("CLI command timed out after 30 seconds")
    except subprocess.SubprocessError as e:
        raise CliExecutionError(f"Failed to execute CLI command: {str(e)}")
    except Exception as e:
        raise CliExecutionError(f"Unexpected error executing CLI: {str(e)}")

@mcp.tool()
async def list_tasks(
    status: Optional[str] = None,
    context: Optional[str] = None,
    project: Optional[str] = None,
    area: Optional[str] = None,
    priority: Optional[str] = None,
    energy: Optional[str] = None,
    format: str = "json",
    limit: int = DEFAULT_LIMIT,
    verbose: bool = False,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Query tasks from Notion with comprehensive filtering options.
    
    Returns structured task data with status, priority, context, and project information.
    Supports filtering by status, context, project, area, priority, and energy level.
    
    Args:
        status: Filter by task status (e.g., 'Not started', 'In progress', 'Done')
        context: Filter by context, comma-separated for multiple (e.g., 'voice,Computer')
        project: Filter by project name or ID
        area: Filter by area name or ID (e.g., 'Personal', 'Work')
        priority: Filter by priority level ('High', 'Medium', 'Low')
        energy: Filter by energy level required ('High', 'Medium', 'Low')
        format: Output format ('json', 'table', 'rich')
        limit: Maximum number of tasks to return (1-100)
        verbose: Include detailed query information
        
    Returns:
        Structured task data with metadata including query time and filters applied
    """
    try:
        if ctx:
            await ctx.info(f"Querying Notion tasks with filters: status={status}, area={area}, project={project}")
        
        # Validate parameters
        params = _validate_parameters(
            status=status, context=context, project=project, area=area,
            priority=priority, energy=energy, format=format, limit=limit, verbose=verbose
        )
        
        # Build CLI command
        base_cmd = [VTM_COMMAND, "list", "tasks"]
        cmd = _build_cli_command(base_cmd, params)
        
        if ctx and params.get('verbose'):
            await ctx.debug(f"Executing command: {' '.join(cmd)}")
        
        # Execute command
        start_time = datetime.now()
        result = _execute_cli_command(cmd)
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Add execution time to metadata if present
        if isinstance(result, dict) and 'metadata' in result:
            result['metadata']['query_time_ms'] = round(execution_time, 2)
        
        if ctx:
            await ctx.info(f"Query completed in {execution_time:.2f}ms")
        
        return result
        
    except (ValidationError, CliExecutionError) as e:
        error_result = {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
                "suggestions": [
                    "Check parameter values against valid options",
                    "Ensure vtm CLI is installed and accessible",
                    "Verify Notion API credentials are configured"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        if ctx:
            await ctx.error(f"Task query failed: {str(e)}")
            
        return error_result
    
    except Exception as e:
        error_result = {
            "success": False,
            "error": {
                "type": "UnexpectedError",
                "message": f"Unexpected error: {str(e)}",
                "suggestions": ["Check server logs for details", "Try again with simpler parameters"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        if ctx:
            await ctx.error(f"Unexpected error in task query: {str(e)}")
            
        return error_result

@mcp.tool()
async def list_projects(
    status: Optional[str] = None,
    area: Optional[str] = None,
    priority: Optional[str] = None,
    active_only: bool = False,
    format: str = "json",
    limit: int = DEFAULT_LIMIT,
    verbose: bool = False,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Query projects from Notion with filtering and progress information.
    
    Returns project data with status, completion metrics, and associated areas.
    Supports filtering by status, area, priority, and active status.
    
    Args:
        status: Filter by project status (e.g., 'Not started', 'In Progress', 'Done')
        area: Filter by area name or ID (e.g., 'Personal', 'Work')
        priority: Filter by priority level ('High', 'Medium', 'Low')
        active_only: Show only active projects (In Progress and not archived)
        format: Output format ('json', 'table', 'rich')
        limit: Maximum number of projects to return (1-100)
        verbose: Include detailed query information
        
    Returns:
        Structured project data with completion metrics and metadata
    """
    try:
        if ctx:
            await ctx.info(f"Querying Notion projects with filters: status={status}, area={area}, active_only={active_only}")
        
        # Validate parameters
        params = _validate_parameters(
            status=status, area=area, priority=priority, active_only=active_only,
            format=format, limit=limit, verbose=verbose
        )
        
        # Build CLI command
        base_cmd = [VTM_COMMAND, "list", "projects"]
        cmd = _build_cli_command(base_cmd, params)
        
        if ctx and params.get('verbose'):
            await ctx.debug(f"Executing command: {' '.join(cmd)}")
        
        # Execute command
        start_time = datetime.now()
        result = _execute_cli_command(cmd)
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Add execution time to metadata if present
        if isinstance(result, dict) and 'metadata' in result:
            result['metadata']['query_time_ms'] = round(execution_time, 2)
        
        if ctx:
            await ctx.info(f"Query completed in {execution_time:.2f}ms")
        
        return result
        
    except (ValidationError, CliExecutionError) as e:
        error_result = {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
                "suggestions": [
                    "Check parameter values against valid options",
                    "Ensure vtm CLI is installed and accessible",
                    "Verify Notion API credentials are configured"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        if ctx:
            await ctx.error(f"Project query failed: {str(e)}")
            
        return error_result
    
    except Exception as e:
        error_result = {
            "success": False,
            "error": {
                "type": "UnexpectedError",
                "message": f"Unexpected error: {str(e)}",
                "suggestions": ["Check server logs for details", "Try again with simpler parameters"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        if ctx:
            await ctx.error(f"Unexpected error in project query: {str(e)}")
            
        return error_result

@mcp.tool()
async def list_areas(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    format: str = "json",
    limit: int = DEFAULT_LIMIT,
    verbose: bool = False,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Query areas from Notion with project and task summary information.
    
    Returns area data with status, progress metrics, and associated counts.
    Provides overview of project and task counts per area.
    
    Args:
        status: Filter by area status (e.g., 'Active', 'On Hold', 'Archived')
        priority: Filter by priority level ('High', 'Medium', 'Low')
        format: Output format ('json', 'table', 'rich')
        limit: Maximum number of areas to return (1-100)
        verbose: Include detailed query information
        
    Returns:
        Structured area data with project/task counts and metadata
    """
    try:
        if ctx:
            await ctx.info(f"Querying Notion areas with filters: status={status}, priority={priority}")
        
        # Validate parameters
        params = _validate_parameters(
            status=status, priority=priority, format=format, limit=limit, verbose=verbose
        )
        
        # Build CLI command
        base_cmd = [VTM_COMMAND, "list", "areas"]
        cmd = _build_cli_command(base_cmd, params)
        
        if ctx and params.get('verbose'):
            await ctx.debug(f"Executing command: {' '.join(cmd)}")
        
        # Execute command
        start_time = datetime.now()
        result = _execute_cli_command(cmd)
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Add execution time to metadata if present
        if isinstance(result, dict) and 'metadata' in result:
            result['metadata']['query_time_ms'] = round(execution_time, 2)
        
        if ctx:
            await ctx.info(f"Query completed in {execution_time:.2f}ms")
        
        return result
        
    except (ValidationError, CliExecutionError) as e:
        error_result = {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
                "suggestions": [
                    "Check parameter values against valid options",
                    "Ensure vtm CLI is installed and accessible",
                    "Verify Notion API credentials are configured"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        if ctx:
            await ctx.error(f"Area query failed: {str(e)}")
            
        return error_result
    
    except Exception as e:
        error_result = {
            "success": False,
            "error": {
                "type": "UnexpectedError",
                "message": f"Unexpected error: {str(e)}",
                "suggestions": ["Check server logs for details", "Try again with simpler parameters"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        if ctx:
            await ctx.error(f"Unexpected error in area query: {str(e)}")
            
        return error_result

# Server health check and info
# =============================================================================
# NEW ENTITY TOOLS - Goals, Notes, Events, References
# =============================================================================

@mcp.tool()
async def list_goals(
    status: Optional[str] = None,
    goal_type: Optional[str] = None,
    area: Optional[str] = None,
    priority: Optional[str] = None,
    format: str = "json",
    limit: int = DEFAULT_LIMIT,
    verbose: bool = False,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Query goals from Notion with comprehensive filtering options.
    
    Returns structured goal data with progress tracking, target dates, and area relationships.
    Supports filtering by status, type, area, and priority.
    
    Args:
        status: Filter by goal status (e.g., 'Active', 'Completed', 'On Hold')
        goal_type: Filter by goal type ('Personal', 'Professional', 'Learning')
        area: Filter by area name or ID (e.g., 'Health', 'Career', 'Family')
        priority: Filter by priority level ('High', 'Medium', 'Low')
        format: Output format ('json', 'table', 'rich')
        limit: Maximum number of goals to return (1-100)
        verbose: Include detailed query information
        
    Returns:
        Structured goal data with metadata including progress and timeline info
    """
    try:
        if ctx:
            await ctx.info(f"Querying Notion goals with filters: status={status}, type={goal_type}, area={area}")
        
        # Validate parameters
        params = _validate_parameters(
            status=status, goal_type=goal_type, area=area,
            priority=priority, format=format, limit=limit, verbose=verbose
        )
        
        # Build CLI command
        base_cmd = [VTM_COMMAND, "list", "goals"]
        cmd = _build_cli_command(base_cmd, params)
        
        if ctx and params.get('verbose'):
            await ctx.debug(f"Executing command: {' '.join(cmd)}")
        
        # Execute command
        start_time = datetime.now()
        result = _execute_cli_command(cmd)
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Add execution time to metadata if present
        if isinstance(result, dict) and 'metadata' in result:
            result['metadata']['query_time_ms'] = round(execution_time, 2)
        
        if ctx:
            await ctx.info(f"Goals query completed in {execution_time:.2f}ms")
        
        return result
        
    except (ValidationError, CliExecutionError) as e:
        error_result = {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
                "suggestions": [
                    "Check goal_type values: 'Personal', 'Professional', 'Learning'",
                    "Verify status values: 'Active', 'Completed', 'On Hold'",
                    "Ensure vtm CLI has goals functionality enabled"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        if ctx:
            await ctx.error(f"Goals query failed: {str(e)}")
            
        return error_result
    
    except Exception as e:
        if ctx:
            await ctx.error(f"Unexpected error in goals query: {str(e)}")
            
        return {
            "success": False,
            "error": {
                "type": "UnexpectedError",
                "message": f"Unexpected error: {str(e)}"
            },
            "timestamp": datetime.now().isoformat()
        }

@mcp.tool()
async def list_notes(
    status: Optional[str] = None,
    note_type: Optional[str] = None,
    project: Optional[str] = None,
    area: Optional[str] = None,
    tags: Optional[str] = None,
    format: str = "json",
    limit: int = DEFAULT_LIMIT,
    verbose: bool = False,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Query notes from Notion with comprehensive filtering options.
    
    Returns structured note data with content, tags, and relationship information.
    Supports filtering by status, type, project, area, and tags.
    
    Args:
        status: Filter by note status (e.g., 'Draft', 'Published', 'Archived')
        note_type: Filter by note type ('Meeting', 'Research', 'General', 'Reference')
        project: Filter by project name or ID
        area: Filter by area name or ID
        tags: Filter by tags, comma-separated for multiple
        format: Output format ('json', 'table', 'rich')
        limit: Maximum number of notes to return (1-100)
        verbose: Include detailed query information
        
    Returns:
        Structured note data with metadata including word count and creation info
    """
    try:
        if ctx:
            await ctx.info(f"Querying Notion notes with filters: status={status}, type={note_type}, project={project}")
        
        # Validate parameters
        params = _validate_parameters(
            status=status, note_type=note_type, project=project, area=area,
            tags=tags, format=format, limit=limit, verbose=verbose
        )
        
        # Build CLI command
        base_cmd = [VTM_COMMAND, "list", "notes"]
        cmd = _build_cli_command(base_cmd, params)
        
        if ctx and params.get('verbose'):
            await ctx.debug(f"Executing command: {' '.join(cmd)}")
        
        # Execute command
        start_time = datetime.now()
        result = _execute_cli_command(cmd)
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Add execution time to metadata if present
        if isinstance(result, dict) and 'metadata' in result:
            result['metadata']['query_time_ms'] = round(execution_time, 2)
        
        if ctx:
            await ctx.info(f"Notes query completed in {execution_time:.2f}ms")
        
        return result
        
    except (ValidationError, CliExecutionError) as e:
        error_result = {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
                "suggestions": [
                    "Check note_type values: 'Meeting', 'Research', 'General', 'Reference'",
                    "Verify status values: 'Draft', 'Published', 'Archived'",
                    "Use comma-separated tags for multiple tag filters"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        if ctx:
            await ctx.error(f"Notes query failed: {str(e)}")
            
        return error_result
    
    except Exception as e:
        if ctx:
            await ctx.error(f"Unexpected error in notes query: {str(e)}")
            
        return {
            "success": False,
            "error": {
                "type": "UnexpectedError",
                "message": f"Unexpected error: {str(e)}"
            },
            "timestamp": datetime.now().isoformat()
        }

@mcp.tool()
async def list_events(
    status: Optional[str] = None,
    event_type: Optional[str] = None,
    date_range: Optional[str] = None,
    project: Optional[str] = None,
    priority: Optional[str] = None,
    format: str = "json",
    limit: int = DEFAULT_LIMIT,
    verbose: bool = False,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Query events/meetings from Notion with comprehensive filtering options.
    
    Returns structured event data with timing, attendees, and project relationships.
    Supports filtering by status, type, date range, project, and priority.
    
    Args:
        status: Filter by event status (e.g., 'Scheduled', 'Completed', 'Cancelled')
        event_type: Filter by event type ('Meeting', 'Call', 'Workshop', 'Review')
        date_range: Filter by date range (e.g., 'today', 'this-week', 'next-month')
        project: Filter by project name or ID
        priority: Filter by priority level ('High', 'Medium', 'Low')
        format: Output format ('json', 'table', 'rich')
        limit: Maximum number of events to return (1-100)
        verbose: Include detailed query information
        
    Returns:
        Structured event data with metadata including timing and participant info
    """
    try:
        if ctx:
            await ctx.info(f"Querying Notion events with filters: status={status}, type={event_type}, date_range={date_range}")
        
        # Validate parameters
        params = _validate_parameters(
            status=status, event_type=event_type, date_range=date_range,
            project=project, priority=priority, format=format, limit=limit, verbose=verbose
        )
        
        # Build CLI command
        base_cmd = [VTM_COMMAND, "list", "events"]
        cmd = _build_cli_command(base_cmd, params)
        
        if ctx and params.get('verbose'):
            await ctx.debug(f"Executing command: {' '.join(cmd)}")
        
        # Execute command
        start_time = datetime.now()
        result = _execute_cli_command(cmd)
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Add execution time to metadata if present
        if isinstance(result, dict) and 'metadata' in result:
            result['metadata']['query_time_ms'] = round(execution_time, 2)
        
        if ctx:
            await ctx.info(f"Events query completed in {execution_time:.2f}ms")
        
        return result
        
    except (ValidationError, CliExecutionError) as e:
        error_result = {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
                "suggestions": [
                    "Check event_type values: 'Meeting', 'Call', 'Workshop', 'Review'",
                    "Verify status values: 'Scheduled', 'Completed', 'Cancelled'",
                    "Use date_range values: 'today', 'this-week', 'next-month'"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        if ctx:
            await ctx.error(f"Events query failed: {str(e)}")
            
        return error_result
    
    except Exception as e:
        if ctx:
            await ctx.error(f"Unexpected error in events query: {str(e)}")
            
        return {
            "success": False,
            "error": {
                "type": "UnexpectedError",
                "message": f"Unexpected error: {str(e)}"
            },
            "timestamp": datetime.now().isoformat()
        }

@mcp.tool()
async def list_references(
    status: Optional[str] = None,
    reference_type: Optional[str] = None,
    category: Optional[str] = None,
    rating: Optional[int] = None,
    project: Optional[str] = None,
    area: Optional[str] = None,
    format: str = "json",
    limit: int = DEFAULT_LIMIT,
    verbose: bool = False,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Query references from Notion with comprehensive filtering options.
    
    Returns structured reference data with ratings, categories, and relationship information.
    Supports filtering by status, type, category, rating, project, and area.
    
    Args:
        status: Filter by reference status (e.g., 'Active', 'Archived', 'To Review')
        reference_type: Filter by type ('Article', 'Book', 'Video', 'Podcast', 'Tool', 'Website')
        category: Filter by category (e.g., 'Technical', 'Business', 'Personal Development')
        rating: Filter by minimum rating (1-5)
        project: Filter by related project name or ID
        area: Filter by related area name or ID
        format: Output format ('json', 'table', 'rich')
        limit: Maximum number of references to return (1-100)
        verbose: Include detailed query information
        
    Returns:
        Structured reference data with metadata including ratings and key insights
    """
    try:
        if ctx:
            await ctx.info(f"Querying Notion references with filters: status={status}, type={reference_type}, rating>={rating}")
        
        # Validate parameters
        params = _validate_parameters(
            status=status, reference_type=reference_type, category=category,
            rating=rating, project=project, area=area,
            format=format, limit=limit, verbose=verbose
        )
        
        # Build CLI command
        base_cmd = [VTM_COMMAND, "list", "references"]
        cmd = _build_cli_command(base_cmd, params)
        
        if ctx and params.get('verbose'):
            await ctx.debug(f"Executing command: {' '.join(cmd)}")
        
        # Execute command
        start_time = datetime.now()
        result = _execute_cli_command(cmd)
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Add execution time to metadata if present
        if isinstance(result, dict) and 'metadata' in result:
            result['metadata']['query_time_ms'] = round(execution_time, 2)
        
        if ctx:
            await ctx.info(f"References query completed in {execution_time:.2f}ms")
        
        return result
        
    except (ValidationError, CliExecutionError) as e:
        error_result = {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
                "suggestions": [
                    "Check reference_type values: 'Article', 'Book', 'Video', 'Podcast', 'Tool', 'Website'",
                    "Verify status values: 'Active', 'Archived', 'To Review'",
                    "Use rating values: 1-5 (minimum rating filter)"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        if ctx:
            await ctx.error(f"References query failed: {str(e)}")
            
        return error_result
    
    except Exception as e:
        if ctx:
            await ctx.error(f"Unexpected error in references query: {str(e)}")
            
        return {
            "success": False,
            "error": {
                "type": "UnexpectedError",
                "message": f"Unexpected error: {str(e)}"
            },
            "timestamp": datetime.now().isoformat()
        }

# =============================================================================
# CRUD OPERATIONS TOOLS
# =============================================================================

@mcp.tool()
async def delete_task(
    task_id: str,
    confirm: bool = False,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Delete (archive) a task in Notion.
    
    Permanently archives a task by its ID. This action cannot be undone easily.
    
    Args:
        task_id: The Notion page ID of the task to delete
        confirm: Safety confirmation flag (must be True)
        
    Returns:
        Success/failure status with task deletion details
    """
    try:
        if not confirm:
            return {
                "success": False,
                "error": {
                    "type": "ConfirmationRequired",
                    "message": "Task deletion requires confirmation. Set confirm=True to proceed.",
                    "suggestions": ["Add confirm=True parameter to confirm deletion"]
                },
                "timestamp": datetime.now().isoformat()
            }
        
        if ctx:
            await ctx.info(f"Deleting task: {task_id}")
        
        # Build CLI command for task deletion
        cmd = [VTM_COMMAND, "delete", "task", task_id, "--confirm"]
        
        if ctx:
            await ctx.debug(f"Executing command: {' '.join(cmd)}")
        
        # Execute command
        result = _execute_cli_command(cmd)
        
        if ctx:
            await ctx.info(f"Task deletion completed")
        
        return result
        
    except (ValidationError, CliExecutionError) as e:
        error_result = {
            "success": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
                "suggestions": [
                    "Verify the task_id is valid and exists",
                    "Ensure you have permission to delete tasks",
                    "Check Notion API connectivity"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        if ctx:
            await ctx.error(f"Task deletion failed: {str(e)}")
            
        return error_result
    
    except Exception as e:
        if ctx:
            await ctx.error(f"Unexpected error in task deletion: {str(e)}")
            
        return {
            "success": False,
            "error": {
                "type": "UnexpectedError",
                "message": f"Unexpected error: {str(e)}"
            },
            "timestamp": datetime.now().isoformat()
        }

@mcp.tool()
async def server_info(ctx: Optional[Context] = None) -> Dict[str, Any]:
    """
    Get information about the MCP server and its capabilities.
    
    Returns server status, available tools, and CLI version information.
    Useful for debugging and understanding server capabilities.
    
    Returns:
        Server information including status, tools, and version details
    """
    try:
        if ctx:
            await ctx.info("Retrieving server information")
        
        # Check CLI availability
        try:
            result = subprocess.run(
                [VTM_COMMAND, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            cli_available = result.returncode == 0
            cli_version = result.stdout.strip() if cli_available else None
        except Exception:
            cli_available = False
            cli_version = None
        
        server_info = {
            "success": True,
            "data": {
                "server_name": "Notion Task Management MCP Server",
                "version": "1.0.0",
                "status": "active",
                "cli_available": cli_available,
                "cli_version": cli_version,
                "available_tools": [
                    # Core List Tools
                    {
                        "name": "list_tasks",
                        "description": "Query tasks from Notion with filtering options"
                    },
                    {
                        "name": "list_projects", 
                        "description": "Query projects from Notion with progress information"
                    },
                    {
                        "name": "list_areas",
                        "description": "Query areas from Notion with summary information"
                    },
                    # New Entity List Tools
                    {
                        "name": "list_goals",
                        "description": "Query goals from Notion with progress tracking and area relationships"
                    },
                    {
                        "name": "list_notes",
                        "description": "Query notes from Notion with content, tags, and relationship information"
                    },
                    {
                        "name": "list_events",
                        "description": "Query events/meetings from Notion with timing and project relationships"
                    },
                    {
                        "name": "list_references",
                        "description": "Query references from Notion with ratings, categories, and relationships"
                    },
                    # CRUD Operations
                    {
                        "name": "delete_task",
                        "description": "Delete (archive) a task in Notion with confirmation"
                    },
                    # Server Management
                    {
                        "name": "server_info",
                        "description": "Get server status and capability information"
                    }
                ],
                "supported_formats": ["json", "table", "rich"],
                "max_limit": MAX_LIMIT,
                "default_limit": DEFAULT_LIMIT
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return server_info
        
    except Exception as e:
        return {
            "success": False,
            "error": {
                "type": "ServerError",
                "message": f"Failed to retrieve server info: {str(e)}"
            },
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Run the server
    mcp.run()