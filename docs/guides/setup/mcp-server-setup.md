# MCP Server Setup Guide

## Overview

This guide covers setting up and using the Notion Task Management MCP Server, which exposes the `vtm` CLI tools to AI agents through the Model Context Protocol.

## Prerequisites

### System Requirements
- Python 3.11 or higher
- Virtual environment with Voice Task Manager package installed
- Working `vtm` CLI with Notion API access
- MCP-compatible client (Claude Desktop, VS Code with MCP support, etc.)

### Dependencies
- `mcp[cli]>=1.12.0` - Model Context Protocol framework
- Existing Voice Task Manager installation

## Installation

### 1. Install MCP Dependencies

From the project root directory:

```bash
# Activate your virtual environment
source venv/bin/activate

# Install MCP with CLI tools
pip install "mcp[cli]>=1.12.0"
```

### 2. Verify Installation

Test that both the CLI and MCP components are working:

```bash
# Test CLI functionality
vtm list tasks --format=json --limit=1

# Test MCP installation
mcp --version

# Test the MCP server
python test_mcp_server.py
```

Expected output from test:
```
🚀 Testing Notion MCP Server Tools
✅ Server info tool working
✅ List tasks tool working  
✅ List projects tool working
✅ List areas tool working
📊 Test Summary: Passed: 4/4, Success Rate: 100.0%
```

## Development Testing

### MCP Inspector

Use the MCP Inspector for development and debugging:

```bash
# Start server with inspector
source venv/bin/activate
mcp dev notion_mcp_server.py
```

This opens a web interface at `http://localhost:6274` where you can:
- Test tool calls interactively
- View tool schemas and documentation
- Debug parameter validation
- Monitor server logs

### Direct Testing

Test individual tools programmatically:

```bash
# Run the test suite
python test_mcp_server.py

# Test specific functionality
python -c "
import asyncio
from notion_mcp_server import list_tasks
result = asyncio.run(list_tasks(area='Work', limit=5))
print('Success:', result.get('success'))
print('Task count:', len(result.get('data', [])))
"
```

## Claude Desktop Integration

### 1. Install Server in Claude Desktop

```bash
# Install for Claude Desktop
source venv/bin/activate
mcp install notion_mcp_server.py --name "Notion Task Management"
```

### 2. Manual Configuration

Alternatively, configure manually by editing Claude Desktop's configuration:

**Location**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "notion-tasks": {
      "command": "/path/to/your/venv/bin/python",
      "args": ["/path/to/task-management/notion_mcp_server.py"],
      "env": {
        "UV_INDEX": ""
      }
    }
  }
}
```

### 3. Restart Claude Desktop

After configuration, restart Claude Desktop to load the server.

## Production Deployment

### HTTP Server Mode

For production deployment with multiple clients:

```bash
# Run as HTTP server
source venv/bin/activate
python notion_mcp_server.py --transport=streamable-http --port=8000
```

### Systemd Service (Linux)

Create a systemd service file at `/etc/systemd/system/notion-mcp.service`:

```ini
[Unit]
Description=Notion MCP Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/task-management
Environment=PATH=/path/to/task-management/venv/bin
ExecStart=/path/to/task-management/venv/bin/python notion_mcp_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable notion-mcp
sudo systemctl start notion-mcp
sudo systemctl status notion-mcp
```

## Usage

### Available Tools

The MCP server exposes 4 tools:

1. **`list_tasks`** - Query tasks with filtering options
2. **`list_projects`** - Query projects with progress information  
3. **`list_areas`** - Query areas with summary information
4. **`server_info`** - Get server status and capabilities

### Tool Parameters

#### list_tasks
- `status`: Filter by status ("Not started", "In progress", "Done")
- `context`: Filter by context ("voice", "Computer", etc.)
- `project`: Filter by project name
- `area`: Filter by area name ("Personal", "Work", etc.)
- `priority`: Filter by priority ("High", "Medium", "Low")
- `energy`: Filter by energy level ("High", "Medium", "Low")
- `format`: Output format ("json", "table", "rich")
- `limit`: Maximum results (1-100, default: 50)
- `verbose`: Include detailed information

#### list_projects
- `status`: Filter by status
- `area`: Filter by area name
- `priority`: Filter by priority level
- `active_only`: Show only active projects
- `format`: Output format
- `limit`: Maximum results
- `verbose`: Include detailed information

#### list_areas
- `status`: Filter by status
- `priority`: Filter by priority level
- `format`: Output format
- `limit`: Maximum results
- `verbose`: Include detailed information

### Example AI Interactions

**Query high priority tasks:**
```
User: "Show me all high priority tasks that are in progress"
→ Calls: list_tasks(priority="High", status="In progress", format="json")
```

**Project overview:**
```
User: "What work projects do I have and what's their status?"
→ Calls: list_projects(area="Work", format="json", verbose=true)
```

**Area summary:**
```
User: "Give me an overview of all my areas with completion rates"
→ Calls: list_areas(format="json", verbose=true)
```

## Troubleshooting

### Common Issues

**1. "CLI command failed" errors**
- Verify `vtm` CLI is accessible in PATH
- Check Notion API credentials are configured
- Test CLI directly: `vtm list tasks --format=json --limit=1`

**2. "JSONDecodeError" messages**
- This indicates the CLI output format changed
- Check for log messages mixed with JSON output
- Run the debug script: `python debug_cli_output.py`

**3. "Module not found" errors**
- Ensure virtual environment is activated
- Verify MCP installation: `pip show mcp`
- Check Python path includes project directory

**4. Server connection timeouts**
- Increase timeout values in server configuration
- Check network connectivity to Notion API
- Monitor server logs for performance issues

### Debug Commands

```bash
# Test CLI output format
vtm list tasks --format=json --limit=1

# Check server tool schemas
python -c "
from notion_mcp_server import mcp
tools = mcp.get_tools()
for tool in tools:
    print(f'{tool.name}: {tool.description}')
"

# Validate server functionality
python test_mcp_server.py

# Debug JSON parsing
python debug_cli_output.py
```

### Performance Monitoring

Monitor server performance and usage:

```bash
# Server resource usage
ps aux | grep notion_mcp_server

# Test response times
time python -c "
import asyncio
from notion_mcp_server import list_tasks
asyncio.run(list_tasks(limit=1))
"

# Check log files for errors
tail -f ~/.notion_mcp_server.log  # if logging is configured
```

## Security Considerations

### Access Control
- The server inherits Notion API permissions from CLI configuration
- No additional authentication is implemented by default
- For production use, consider adding OAuth authentication

### Network Security
- Default stdio transport is secure for local use
- HTTP transport should use HTTPS in production
- Consider firewall rules for network-accessible deployments

### Data Privacy
- Server does not store or cache Notion data
- All queries are passed through to Notion API
- Logs may contain task titles and metadata

## Next Steps

After successful setup:

1. **Test Integration**: Verify tools work in your AI client
2. **Configure Filters**: Set up common query patterns for your workflow
3. **Monitor Performance**: Check response times and error rates
4. **Backup Configuration**: Save MCP server configs and credentials
5. **Explore Extensions**: Consider adding more CLI commands as tools

For advanced usage and customization, see the [MCP Server Design](../../architecture/mcp-server-design.md) documentation.

*Last Updated: 2025-07-26*