#!/usr/bin/env python3
import subprocess
import json
import os

# Change to project directory
os.chdir("/home/mike/development/task-management")

# Prepare the prompt
prompt = '''Use the mcp__agent-db__execute_cypher tool with these exact parameters:
{
  "query": "MATCH (a:AREA)\\nRETURN a.notion_id as area_id, a.name as name",
  "parameters": {}
}

Return ONLY the raw JSON result from the tool, with no additional text or formatting.'''

# Execute claude with MCP
cmd = [
    "/home/mike/.nvm/versions/node/v24.2.0/bin/claude",
    "-p", prompt,
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    # Parse the response
    response = json.loads(result.stdout)
    # Extract the actual content from the response
    if 'content' in response and len(response['content']) > 0:
        print(response['content'][0]['text'])
else:
    print(f"Error: {result.stderr}")