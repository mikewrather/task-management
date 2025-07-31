#!/usr/bin/env python3
import json
import os
import subprocess
import sys

# Change to project directory
os.chdir("/home/mike/development/task-management")

# The Cypher query
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

# Create the prompt for Claude
prompt = f'''Use the mcp__agent-db__execute_cypher tool with these exact parameters:
{{
  "query": {json.dumps(query)},
  "parameters": {{}}
}}

Return ONLY the raw JSON result from the tool, with no additional text or formatting.'''

# Execute Claude with MCP
cmd = [
    "claude",
    "-p", prompt,
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=None)
    
    if result.returncode == 0 and result.stdout:
        # Parse the JSON output
        response = json.loads(result.stdout)
        
        # Extract the actual result from Claude's response
        if "result" in response:
            # Print just the raw result
            print(json.dumps(response["result"], indent=2))
        else:
            print(result.stdout)
    else:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
        
except Exception as e:
    print(f"Error: {str(e)}", file=sys.stderr)
    sys.exit(1)