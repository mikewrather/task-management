# MCP Tool Definitions - Voice Task Management

## Overview

These are the detailed MCP tool definitions for exposing the Notion CLI tools to AI agents. Each tool wraps the corresponding `vtm list` command with proper validation and structured outputs.

## Tool 1: List Tasks

### Definition
```json
{
  "name": "list_tasks",
  "description": "Query tasks from Notion with comprehensive filtering options. Returns structured task data with status, priority, context, and project information.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "status": {
        "type": "string",
        "description": "Filter by task status. Common values: 'Not started', 'In progress', 'Done'",
        "examples": ["Not started", "In progress", "Done", "Next Action"]
      },
      "context": {
        "type": "string", 
        "description": "Filter by context (comma-separated for multiple). Common values: 'voice', 'Computer', 'Meeting', 'Reading'",
        "examples": ["voice", "Computer,Meeting", "Reading"]
      },
      "project": {
        "type": "string",
        "description": "Filter by project name or ID. Supports partial matching.",
        "examples": ["Voice Task Management", "Personal Development"]
      },
      "area": {
        "type": "string",
        "description": "Filter by area name or ID. Common values: 'Personal', 'Work', 'Health'",
        "examples": ["Personal", "Work", "Health", "Finance"]
      },
      "priority": {
        "type": "string",
        "description": "Filter by priority level",
        "enum": ["High", "Medium", "Low"],
        "examples": ["High", "Medium", "Low"]
      },
      "energy": {
        "type": "string",
        "description": "Filter by energy level required for task",
        "enum": ["High", "Medium", "Low"],
        "examples": ["High", "Medium", "Low"]
      },
      "format": {
        "type": "string",
        "enum": ["json", "table", "rich"],
        "default": "json",
        "description": "Output format: 'json' for structured data, 'table' for tabular display, 'rich' for formatted console output"
      },
      "limit": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "default": 50,
        "description": "Maximum number of tasks to return"
      },
      "verbose": {
        "type": "boolean",
        "default": false,
        "description": "Include detailed query information and performance metrics"
      }
    },
    "required": [],
    "additionalProperties": false
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": {
        "type": "boolean",
        "description": "Whether the query executed successfully"
      },
      "data": {
        "type": "array",
        "description": "Array of task objects",
        "items": {
          "type": "object",
          "properties": {
            "id": {"type": "string", "description": "Notion task ID"},
            "title": {"type": "string", "description": "Task name/title"},
            "status": {"type": "string", "description": "Current task status"},
            "priority": {"type": "string", "description": "Task priority level"},
            "energy": {"type": "string", "description": "Energy level required"},
            "contexts": {
              "type": "array",
              "items": {"type": "string"},
              "description": "List of contexts associated with task"
            },
            "project": {"type": "string", "description": "Associated project name"},
            "area": {"type": "string", "description": "Associated area name"},
            "created_time": {"type": "string", "format": "date-time"},
            "last_edited_time": {"type": "string", "format": "date-time"},
            "url": {"type": "string", "format": "uri", "description": "Direct link to task in Notion"}
          },
          "required": ["id", "title", "status"]
        }
      },
      "metadata": {
        "type": "object",
        "properties": {
          "total_count": {"type": "integer", "description": "Number of tasks returned"},
          "query_time_ms": {"type": "number", "description": "Query execution time in milliseconds"},
          "filters_applied": {
            "type": "object",
            "description": "Summary of filters that were applied"
          },
          "cached": {"type": "boolean", "description": "Whether results were served from cache"}
        }
      },
      "timestamp": {"type": "string", "format": "date-time", "description": "When the query was executed"}
    },
    "required": ["success", "data", "metadata"]
  }
}
```

### CLI Command Mapping
```bash
vtm list tasks [--status STATUS] [--context CONTEXT] [--project PROJECT] 
               [--area AREA] [--priority PRIORITY] [--energy ENERGY] 
               [--format FORMAT] [--limit LIMIT] [--verbose]
```

