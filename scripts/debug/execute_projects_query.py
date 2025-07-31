#!/usr/bin/env python3
import os
import sys
import subprocess
import json

# Change to project directory
os.chdir("/home/mike/development/task-management")

# Construct command
cmd = [
    "/home/mike/.claude/local/claude",
    "-p", """Use the mcp__agent-db__execute_cypher tool with these exact parameters:
{
  "query": "MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA) RETURN p.notion_id as project_id, p.name as name, a.notion_id as area_id, a.name as area_name",
  "parameters": {}
}

Return ONLY the raw JSON result from the tool execution, with no additional text or formatting.""",
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=None)
    response = json.loads(result.stdout)
    # Extract the actual tool result from Claude's response
    if "content" in response:
        print(response["content"])
    else:
        print(json.dumps(response))
except subprocess.CalledProcessError as e:
    print(f"Error: {e.stderr}", file=sys.stderr)
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"JSON parsing error: {e}", file=sys.stderr)
    print(f"Raw output: {result.stdout}", file=sys.stderr)
    sys.exit(1)