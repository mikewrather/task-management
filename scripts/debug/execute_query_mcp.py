#!/usr/bin/env python3
import subprocess
import json
import os

# Change to project directory where .mcp.json is located
os.chdir("/home/mike/development/task-management")

# Prepare the prompt with the Cypher query
prompt = '''Use the mcp__agent-db__execute_cypher tool with these exact parameters:
{
  "query": "MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA) RETURN p.notion_id as project_id, p.name as name, a.notion_id as area_id, a.name as area_name",
  "parameters": {}
}

Return ONLY the raw JSON result from the tool, with no additional text or formatting.'''

# Execute claude with MCP
cmd = [
    "claude",
    "-p", prompt,
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    try:
        # Parse the outer JSON wrapper
        wrapper = json.loads(result.stdout)
        # Extract the actual content
        content = wrapper.get("content", "")
        # Try to parse the content as JSON
        try:
            data = json.loads(content)
            print(json.dumps(data, indent=2))
        except:
            # If content is not valid JSON, just print it
            print(content)
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(result.stdout)
else:
    print(f"Error executing claude: {result.stderr}")