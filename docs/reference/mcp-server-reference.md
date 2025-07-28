# MCP Server Quick Reference

## Overview

Quick reference for the Notion Task Management MCP Server tools and commands.

## Tools Summary

| Tool | Purpose | Common Parameters |
|------|---------|-------------------|
| `list_tasks` | Query tasks with filters | `status`, `area`, `project`, `priority` |
| `list_projects` | Query projects with progress | `area`, `status`, `active_only` |
| `list_areas` | Query areas with summaries | `status`, `priority` |
| `server_info` | Server status and capabilities | None |

## Quick Commands

### Development

```bash
# Start MCP Inspector for testing
mcp dev notion_mcp_server.py

# Run test suite
python test_mcp_server.py

# Install for Claude Desktop
mcp install notion_mcp_server.py --name "Notion Tasks"
```

### Common Filters

**Task Filters:**
- Status: `"Not started"`, `"In progress"`, `"Done"`, `"Inbox"`
- Priority: `"High"`, `"Medium"`, `"Low"`
- Energy: `"High"`, `"Medium"`, `"Low"`
- Context: `"voice"`, `"Computer"`, `"Meeting"`, `"Reading"`
- Area: `"Personal"`, `"Work"`, `"Health"`, `"Finance"`

**Project Filters:**
- Status: `"Not started"`, `"In Progress"`, `"Done"`, `"On Hold"`
- `active_only: true` - Only active, non-archived projects

**Output Formats:**
- `"json"` - Structured data (recommended for AI)
- `"table"` - Tabular text format
- `"rich"` - Formatted console output

## Example AI Queries

### Task Management

```
"Show me all voice tasks that need attention"
→ list_tasks(context="voice", status="In progress")

"What high priority work tasks do I have?"
→ list_tasks(area="Work", priority="High")

"List all tasks in my Personal area"
→ list_tasks(area="Personal", limit=20)
```

### Project Tracking

```
"What projects are currently active?"
→ list_projects(active_only=true)

"Show me work projects and their progress"
→ list_projects(area="Work", verbose=true)

"List all projects with high priority"
→ list_projects(priority="High")
```

### Area Overview

```
"Give me an overview of all my areas"
→ list_areas(verbose=true)

"Show me areas that need attention"
→ list_areas(status="Active", priority="High")
```

### System Status

```
"Is the server working properly?"
→ server_info()
```

## Response Format

All tools return structured JSON responses:

```json
{
  "success": true,
  "data": [...],
  "metadata": {
    "total_count": 10,
    "query_time_ms": 245.3,
    "filters_applied": {...},
    "cached": false
  },
  "timestamp": "2025-07-26T09:30:00Z"
}
```

## Error Responses

```json
{
  "success": false,
  "error": {
    "type": "ValidationError",
    "message": "Invalid parameter value",
    "suggestions": ["Check parameter format", "Try simpler query"]
  },
  "timestamp": "2025-07-26T09:30:00Z"
}
```

## Parameter Limits

- `limit`: 1-100 (default: 50)
- String parameters: Alphanumeric + spaces, commas, hyphens, underscores
- Timeout: 30 seconds per query
- Context multiple values: Comma-separated (e.g., `"voice,Computer"`)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "CLI command failed" | Check `vtm` installation and Notion API credentials |
| "JSONDecodeError" | Verify CLI output format with `vtm list tasks --format=json` |
| "Module not found" | Activate virtual environment and check MCP installation |
| Slow responses | Check Notion API performance, reduce `limit` parameter |

## File Locations

- **Server**: `/path/to/task-management/notion_mcp_server.py`
- **Test Script**: `/path/to/task-management/test_mcp_server.py`  
- **Requirements**: `/path/to/task-management/mcp-requirements.txt`
- **Setup Guide**: `docs/guides/setup/mcp-server-setup.md`
- **Architecture**: `docs/architecture/mcp-server-design.md`

## Configuration Files

**Claude Desktop Config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "notion-tasks": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/notion_mcp_server.py"]
    }
  }
}
```

## Development URLs

- **MCP Inspector**: `http://localhost:6274` (when running `mcp dev`)
- **HTTP Server**: `http://localhost:8000/mcp` (production mode)

*Last Updated: 2025-07-26*