## Tool 2: List Projects

### Definition
```json
{
  "name": "list_projects", 
  "description": "Query projects from Notion with filtering and progress information. Returns project data with status, completion metrics, and associated areas.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "status": {
        "type": "string",
        "description": "Filter by project status. Common values: 'Not started', 'In Progress', 'Done', 'On Hold'",
        "examples": ["Not started", "In Progress", "Done", "On Hold"]
      },
      "area": {
        "type": "string",
        "description": "Filter by area name or ID. Only show projects within specified area.",
        "examples": ["Personal", "Work", "Health", "Finance"]
      },
      "priority": {
        "type": "string", 
        "description": "Filter by priority level",
        "enum": ["High", "Medium", "Low"],
        "examples": ["High", "Medium", "Low"]
      },
      "active_only": {
        "type": "boolean",
        "default": false,
        "description": "Show only active projects (In Progress status and not archived)"
      },
      "format": {
        "type": "string",
        "enum": ["json", "table", "rich"],
        "default": "json", 
        "description": "Output format: 'json' for structured data, 'table' for tabular display, 'rich' for formatted console output"
      },
      "limit": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "default": 50,
        "description": "Maximum number of projects to return"
      },
      "verbose": {
        "type": "boolean",
        "default": false,
        "description": "Include detailed query information and performance metrics"
      }
    },
    "required": [],
    "additionalProperties": false
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": {
        "type": "boolean",
        "description": "Whether the query executed successfully"
      },
      "data": {
        "type": "array",
        "description": "Array of project objects",
        "items": {
          "type": "object", 
          "properties": {
            "id": {"type": "string", "description": "Notion project ID"},
            "name": {"type": "string", "description": "Project name/title"},
            "status": {"type": "string", "description": "Current project status"},
            "priority": {"type": "string", "description": "Project priority level"},
            "area": {"type": "string", "description": "Associated area name"},
            "completion_percentage": {
              "type": "number",
              "minimum": 0,
              "maximum": 100,
              "description": "Project completion percentage (0-100)"
            },
            "task_count": {"type": "integer", "description": "Total number of tasks in project"},
            "completed_tasks": {"type": "integer", "description": "Number of completed tasks"},
            "created_time": {"type": "string", "format": "date-time"},
            "last_edited_time": {"type": "string", "format": "date-time"},
            "url": {"type": "string", "format": "uri", "description": "Direct link to project in Notion"}
          },
          "required": ["id", "name", "status"]
        }
      },
      "metadata": {
        "type": "object",
        "properties": {
          "total_count": {"type": "integer", "description": "Number of projects returned"},
          "query_time_ms": {"type": "number", "description": "Query execution time in milliseconds"},
          "filters_applied": {
            "type": "object",
            "description": "Summary of filters that were applied"
          },
          "cached": {"type": "boolean", "description": "Whether results were served from cache"}
        }
      },
      "timestamp": {"type": "string", "format": "date-time", "description": "When the query was executed"}
    },
    "required": ["success", "data", "metadata"]
  }
}
```

### CLI Command Mapping
```bash
vtm list projects [--status STATUS] [--area AREA] [--priority PRIORITY] 
                  [--active-only] [--format FORMAT] [--limit LIMIT] [--verbose]
```

## Tool 3: List Areas

