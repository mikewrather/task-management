# Enhanced MCP Server Guide

The Voice Task Manager MCP (Model Context Protocol) server provides AI agents with structured access to your Notion workspace through comprehensive CRUD operations and advanced querying capabilities.

## 🚀 Recent Enhancements

### ✅ Completed Updates
- **uv Compatibility**: Updated to work with uv virtual environment (`.venv/bin/python`)
- **4 New Entity Types**: Added Goals, Notes, Events, and References support
- **CRUD Operations**: Added delete functionality with confirmation safety
- **Enhanced Filtering**: Advanced filtering options for all entity types
- **Performance Tracking**: Query execution time monitoring
- **Comprehensive Error Handling**: Detailed error messages and suggestions

### 📊 MCP Server Capabilities

**Total Tools Available: 9**
- **4 Core List Tools**: Tasks, Projects, Areas, Server Info
- **4 New Entity Tools**: Goals, Notes, Events, References  
- **1 CRUD Operation**: Task Deletion (with more coming)

## 🛠️ Available Tools

### Core List Tools

#### `list_tasks`
Query tasks from Notion with comprehensive filtering options.

**Parameters:**
- `status`: Filter by task status (e.g., 'Not started', 'In progress', 'Done')
- `context`: Filter by context, comma-separated (e.g., 'voice,Computer')
- `project`: Filter by project name or ID
- `area`: Filter by area name or ID (e.g., 'Personal', 'Work')
- `priority`: Filter by priority level ('High', 'Medium', 'Low')
- `energy`: Filter by energy level required ('High', 'Medium', 'Low')
- `format`: Output format ('json', 'table', 'rich')
- `limit`: Maximum number of tasks to return (1-100)
- `verbose`: Include detailed query information

#### `list_projects`
Query projects from Notion with progress information.

**Parameters:**
- `status`: Filter by project status
- `area`: Filter by area name or ID
- `priority`: Filter by priority level
- `format`: Output format ('json', 'table', 'rich')
- `limit`: Maximum number of projects (1-100)
- `verbose`: Include detailed query information

#### `list_areas`
Query areas from Notion with summary information.

**Parameters:**
- `status`: Filter by area status
- `priority`: Filter by priority level
- `format`: Output format ('json', 'table', 'rich')
- `limit`: Maximum number of areas (1-100)
- `verbose`: Include detailed query information

### New Entity Tools

#### `list_goals`
Query goals from Notion with progress tracking and area relationships.

**Parameters:**
- `status`: Filter by goal status ('Active', 'Completed', 'On Hold')
- `goal_type`: Filter by goal type ('Personal', 'Professional', 'Learning')
- `area`: Filter by area name or ID ('Health', 'Career', 'Family')
- `priority`: Filter by priority level ('High', 'Medium', 'Low')
- `format`: Output format ('json', 'table', 'rich')
- `limit`: Maximum number of goals (1-100)
- `verbose`: Include detailed query information

**Returns:** Structured goal data with progress and timeline info

#### `list_notes`
Query notes from Notion with content, tags, and relationship information.

**Parameters:**
- `status`: Filter by note status ('Draft', 'Published', 'Archived')
- `note_type`: Filter by note type ('Meeting', 'Research', 'General', 'Reference')
- `project`: Filter by project name or ID
- `area`: Filter by area name or ID
- `tags`: Filter by tags, comma-separated for multiple
- `format`: Output format ('json', 'table', 'rich')
- `limit`: Maximum number of notes (1-100)
- `verbose`: Include detailed query information

**Returns:** Structured note data with word count and creation info

#### `list_events`
Query events/meetings from Notion with timing and project relationships.

**Parameters:**
- `status`: Filter by event status ('Scheduled', 'Completed', 'Cancelled')
- `event_type`: Filter by event type ('Meeting', 'Call', 'Workshop', 'Review')
- `date_range`: Filter by date range ('today', 'this-week', 'next-month')
- `project`: Filter by project name or ID
- `priority`: Filter by priority level ('High', 'Medium', 'Low')
- `format`: Output format ('json', 'table', 'rich')
- `limit`: Maximum number of events (1-100)
- `verbose`: Include detailed query information

**Returns:** Structured event data with timing and participant info

#### `list_references`
Query references from Notion with ratings, categories, and relationships.

**Parameters:**
- `status`: Filter by reference status ('Active', 'Archived', 'To Review')
- `reference_type`: Filter by type ('Article', 'Book', 'Video', 'Podcast', 'Tool', 'Website')
- `category`: Filter by category ('Technical', 'Business', 'Personal Development')
- `rating`: Filter by minimum rating (1-5)
- `project`: Filter by related project name or ID
- `area`: Filter by related area name or ID
- `format`: Output format ('json', 'table', 'rich')
- `limit`: Maximum number of references (1-100)
- `verbose`: Include detailed query information

