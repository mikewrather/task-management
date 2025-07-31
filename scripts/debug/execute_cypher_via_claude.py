#!/usr/bin/env python3
import subprocess
import json
import os

# Change to project directory where .mcp.json is located
os.chdir("/home/mike/development/task-management")

# Prepare the prompt
prompt = """Use the mcp__agent-db__execute_cypher tool with these exact parameters:
{
  "query": "MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA) RETURN p.notion_id as project_id, p.name as name, a.notion_id as area_id, a.name as area_name",
  "parameters": {}
}

Return ONLY the raw JSON result from the tool, with no additional text or formatting."""

# Execute claude with MCP
cmd = [
    "/home/mike/.claude/local/claude",
    "-p", prompt,
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=None)

if result.returncode == 0:
    try:
        # Parse the JSON response
        response = json.loads(result.stdout)
        # Extract the actual content from the response
        if "result" in response:
            print(json.dumps(response["result"], indent=2))
        else:
            print(result.stdout)
    except json.JSONDecodeError:
        print(result.stdout)
else:
    print(f"Error: {result.stderr}")