### Definition
```json
{
  "name": "list_areas",
  "description": "Query areas from Notion with project and task summary information. Returns area data with status, progress metrics, and associated counts.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "status": {
        "type": "string",
        "description": "Filter by area status. Common values: 'Active', 'On Hold', 'Archived'",
        "examples": ["Active", "On Hold", "Archived"]
      },
      "priority": {
        "type": "string",
        "description": "Filter by priority level",
        "enum": ["High", "Medium", "Low"],
        "examples": ["High", "Medium", "Low"]
      },
      "format": {
        "type": "string",
        "enum": ["json", "table", "rich"],
        "default": "json",
        "description": "Output format: 'json' for structured data, 'table' for tabular display, 'rich' for formatted console output"
      },
      "limit": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "default": 50,
        "description": "Maximum number of areas to return"
      },
      "verbose": {
        "type": "boolean",
        "default": false,
        "description": "Include detailed query information and performance metrics"
      }
    },
    "required": [],
    "additionalProperties": false
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": {
        "type": "boolean",
        "description": "Whether the query executed successfully"
      },
      "data": {
        "type": "array",
        "description": "Array of area objects",
        "items": {
          "type": "object",
          "properties": {
            "id": {"type": "string", "description": "Notion area ID"},
            "name": {"type": "string", "description": "Area name/title"},
            "status": {"type": "string", "description": "Current area status"},
            "priority": {"type": "string", "description": "Area priority level"},
            "completion_percentage": {
              "type": "number",
              "minimum": 0,
              "maximum": 100,
              "description": "Area completion percentage (0-100)"
            },
            "project_count": {"type": "integer", "description": "Number of projects in this area"},
            "task_count": {"type": "integer", "description": "Total number of tasks in this area"},
            "completed_projects": {"type": "integer", "description": "Number of completed projects"},
            "completed_tasks": {"type": "integer", "description": "Number of completed tasks"},
            "created_time": {"type": "string", "format": "date-time"},
            "last_edited_time": {"type": "string", "format": "date-time"},
            "url": {"type": "string", "format": "uri", "description": "Direct link to area in Notion"}
          },
          "required": ["id", "name", "status"]
        }
      },
      "metadata": {
        "type": "object", 
        "properties": {
          "total_count": {"type": "integer", "description": "Number of areas returned"},
          "query_time_ms": {"type": "number", "description": "Query execution time in milliseconds"},
          "filters_applied": {
            "type": "object",
            "description": "Summary of filters that were applied"
          },
          "cached": {"type": "boolean", "description": "Whether results were served from cache"}
        }
      },
      "timestamp": {"type": "string", "format": "date-time", "description": "When the query was executed"}
    },
    "required": ["success", "data", "metadata"]
  }
}
```

### CLI Command Mapping
```bash
vtm list areas [--status STATUS] [--priority PRIORITY] 
               [--format FORMAT] [--limit LIMIT] [--verbose]
```

## Error Handling

All tools support comprehensive error handling with structured error responses:

```json
{
  "success": false,
  "error": {
    "type": "ValidationError | ExecutionError | NotionAPIError",
    "message": "Human-readable error description",
    "details": "Additional technical details",
    "suggestions": ["Suggested fixes or next steps"]
  },
  "timestamp": "2025-07-26T09:15:00Z"
}
```

## Usage Examples

### AI Agent Interactions

**Example 1: Find High Priority Tasks**
```
Agent Query: "Show me all high priority tasks that are in progress"
MCP Call: list_tasks(status="In progress", priority="High", format="json")
```

**Example 2: Review Work Projects**
```
Agent Query: "What work projects do I have and what's their status?"
MCP Call: list_projects(area="Work", format="json", verbose=true)
```

**Example 3: Area Overview**
```
Agent Query: "Give me an overview of all my areas with completion rates"
MCP Call: list_areas(format="json", verbose=true)
```

## Performance Considerations

- **Query Time**: All tools include execution time metrics
- **Caching**: Results can be cached for repeated queries
- **Limits**: Configurable result limits prevent overwhelming responses
- **Filtering**: Server-side filtering reduces data transfer
- **Validation**: Input validation prevents invalid Notion API calls

## Security Features

- **Input Sanitization**: All parameters are validated before CLI execution
- **Command Injection Prevention**: Subprocess calls use safe parameter passing
- **Error Masking**: Sensitive information is filtered from error responses
- **Access Control**: Can be extended with OAuth authentication

*Last Updated: 2025-07-26*