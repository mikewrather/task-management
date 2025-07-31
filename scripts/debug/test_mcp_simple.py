#!/usr/bin/env python3
import subprocess
import json
import os

# Change to project directory where .mcp.json is located
os.chdir("/home/mike/development/task-management")

# Set PROJECT_AGENTS_DIR if not set
os.environ["PROJECT_AGENTS_DIR"] = os.environ.get("PROJECT_AGENTS_DIR", "/home/mike/development/agent-db")

# Execute claude with MCP tool - just list available tools
cmd = [
    "/home/mike/.nvm/versions/node/v24.2.0/bin/claude",
    "-p", "List all available MCP tools that start with mcp__agent-db and return them as a JSON array",
    "--dangerously-skip-permissions", 
    "--output-format", "json"
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=os.environ)
    if result.stdout:
        print("Raw stdout:")
        print(result.stdout)
        print("\n" + "="*50 + "\n")
        
        try:
            # Parse the JSON output
            output = json.loads(result.stdout)
            
            # Extract the result
            if "result" in output:
                print("Result field:")
                print(output["result"])
            else:
                print("Full output:")
                print(json.dumps(output, indent=2))
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
    else:
        print(f"Error: {result.stderr}")
        print(f"Return code: {result.returncode}")
except Exception as e:
    print(f"Exception: {e}")