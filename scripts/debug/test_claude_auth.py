#!/usr/bin/env python3
"""
Test Claude authentication with the new robust utilities
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.voice_task_manager.utils.claude_cli import (
    get_claude_path,
    build_claude_env,
    preflight_claude_ok,
    execute_claude_command
)

print("=" * 60)
print("Testing Claude Authentication with Robust Utilities")
print("=" * 60)

# Test 1: Check Claude binary path
print("\n1. Claude Binary Path:")
claude_path = get_claude_path()
print(f"   Path: {claude_path}")
print(f"   Exists: {Path(claude_path).exists()}")

# Test 2: Check environment setup
print("\n2. Environment Setup:")
env = build_claude_env()
print(f"   HOME: {env.get('HOME')}")
print(f"   PYTHONPATH includes project: {'task-management/src' in env.get('PYTHONPATH', '')}")
print(f"   PATH includes Claude dir: {str(Path(claude_path).parent) in env.get('PATH', '')}")

# Test 3: Run preflight check
print("\n3. Preflight Check:")
ok, message = preflight_claude_ok()
if ok:
    print(f"   ✅ SUCCESS: {message}")
else:
    print(f"   ❌ FAILED: {message}")

# Test 4: Test simple command execution
print("\n4. Simple Command Test:")
success, stdout, stderr = execute_claude_command(
    "Return the text: Authentication test successful",
    skip_preflight=True  # Already did preflight above
)
if success:
    print("   ✅ Command executed successfully")
    if stdout:
        print(f"   Output: {stdout[:200]}")
else:
    print(f"   ❌ Command failed")
    if stderr:
        print(f"   Error: {stderr[:500]}")

# Test 5: Test MCP access
print("\n5. MCP Access Test:")
success, stdout, stderr = execute_claude_command(
    "Use the mcp__agent-db__get_health_status tool and return the result",
    skip_preflight=True
)
if success:
    print("   ✅ MCP command executed successfully")
    if stdout:
        print(f"   Output: {stdout[:200]}")
else:
    print(f"   ❌ MCP command failed")
    if stderr:
        print(f"   Error: {stderr[:500]}")

print("\n" + "=" * 60)
print("Authentication Test Complete")
print("=" * 60)