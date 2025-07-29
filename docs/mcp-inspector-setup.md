# MCP Inspector Setup Guide

The **MCP Inspector** is the official visual testing tool for MCP servers, providing a comprehensive dashboard interface for testing and debugging your enhanced Notion MCP server.

## 🎛️ What is MCP Inspector?

**MCP Inspector** provides:
- **Visual Dashboard**: Interactive web interface for testing MCP tools
- **Real-time Testing**: Test all 9 tools in your Notion MCP server
- **Parameter Testing**: Interactive forms for tool parameters
- **Response Visualization**: Structured display of tool responses
- **Export Configurations**: Generate client configs for Claude Desktop, Cursor, etc.
- **Debug Support**: Detailed error messages and server communication logs

## 🚀 Quick Start Methods

### Method 1: Using MCP CLI (Recommended)
```bash
# Activate uv environment
source .venv/bin/activate

# Start inspector with MCP CLI
mcp dev notion_mcp_server.py
```

### Method 2: Using npx (Direct)
```bash
# Run our automated script
./scripts/start-mcp-inspector.sh

# Or manually with npx
npx @modelcontextprotocol/inspector .venv/bin/python notion_mcp_server.py
```

### Method 3: Manual Setup
```bash
# Install inspector globally
npm install -g @modelcontextprotocol/inspector

# Start inspector
mcp-inspector .venv/bin/python notion_mcp_server.py
```

## 🖥️ Dashboard Features

### Inspector Interface
- **URL**: http://localhost:6274 (Inspector UI)
- **Proxy**: http://localhost:6277 (MCP Proxy Server)
- **Binding**: localhost only (secure by default)

### Main Dashboard Tabs

#### 1. **Resources Tab**
- View available MCP resources
- Test resource access and permissions
- Validate resource metadata

#### 2. **Prompts Tab** 
- Test prompt templates
- Validate prompt parameters
- Preview prompt generation

#### 3. **Tools Tab** ⭐ **Most Important for Your Server**
- **All 9 Tools Listed**: Tasks, Projects, Areas, Goals, Notes, Events, References, Delete Task, Server Info
- **Interactive Testing**: Click "Run tool" button for each tool
- **Parameter Forms**: Fill in parameters like status, priority, limit, etc.
- **Live Results**: See JSON responses in real-time
- **Error Debugging**: Detailed error messages and suggestions

### Testing Your 9 Tools

#### Core List Tools
1. **list_tasks**
   - Test parameters: status, context, project, area, priority, energy
   - Example: status="In Progress", area="Work", limit=5

2. **list_projects**
   - Test parameters: status, area, priority
   - Example: status="Active", priority="High"

3. **list_areas**
   - Test parameters: status, priority
   - Example: status="Active"

#### New Entity Tools
4. **list_goals**
   - Test parameters: status, goal_type, area, priority
   - Example: goal_type="Personal", status="Active"

5. **list_notes**
   - Test parameters: status, note_type, project, area, tags
   - Example: note_type="Meeting", status="Published"

6. **list_events**
   - Test parameters: status, event_type, date_range, project
   - Example: event_type="Meeting", date_range="this-week"

7. **list_references**
   - Test parameters: status, reference_type, category, rating
   - Example: reference_type="Article", rating=4

#### CRUD Operations
8. **delete_task**
   - Test parameters: task_id, confirm
   - Example: task_id="abc123", confirm=true
   - ⚠️ **Safety**: Test with non-existent IDs first

#### Server Management
9. **server_info**
   - No parameters required
   - Shows all available tools and capabilities

## 🔧 Advanced Features

### Export Client Configurations
The Inspector provides convenient buttons to export server launch configurations for:
- **Claude Desktop**
- **Cursor IDE**
- **Other MCP Clients**

### Authentication Testing
- **Bearer Token Support**: Test SSE connections with authentication
- **Security Headers**: Validate proper authorization headers
- **Network Isolation**: localhost binding prevents external access

