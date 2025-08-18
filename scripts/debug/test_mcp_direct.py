#!/usr/bin/env python3
"""
Test MCP tool usage directly to debug connection issues
"""

import subprocess
import json
import os

# Change to project directory
os.chdir("/home/mike/development/task-management")

print("=" * 60)
print("MCP TOOL USAGE DEBUGGING")
print("=" * 60)

# Test 1: Direct MCP call to check health
print("\n1. Testing mcp__agent-db__get_health_status:")
print("-" * 40)

health_prompt = """Use the mcp__agent-db__get_health_status tool with no parameters.
Return only the raw JSON response."""

cmd = [
    "/home/mike/.nvm/versions/node/v24.2.0/bin/claude",
    "-p", health_prompt,
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

print("Command:", " ".join(cmd))
print("\nExecuting...")

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd="/home/mike/development/task-management")
    print(f"Return code: {result.returncode}")
    print(f"STDOUT: {result.stdout[:500]}")
    if result.stderr:
        print(f"STDERR: {result.stderr[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Direct Cypher query
print("\n" + "=" * 60)
print("2. Testing mcp__agent-db__query_with_cypher:")
print("-" * 40)

cypher_prompt = """Use the mcp__agent-db__query_with_cypher tool with these parameters:
{
  "query": "MATCH (n) RETURN labels(n) as labels, count(*) as count ORDER BY count DESC LIMIT 5",
  "parameters": {}
}

Return only the raw JSON response."""

cmd[2] = cypher_prompt
print("Command:", " ".join(cmd))
print("\nExecuting...")

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd="/home/mike/development/task-management")
    print(f"Return code: {result.returncode}")
    print(f"STDOUT: {result.stdout[:1000]}")
    if result.stderr:
        print(f"STDERR: {result.stderr[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Check MCP configuration
print("\n" + "=" * 60)
print("3. Checking MCP Configuration:")
print("-" * 40)

# Check environment variables
print("\nEnvironment variables:")
print(f"NEO4J_URI: {os.getenv('NEO4J_URI', 'NOT SET')}")
print(f"NEO4J_USER: {os.getenv('NEO4J_USER', 'NOT SET')}")
print(f"NEO4J_PASSWORD: {'SET' if os.getenv('NEO4J_PASSWORD') else 'NOT SET'}")
print(f"USE_REAL_MCP: {os.getenv('USE_REAL_MCP', 'NOT SET')}")

# Check .env file
env_file = "/home/mike/development/task-management/.env"
if os.path.exists(env_file):
    print(f"\n.env file exists at: {env_file}")
    with open(env_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if 'NEO4J' in line and 'PASSWORD' not in line:
                print(f"  {line.strip()}")
            elif 'USE_REAL_MCP' in line:
                print(f"  {line.strip()}")

# Test 4: List available MCP tools
print("\n" + "=" * 60)
print("4. Listing Available MCP Tools:")
print("-" * 40)

list_tools_cmd = [
    "/home/mike/.nvm/versions/node/v24.2.0/bin/claude",
    "mcp",
    "list"
]

print("Command:", " ".join(list_tools_cmd))
print("\nExecuting...")

try:
    result = subprocess.run(list_tools_cmd, capture_output=True, text=True, timeout=10, cwd="/home/mike/development/task-management")
    print(f"Return code: {result.returncode}")
    print("Output:", result.stdout)
    if result.stderr:
        print(f"STDERR: {result.stderr}")
except Exception as e:
    print(f"Error: {e}")

# Test 5: Direct query with project-agents context
print("\n" + "=" * 60)
print("5. Testing from project-agents directory:")
print("-" * 40)

os.chdir("/home/mike/development/project-agents")

cypher_prompt2 = """Use the mcp__agent-db__query_with_cypher tool to execute this query:
{
  "query": "MATCH (n) RETURN labels(n)[0] as label, count(*) as count ORDER BY count DESC LIMIT 10",
  "parameters": {}
}

Return the raw JSON response."""

cmd = [
    "/home/mike/.nvm/versions/node/v24.2.0/bin/claude",
    "-p", cypher_prompt2,
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

print("Working directory:", os.getcwd())
print("Command:", " ".join(cmd))
print("\nExecuting...")

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    print(f"Return code: {result.returncode}")
    
    if result.returncode == 0:
        try:
            response = json.loads(result.stdout)
            if 'result' in response:
                print("Tool response:", response['result'][:1000])
            else:
                print("Full response:", json.dumps(response, indent=2)[:1000])
        except:
            print("Raw output:", result.stdout[:1000])
    else:
        print(f"STDOUT: {result.stdout[:500]}")
        if result.stderr:
            print(f"STDERR: {result.stderr[:500]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("DEBUGGING COMPLETE")
print("=" * 60)