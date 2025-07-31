#!/usr/bin/env python3
import subprocess
import json
import os
import re

# Change to project directory where .mcp.json is located
os.chdir("/home/mike/development/task-management")

# Set PROJECT_AGENTS_DIR if not set
os.environ["PROJECT_AGENTS_DIR"] = os.environ.get("PROJECT_AGENTS_DIR", "/home/mike/development/agent-db")

# Execute claude with MCP tool
cmd = [
    "/home/mike/.nvm/versions/node/v24.2.0/bin/claude",
    "-p", "Use the mcp__agent-db__get_health_status tool with these exact parameters: {} and return ONLY the raw JSON result from the tool, with no additional text or formatting.",
    "--dangerously-skip-permissions", 
    "--output-format", "json"
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=os.environ)
    if result.stdout:
        # Parse the JSON output
        output = json.loads(result.stdout)
        
        if "result" in output:
            result_content = output["result"]
            
            # Extract JSON from the result - look for JSON object pattern
            json_patterns = [
                r'\{[^{}]*"success"[^{}]*:.*?\}',  # Look for success response
                r'\{[^{}]*"components"[^{}]*:.*?\}',  # Look for health check response
                r'```json\s*(\{.*?\})\s*```',  # JSON in code block
                r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})'  # Generic JSON object
            ]
            
            for pattern in json_patterns:
                json_match = re.search(pattern, result_content, re.DOTALL)
                if json_match:
                    try:
                        # Extract the JSON part
                        json_str = json_match.group(1) if '```' in pattern else json_match.group()
                        mcp_response = json.loads(json_str)
                        print(json.dumps(mcp_response, indent=2))
                        break
                    except json.JSONDecodeError:
                        continue
            else:
                # If no JSON found, print the raw result
                print(result_content)
        else:
            print(json.dumps(output, indent=2))
    else:
        print(f"Error: {result.stderr}")
except Exception as e:
    print(f"Exception: {e}")