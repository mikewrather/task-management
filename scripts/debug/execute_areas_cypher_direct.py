#!/usr/bin/env python3
"""Execute Cypher query to get all areas from GraphRAG database"""

import subprocess
import json
import os

# Change to project directory
os.chdir("/home/mike/development/task-management")

# Build the query
query = """
        MATCH (a:AREA)
        RETURN a.notion_id as area_id, a.name as name
        """

# Create the prompt for Claude
prompt = f"""Use the mcp__agent-db__execute_cypher tool with these exact parameters:
{json.dumps({"query": query, "parameters": {}}, indent=2)}

Return ONLY the raw JSON result from the tool, with no additional text or formatting."""

# Execute via claude
claude_path = "/home/mike/.nvm/versions/node/v24.2.0/bin/claude"
cmd = [
    claude_path,
    "-p", prompt,
    "--dangerously-skip-permissions", 
    "--output-format", "json"
]

print("Executing Cypher query via Claude MCP...")
result = subprocess.run(cmd, capture_output=True, text=True, timeout=None)

if result.returncode != 0:
    print(f"Error: {result.stderr}")
else:
    # Parse the Claude JSON wrapper
    try:
        response = json.loads(result.stdout)
        if 'result' in response:
            # Extract and print the raw result
            print(response['result'])
        else:
            print(result.stdout)
    except json.JSONDecodeError:
        print(result.stdout)