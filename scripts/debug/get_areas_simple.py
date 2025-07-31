#!/usr/bin/env python3
import json
import subprocess
import os

# Change to project directory where .mcp.json is located
os.chdir("/home/mike/development/task-management")

# Prepare the prompt with the exact Cypher query format requested
prompt = '''Use the mcp__agent-db__execute_cypher tool with these exact parameters:
{
  "query": "\\n        MATCH (a:AREA)\\n        RETURN a.notion_id as area_id, a.name as name\\n        ",
  "parameters": {}
}

Return ONLY the raw JSON result from the tool, with no additional text or formatting.'''

# Use full path to claude command  
claude_path = "/home/mike/.nvm/versions/node/v24.2.0/bin/claude"

# Execute claude with MCP - no timeout
cmd = [
    claude_path,
    "-p", prompt,
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=None)

if result.returncode == 0:
    try:
        # Parse the JSON output
        output = json.loads(result.stdout)
        # Extract the actual content from the Claude response
        if 'content' in output:
            content = output['content']
            # Try to parse the content as JSON if it looks like JSON
            if content.strip().startswith('{') or content.strip().startswith('['):
                try:
                    json_content = json.loads(content)
                    print(json.dumps(json_content))
                except:
                    print(content)
            else:
                print(content)
        else:
            print(json.dumps(output))
    except json.JSONDecodeError:
        print(result.stdout)
else:
    print(f"Error: {result.stderr}")