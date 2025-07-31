#\!/usr/bin/env python3
import subprocess
import json
import os

# Set PROJECT_AGENTS_DIR if not set
os.environ['PROJECT_AGENTS_DIR'] = os.environ.get('PROJECT_AGENTS_DIR', '/home/mike/development/project-agents')

# Execute the query using Claude CLI
cmd = [
    '/home/mike/.nvm/versions/node/v24.2.0/bin/claude',
    '-p',
    '''Use the mcp__agent-db__execute_cypher tool with these exact parameters:
{
  "query": "\\n        MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA)\\n        RETURN p.notion_id as project_id, p.name as name, \\n               a.notion_id as area_id, a.name as area_name\\n        ",
  "parameters": {}
}

Return ONLY the raw JSON result from the tool, with no additional text or formatting.''',
    '--dangerously-skip-permissions',
    '--output-format', 'json'
]

result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    try:
        # Parse the Claude response and extract the result
        response = json.loads(result.stdout)
        if 'result' in response:
            # Extract and parse the actual tool response
            tool_result = json.loads(response['result'])
            print(json.dumps(tool_result))
        else:
            print(json.dumps({"error": "No result in response"}))
    except json.JSONDecodeError:
        print(json.dumps({"error": "Failed to parse response"}))
else:
    print(json.dumps({"error": f"Command failed: {result.stderr}"}))