### Performance Monitoring  
- **Response Times**: View query execution times
- **Error Tracking**: Monitor tool failure rates
- **Parameter Validation**: Test edge cases and invalid inputs

## 🧪 Testing Workflow

### 1. Start the Inspector
```bash
# Quick start with our script
./scripts/start-mcp-inspector.sh

# Should show:
# ✅ MCP server imported successfully  
# 🔧 Total tools available: 9
# 🌐 Inspector will open at: http://localhost:6274
```

### 2. Open the Dashboard
- Navigate to http://localhost:6274
- You'll see the MCP Inspector interface

### 3. Test Your Tools
1. **Go to Tools Tab**
2. **Find your tool** (e.g., "list_goals")
3. **Fill in parameters** (e.g., status="Active")
4. **Click "Run tool"**
5. **View results** in the response panel

### 4. Debug Issues
- Check error messages in the response
- Verify parameter values match expected formats
- Test with different parameter combinations
- Monitor server logs for detailed debugging

## 🎯 Testing Your Enhanced Server

### Verify All New Features
```bash
# Test that all 9 tools are recognized
1. Open Inspector → Tools tab
2. Verify 9 tools listed:
   ✅ list_tasks, list_projects, list_areas (original)
   ✅ list_goals, list_notes, list_events, list_references (new)
   ✅ delete_task (new CRUD)
   ✅ server_info (updated)
```

### Test New Entity Tools
```bash
# Goals testing
- Run list_goals with goal_type="Personal"
- Run list_goals with status="Active", area="Health"

# Notes testing  
- Run list_notes with note_type="Meeting"
- Run list_notes with status="Published", tags="work,project"

# Events testing
- Run list_events with event_type="Meeting", date_range="today"

# References testing
- Run list_references with reference_type="Article", rating=4
```

### Test CRUD Operations
```bash
# Safe deletion testing
- Run delete_task with confirm=false (should fail with confirmation error)
- Run delete_task with invalid task_id and confirm=true (should fail gracefully)
```

## 🐛 Troubleshooting

### Common Issues

**Inspector won't start**
```bash
# Check Node.js availability
node --version

# Check MCP server works
python scripts/test-mcp-server.py

# Try alternative method
mcp dev notion_mcp_server.py
```

**Tools not appearing**
```bash
# Verify server info
python -c "
import sys; sys.path.insert(0, '.')
from notion_mcp_server import server_info
import asyncio
result = asyncio.run(server_info())
print(f'Tools: {len(result[\"data\"][\"available_tools\"])}')
"
```

**Connection errors**
```bash
# Check ports are available
netstat -an | grep 6274
netstat -an | grep 6277

# Restart with different ports if needed
npx @modelcontextprotocol/inspector --port 8080 .venv/bin/python notion_mcp_server.py
```

### Tool-Specific Issues

**vtm command not found**
```bash
# Verify CLI is working
source .venv/bin/activate
vtm --help
```

**Environment variables missing**
```bash
# Check .env configuration
cat .env | grep NOTION_
# Ensure all database IDs are set
```

## 📊 Benefits of Using MCP Inspector

### Development Benefits
- **🎯 Interactive Testing**: Test all tools without writing test code
- **🔍 Real-time Debugging**: See exactly what your server returns
- **📝 Parameter Validation**: Test edge cases and invalid inputs
- **⚡ Fast Iteration**: Make changes and test immediately

### Production Benefits
- **🚀 Pre-deployment Testing**: Verify everything works before release
- **📋 Client Configuration**: Export configs for easy client setup
- **🔒 Security Testing**: Validate authentication and authorization
- **📈 Performance Monitoring**: Track response times and error rates

## 🎉 Next Steps

1. **Start the Inspector**: Run `./scripts/start-mcp-inspector.sh`
2. **Test All Tools**: Go through each of the 9 tools systematically
3. **Validate Responses**: Ensure all responses match expected formats
4. **Export Configurations**: Generate client configs for production use
5. **Debug Any Issues**: Use the detailed error messages to fix problems

The MCP Inspector transforms MCP development from command-line testing to visual, interactive development with real-time feedback!