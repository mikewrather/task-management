#!/usr/bin/env python3
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