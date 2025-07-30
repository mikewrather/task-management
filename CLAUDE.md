# Task Management Project - Claude Integration Guide

## MCP (Model Context Protocol) Integration

### Critical: Claude CLI Usage for MCP

When executing Claude with MCP tools from Python subprocess:

**CORRECT approach:**
```python
# 1. Change to project directory (where .mcp.json is located)
os.chdir("/home/mike/development/task-management")

# 2. Run claude with the prompt using -p flag
cmd = [
    "claude",  # or full path
    "-p", prompt,  # -p takes the PROMPT, not project name!
    "--dangerously-skip-permissions",
    "--output-format", "json"
]
```

**INCORRECT approaches:**
- ❌ `claude -p task-management` (this treats "task-management" as a prompt)
- ❌ Running claude from wrong directory (won't find .mcp.json)
- ❌ Missing `--dangerously-skip-permissions` flag

### Why This Matters

The `.mcp.json` file in the project root configures MCP servers (agent-db, notion-task-management). Claude needs to:
1. Be run from the directory containing `.mcp.json`
2. Use `-p` flag with the actual prompt/instructions
3. Include `--dangerously-skip-permissions` for automated execution

### Current Implementation

The GraphRAG adapter and Claude processor correctly:
- Change to project directory before executing
- Pass the full prompt with instructions to `-p`
- Parse the JSON output which includes metadata wrapper

## Known Issues

1. **MCP Tool Performance**: Each `claude -p` subprocess call takes 30-60 seconds due to:
   - Claude initialization overhead
   - MCP server connection time
   - Tool execution time

2. **Timeouts**: Originally had timeouts that killed long-running MCP operations. Now set to `timeout=None` to let Claude finish.

## Testing MCP Tools

To test MCP tools are working:
```bash
cd /home/mike/development/task-management
claude -p "Use the mcp__agent-db__get_health_status tool and return the JSON result" --dangerously-skip-permissions --output-format json
```

This should return a JSON response with health status from the GraphRAG database.