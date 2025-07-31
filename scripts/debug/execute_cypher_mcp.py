#!/usr/bin/env python3
import os
import subprocess
import json

# Change to project directory where .mcp.json is located
os.chdir("/home/mike/development/task-management")

# Prepare the prompt with the Cypher query
prompt = '''Use the mcp__agent-db__execute_cypher tool with these exact parameters:
{
  "query": "MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA) RETURN p.notion_id as project_id, p.name as name, a.notion_id as area_id, a.name as area_name",
  "parameters": {}
}

Return ONLY the raw JSON result from the tool, with no additional text or formatting.'''

# Run claude with MCP integration
cmd = [
    "/home/mike/.claude/local/claude",
    "-p", prompt,
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=None)
    output = json.loads(result.stdout)
    
    # Extract the actual content from the JSON wrapper
    if "text" in output:
        print(output["text"])
    else:
        print(json.dumps(output, indent=2))
        
except subprocess.CalledProcessError as e:
    print(f"Error executing claude: {e}")
    print(f"stdout: {e.stdout}")
    print(f"stderr: {e.stderr}")
except json.JSONDecodeError as e:
    print(f"Error parsing JSON: {e}")
    print(f"Raw output: {result.stdout}")
except Exception as e:
    print(f"Unexpected error: {e}")