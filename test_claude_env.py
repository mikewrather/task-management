#!/usr/bin/env python3
"""
Debug Claude environment issues
"""

import os
import subprocess
import json
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=" * 50)
print("CLAUDE ENVIRONMENT DEBUG")
print("=" * 50)

# Check environment
print("\n1. Environment Variables:")
print(f"   CLAUDE_CODE_OAUTH_TOKEN: {'SET' if os.getenv('CLAUDE_CODE_OAUTH_TOKEN') else 'NOT SET'}")
print(f"   HOME: {os.getenv('HOME')}")
print(f"   PATH: {os.getenv('PATH')[:100]}...")

# Test direct subprocess call
print("\n2. Direct subprocess test:")
cmd = ['/home/mike/.claude/local/claude', '-p', 'Return only: TEST', '--output-format', 'json']
result = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy())

if result.stdout:
    try:
        resp = json.loads(result.stdout)
        print(f"   Success: {not resp.get('is_error')}")
        print(f"   Result: {resp.get('result')[:50] if resp.get('result') else 'None'}")
    except:
        print(f"   Failed to parse: {result.stdout[:100]}")

# Try with shell=True to see if that makes a difference
print("\n3. Shell command test:")
shell_cmd = 'claude -p "Return only: TEST" --output-format json'
result2 = subprocess.run(shell_cmd, shell=True, capture_output=True, text=True)

if result2.stdout:
    try:
        resp = json.loads(result2.stdout)
        print(f"   Success: {not resp.get('is_error')}")
        print(f"   Result: {resp.get('result')[:50] if resp.get('result') else 'None'}")
    except:
        print(f"   Failed to parse: {result2.stdout[:100]}")

print("\n" + "=" * 50)
print("Now try running this in terminal:")
print("  claude -p 'Return only: TEST' --output-format json")
print("\nAnd compare the results!")