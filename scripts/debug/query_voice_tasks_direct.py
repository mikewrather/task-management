#!/usr/bin/env python3
import os
import subprocess
import json

# Change to project directory where .mcp.json is located
os.chdir("/home/mike/development/task-management")

# The Cypher query to execute
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
prompt = f"""Use the mcp__agent-db__execute_cypher tool with these exact parameters:
{{
  "query": "{query.replace('"', '\\"')}",
  "parameters": {{}}
}}

Return ONLY the raw JSON result from the tool, with no additional text or formatting."""

# Execute claude with the prompt
cmd = [
    "/home/mike/.claude/local/claude",
    "-p", prompt,
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=None)
    
    if result.returncode == 0:
        # Parse the JSON output
        output = json.loads(result.stdout)
        
        # Extract the actual content from Claude's response
        if "content" in output:
            content = output["content"]
            # Try to parse the content as JSON if it's a string
            if isinstance(content, str):
                try:
                    content_json = json.loads(content)
                    print(json.dumps(content_json, indent=2))
                except json.JSONDecodeError:
                    print(content)
            else:
                print(json.dumps(content, indent=2))
        else:
            print(json.dumps(output, indent=2))
    else:
        print(f"Error running claude: {result.stderr}")
        
except subprocess.TimeoutExpired:
    print("Command timed out")
except Exception as e:
    print(f"Error: {e}")