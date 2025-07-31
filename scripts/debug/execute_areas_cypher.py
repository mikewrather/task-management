#!/usr/bin/env python3
"""Execute a Cypher query via Claude CLI with MCP"""

import subprocess
import json
import os

# Change to project directory where .mcp.json is located
os.chdir("/home/mike/development/task-management")

# Build the prompt for Claude
prompt = """Use the mcp__agent-db__execute_cypher tool with these exact parameters:
{
  "query": "MATCH (a:AREA) RETURN a.notion_id as area_id, a.name as name",
  "parameters": {}
}

Return ONLY the raw JSON result from the tool, with no additional text or formatting."""

# Execute claude command
cmd = [
    "/home/mike/.claude/local/claude",
    "-p", prompt,
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=None)
    
    if result.returncode == 0:
        # Parse the JSON response
        response = json.loads(result.stdout)
        
        # Extract the actual result from the wrapper
        if "result" in response:
            content = response["result"]
            # Try to parse the content as JSON
            try:
                data = json.loads(content)
                print(json.dumps(data))
            except json.JSONDecodeError:
                print(content)
        else:
            print(json.dumps(response))
    else:
        print(f"Error: {result.stderr}")
        
except Exception as e:
    print(f"Error executing command: {e}")