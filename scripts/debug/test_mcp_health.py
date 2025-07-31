#!/usr/bin/env python3
import subprocess
import json
import os

# Change to project directory where .mcp.json is located
os.chdir("/home/mike/development/task-management")

# Execute claude with MCP tool
cmd = [
    "/home/mike/.nvm/versions/node/v24.2.0/bin/claude",
    "-p", "Use the mcp__agent-db__get_health_status tool and return the JSON result",
    "--dangerously-skip-permissions", 
    "--output-format", "json",
    "-v"  # Add verbose flag
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=None)
    if result.stdout:
        # Parse the JSON output
        output = json.loads(result.stdout)
        # Look for the result field which contains the actual MCP response
        if "result" in output:
            # The result field contains the MCP tool response
            result_content = output["result"]
            # If it's a string, try to parse it as JSON
            if isinstance(result_content, str):
                # Remove markdown code block if present
                if result_content.startswith('```json') and result_content.endswith('```'):
                    result_content = result_content[7:-3].strip()
                try:
                    mcp_response = json.loads(result_content)
                    print(json.dumps(mcp_response, indent=2))
                except json.JSONDecodeError:
                    # If it's not JSON, just print the raw result
                    print(result_content)
            else:
                # If it's already a dict/object, print it directly
                print(json.dumps(result_content, indent=2))
        else:
            print(json.dumps(output, indent=2))
    else:
        print(f"Error: {result.stderr}")
except Exception as e:
    print(f"Exception: {e}")