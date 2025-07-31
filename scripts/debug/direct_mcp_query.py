#!/usr/bin/env python3
"""Execute Cypher query directly using Claude CLI"""

import subprocess
import json
import os

# Build the prompt
query = """
        MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA)
        RETURN p.notion_id as project_id, p.name as name, 
               a.notion_id as area_id, a.name as area_name
        """

prompt = f"""Use the mcp__agent-db__execute_cypher tool with these exact parameters:
{{
  "query": {json.dumps(query)},
  "parameters": {{}}
}}

Return ONLY the raw JSON result from the tool, with no additional text or formatting."""

# Change to project directory
os.chdir("/home/mike/development/task-management")

# Execute claude command
cmd = [
    "/home/mike/.nvm/versions/node/v24.2.0/bin/claude",
    "-p", prompt,
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

try:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode == 0:
        # Parse the response
        response = json.loads(result.stdout)
        
        # The actual result is in the 'result' field
        if 'result' in response:
            print(response['result'])
        else:
            print(json.dumps(response, indent=2))
    else:
        print(f"Error: {result.stderr}")
        
except Exception as e:
    print(f"Exception: {e}")