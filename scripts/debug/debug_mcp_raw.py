#!/usr/bin/env python3
import subprocess
import json
import os

# Change to project directory where .mcp.json is located
os.chdir("/home/mike/development/task-management")

# Set PROJECT_AGENTS_DIR if not set
os.environ["PROJECT_AGENTS_DIR"] = os.environ.get("PROJECT_AGENTS_DIR", "/home/mike/development/agent-db")

# Execute claude with a simple prompt to force MCP usage
cmd = [
    "/home/mike/.nvm/versions/node/v24.2.0/bin/claude",
    "-p", """The user needs you to check the health status of the GraphRAG database. Please check if the database is healthy and return the status information.""",
    "--dangerously-skip-permissions", 
    "--output-format", "json"
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=os.environ)
    print("=== RAW STDOUT ===")
    print(result.stdout)
    print("\n=== RAW STDERR ===")
    print(result.stderr)
    print("\n=== RETURN CODE ===")
    print(result.returncode)
    
    if result.stdout:
        try:
            output = json.loads(result.stdout)
            print("\n=== PARSED OUTPUT ===")
            print(json.dumps(output, indent=2))
        except json.JSONDecodeError as e:
            print(f"\nFailed to parse JSON: {e}")
            
except Exception as e:
    print(f"Exception: {e}")