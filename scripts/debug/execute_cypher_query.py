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
  "query": "MATCH (t:TASK) WHERE t.source = 'voice' AND t.created IS NOT NULL OPTIONAL MATCH (t)-[:BELONGS_TO]->(p:PROJECT) OPTIONAL MATCH (p)-[:BELONGS_TO]->(a:AREA) RETURN t.name as title, p.name as project_name, p.notion_id as project_id, a.name as area_name, t.contexts as contexts ORDER BY t.created DESC LIMIT 20",
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
        
        # Extract the actual content from the wrapper
        if "content" in response:
            content = response["content"]
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