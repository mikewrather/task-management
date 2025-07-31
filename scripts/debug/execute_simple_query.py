#!/usr/bin/env python3

import subprocess
import json
import os

# Change to project directory
os.chdir("/home/mike/development/task-management")

query = """
MATCH (t:TASK)
WHERE t.source = 'voice' AND t.created IS NOT NULL
OPTIONAL MATCH (t)-[:BELONGS_TO]->(p:PROJECT)
OPTIONAL MATCH (p)-[:BELONGS_TO]->(a:AREA)
RETURN t.name as title, p.name as project_name, p.notion_id as project_id,
       a.name as area_name, t.contexts as contexts
ORDER BY t.created DESC
LIMIT 20
"""

prompt = f"""Use the mcp__agent-db__execute_cypher tool with these exact parameters:
{{
  "query": "{query}",
  "parameters": {{}}
}}

Return ONLY the raw JSON result from the tool, with no additional text or formatting."""

claude_path = "/home/mike/.nvm/versions/node/v24.2.0/bin/claude"
cmd = [
    claude_path, 
    "-p", prompt,
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)  # 3 minute timeout
    if result.returncode == 0:
        data = json.loads(result.stdout)
        # Extract the actual result from Claude's response
        if 'result' in data:
            print(data['result'])
        else:
            print(result.stdout)
    else:
        print(f"Error: {result.stderr}")
except Exception as e:
    print(f"Error: {e}")