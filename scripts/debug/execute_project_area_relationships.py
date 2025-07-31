#!/usr/bin/env python3
"""Execute Cypher query to get project-area relationships"""

import subprocess
import json
import os
import sys

# Change to project directory
os.chdir("/home/mike/development/task-management")

# Build the prompt
query = "MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA) RETURN p.notion_id as project_id, p.name as name, a.notion_id as area_id, a.name as area_name"
parameters = {}

prompt = f"""Use the mcp__agent-db__execute_cypher tool with these exact parameters:
{{
  "query": "{query}",
  "parameters": {json.dumps(parameters)}
}}

Return ONLY the raw JSON result from the tool, with no additional text or formatting."""

# Execute via claude
claude_path = "/home/mike/.nvm/versions/node/v24.2.0/bin/claude"
cmd = [
    claude_path, 
    "-p", prompt,
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

try:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    
    # Parse the response
    output = result.stdout.strip()
    response = json.loads(output)
    
    # Extract the actual result
    if isinstance(response, dict) and 'result' in response:
        result_content = response['result']
        
        # The result might be a string containing JSON
        if isinstance(result_content, str):
            try:
                actual_result = json.loads(result_content)
                print(json.dumps(actual_result, indent=2))
            except:
                print(result_content)
        else:
            print(json.dumps(result_content, indent=2))
    else:
        print(json.dumps(response, indent=2))
        
except subprocess.TimeoutExpired:
    print("Error: Command timed out", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)