**Returns:** Structured reference data with ratings and key insights

### CRUD Operations

#### `delete_task`
Delete (archive) a task in Notion with confirmation safety.

**Parameters:**
- `task_id`: The Notion page ID of the task to delete (required)
- `confirm`: Safety confirmation flag (must be True) (required)

**Returns:** Success/failure status with task deletion details

**Safety Features:**
- Requires explicit `confirm=True` parameter
- Archives rather than permanently deletes
- Detailed error messages and suggestions
- Comprehensive logging

### Server Management

#### `server_info`
Get information about the MCP server and its capabilities.

**Returns:**
- Server name, version, and status
- CLI availability and version
- Complete list of available tools
- Supported formats and limits
- Performance and configuration info

## 🔧 Setup and Usage

### Prerequisites
- Voice Task Manager installed with uv: `uv pip install -e ".[mcp]"`
- Notion API credentials configured in `.env`
- vtm CLI commands working: `vtm --help`

### Running the Server

#### Method 1: Direct Execution
```bash
# Activate uv environment
source .venv/bin/activate

# Run MCP server
python notion_mcp_server.py
```

#### Method 2: MCP Client Configuration
Add to your MCP client configuration:
```json
{
  "mcpServers": {
    "notion-task-management": {
      "command": "/path/to/task-management/.venv/bin/python",
      "args": ["/path/to/task-management/notion_mcp_server.py"]
    }
  }
}
```

### Testing the Server
```bash
# Test server functionality
python scripts/test-mcp-server.py
```

## 📊 Performance Features

### Query Performance Tracking
- Execution time monitoring for all operations
- Metadata includes query time in milliseconds
- Performance stats in verbose mode

### Error Handling
- Comprehensive error categorization
- Detailed error messages with suggestions
- Fallback handling for CLI failures
- Input validation with helpful feedback

### Safety Features
- Confirmation required for destructive operations
- Input parameter validation
- Rate limiting awareness
- Timeout handling for long operations

## 🔗 Integration Examples

### Basic Query
```python
# Query active goals in Health area
result = await list_goals(
    status="Active",
    area="Health",
    limit=10,
    verbose=True
)
```

### Advanced Filtering
```python
# Query high-priority meetings for this week
events = await list_events(
    event_type="Meeting",
    priority="High", 
    date_range="this-week",
    format="json"
)
```

### Safe Deletion
```python
# Delete a task with confirmation
result = await delete_task(
    task_id="abc123-def456-ghi789",
    confirm=True
)
```

## 📈 Recent Improvements

### uv Migration Benefits
- **10-40x faster** dependency installation and environment setup
- **Consistent environments** with lock files
- **Modern Python tooling** with uv package management
- **Updated shebang** pointing to `.venv/bin/python`

### Enhanced Functionality
- **4 new entity types** with full querying support
- **Advanced filtering** options for all entities
- **Performance monitoring** built into all operations
- **Comprehensive error handling** with actionable suggestions
- **Safety confirmations** for destructive operations

### Developer Experience
- **Test script** for easy verification (`scripts/test-mcp-server.py`)
- **Detailed documentation** with examples
- **Comprehensive tool descriptions** in server_info
- **Improved error messages** with specific suggestions

## 🚧 Roadmap

### Planned Enhancements
- **Full CRUD Support**: Create, update operations for all entity types
- **Batch Operations**: Multi-entity operations in single calls
- **Advanced Search**: Full-text search across all entities
- **Relationship Management**: Create and manage entity relationships
- **Webhook Support**: Real-time notifications from Notion changes

### Future Entity Support
- **Templates**: Project and task templates
- **Workflows**: Custom automation workflows  
- **Analytics**: Usage statistics and productivity metrics
- **Integrations**: Extended third-party service connections

## 🐛 Troubleshooting

### Common Issues

**"vtm command not found"**
```bash
# Ensure vtm is installed and environment is activated
source .venv/bin/activate
vtm --help
```

**"Permission denied" on server startup**
```bash
# Check shebang path and make executable
chmod +x notion_mcp_server.py
head -1 notion_mcp_server.py  # Should show correct Python path
```

**"Import errors" during testing**
```bash
# Verify MCP dependencies are installed
uv pip install -e ".[mcp]"
python -c "import mcp; print('MCP available')"
```

**Tool execution failures**
- Verify `.env` configuration with all required database IDs
- Check Notion API connectivity: `vtm list tasks --limit 1`
- Ensure database permissions in Notion workspace

## 📚 Resources

- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Voice Task Manager CLI Reference](../README.md)
- [uv Package Manager](https://docs.astral.sh/uv/)