#!/usr/bin/env python3
"""
Debug MCP validation issue by testing different parameter formats.
Created for GraphRAG Entity Refactor validation debugging.
"""

import json
import sys
import os
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_direct_mcp_call():
    """Test direct MCP call without wrapper to understand exact issue."""
    print("=== Testing Direct MCP Call ===")
    
    try:
        # Test the simplest possible call
        import subprocess
        from voice_task_manager.utils.claude_cli import get_claude_path, build_claude_env
        
        # Test 1: Health status (should work)
        print("\n--- Test 1: Health Status ---")
        cmd = [
            get_claude_path(),
            "-p", "Use mcp__agent-db__get_health_status tool",
            "--dangerously-skip-permissions",
            "--mcp-config", ".mcp.json",
            "--strict-mcp-config",
            "--output-format", "json"
        ]
        
        env = build_claude_env()
        result = subprocess.run(cmd, cwd=project_root, env=env, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Health status call successful")
            try:
                response = json.loads(result.stdout)
                print(f"Response keys: {list(response.keys())}")
            except:
                print(f"Response (first 200 chars): {result.stdout[:200]}")
        else:
            print(f"❌ Health status failed: {result.stderr[:200]}")
        
        # Test 2: Query existing schemas  
        print("\n--- Test 2: Query Schemas ---")
        cmd[1] = 'Use mcp__agent-db__query_with_cypher with query="MATCH (n:ENTITY_SCHEMA) WHERE n.entity_type CONTAINS \'AREA\' RETURN n LIMIT 1"'
        
        result = subprocess.run(cmd, cwd=project_root, env=env, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Query schemas successful")
            try:
                response = json.loads(result.stdout)
                print(f"Found {len(response.get('results', []))} schema results")
            except:
                print(f"Query response: {result.stdout[:300]}")
        else:
            print(f"❌ Query failed: {result.stderr[:200]}")
        
        # Test 3: Simple entity creation
        print("\n--- Test 3: Entity Creation ---")
        entity_data = json.dumps([{"name": "Test Area Simple"}])
        cmd[1] = f'Use mcp__agent-db__create_entities with entity_type="TASK_MANAGEMENT:AREA" and entities={entity_data}'
        
        result = subprocess.run(cmd, cwd=project_root, env=env, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Entity creation successful")
            try:
                response = json.loads(result.stdout)
                print(f"Creation response: {response}")
            except:
                print(f"Creation response: {result.stdout[:300]}")
        else:
            print(f"❌ Entity creation failed: {result.stderr[:200]}")
            
    except Exception as e:
        print(f"❌ Direct MCP test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("MCP Validation Issue Debug")
    print("=" * 40)
    
    # Set environment
    os.environ["USE_REAL_MCP"] = "true"
    
    test_direct_mcp_call()
    
    print("\n=== Summary ===")
    print("This debug script tests:")
    print("1. Basic MCP connectivity")
    print("2. Schema querying") 
    print("3. Entity creation with minimal data")
    print("4. Helps identify exact validation requirements")


if __name__ == "__main__":
    main()