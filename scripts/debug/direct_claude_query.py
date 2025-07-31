#!/usr/bin/env python3

import subprocess
import json
import os
import re

# Change to project directory
os.chdir("/home/mike/development/task-management")

# The Cypher query
cypher_query = """
MATCH (t:TASK)
WHERE t.source = 'voice' AND t.created IS NOT NULL
OPTIONAL MATCH (t)-[:BELONGS_TO]->(p:PROJECT)
OPTIONAL MATCH (p)-[:BELONGS_TO]->(a:AREA)
RETURN t.name as title, p.name as project_name, p.notion_id as project_id,
       a.name as area_name, t.contexts as contexts
ORDER BY t.created DESC
LIMIT 20
"""

# Build the prompt
prompt = f'''Use the mcp__agent-db__execute_cypher tool with these exact parameters:
{{
  "query": "{cypher_query.strip()}",
  "parameters": {{}}
}}

Return ONLY the raw JSON result from the tool, with no additional text or formatting.'''

# Execute claude
cmd = [
    "/home/mike/.claude/local/claude",
    "-p", prompt,
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    if result.returncode == 0:
        # Parse the JSON wrapper
        wrapper = json.loads(result.stdout)
        
        # Extract the actual result from the content
        if isinstance(wrapper, dict) and 'content' in wrapper:
            content = wrapper['content']
            # Extract JSON array from content string
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                print(json.dumps(data))
            else:
                print(content)
        else:
            print(result.stdout)
    else:
        print(f"Error: {result.stderr}")
        
except subprocess.TimeoutExpired:
    print("Error: Command timed out")
except Exception as e:
    print(f"Error: {e}")