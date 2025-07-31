#!/usr/bin/env python3
"""Execute health status check directly using Claude CLI"""

import subprocess
import json
import os

# Build the prompt
prompt = """Use the mcp__agent-db__get_health_status tool with these exact parameters:
{}

Return ONLY the raw JSON result from the tool, with no additional text or formatting."""

# Change to project directory
os.chdir("/home/mike/development/task-management")

# Try different claude paths
claude_paths = [
    "/home/mike/.claude/local/claude",
    "/home/mike/.nvm/versions/node/v24.2.0/bin/claude",
    "claude"
]

# Execute claude command
for claude_path in claude_paths:
    try:
        cmd = [
            claude_path,
            "-p", prompt,
            "--dangerously-skip-permissions",
            "--output-format", "json"
        ]
        
        print(f"Trying {claude_path}...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # Parse the response
            response = json.loads(result.stdout)
            
            # The actual result is in the 'result' field
            if 'result' in response:
                print(response['result'])
            else:
                print(json.dumps(response, indent=2))
            break
        else:
            print(f"Error with {claude_path}: {result.stderr}")
            
    except FileNotFoundError:
        print(f"{claude_path} not found")
        continue
    except Exception as e:
        print(f"Exception with {claude_path}: {e}")
        continue