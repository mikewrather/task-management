#!/usr/bin/env python3
"""
Systematically solve the MCP validation issue by testing different approaches.
Created for GraphRAG Entity Refactor validation debugging.
"""

import json
import sys
import os
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from voice_task_manager.utils.claude_cli import execute_claude_command


def test_different_formats():
    """Test different entity data formats to find what works."""
    print("=== Testing Different Entity Data Formats ===")
    
    # Test case 1: Minimal data
    test_cases = [
        {
            "name": "minimal_object", 
            "entity_type": "TASK_MANAGEMENT:AREA",
            "entities": {"name": "Health"}
        },
        {
            "name": "minimal_array",
            "entity_type": "TASK_MANAGEMENT:AREA", 
            "entities": [{"name": "Health"}]
        },
        {
            "name": "with_id_object",
            "entity_type": "TASK_MANAGEMENT:AREA",
            "entities": {"id": "area_001", "name": "Health"}
        },
        {
            "name": "with_id_array",
            "entity_type": "TASK_MANAGEMENT:AREA",
            "entities": [{"id": "area_002", "name": "Health"}]
        },
        {
            "name": "task_minimal",
            "entity_type": "TASK_MANAGEMENT:TASK",
            "entities": [{"id": "task_001", "description": "Test task"}]
        },
        {
            "name": "task_with_name", 
            "entity_type": "TASK_MANAGEMENT:TASK",
            "entities": [{"id": "task_002", "name": "Test Task", "description": "Test task"}]
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        
        # Build the command
        entities_json = json.dumps(test_case['entities'])
        prompt = f'Use mcp__agent-db__create_entities with entity_type="{test_case["entity_type"]}" and entities={entities_json}'
        
        success, stdout, stderr = execute_claude_command(prompt, timeout=120)
        
        print(f"Success: {success}")
        if success:
            print(f"Response: {stdout[:200]}...")
        else:
            print(f"Error: {stderr[:200]}...")


def test_existing_entity_query():
    """Test querying existing entities to understand working format."""
    print("\n=== Testing Existing Entity Queries ===")
    
    # Check what entities exist
    queries = [
        "MATCH (n) WHERE any(label IN labels(n) WHERE label STARTS WITH 'TASK_MANAGEMENT') RETURN labels(n), count(n) ORDER BY count(n) DESC LIMIT 5",
        "MATCH (n:TASK_MANAGEMENT:AREA) RETURN n LIMIT 1", 
        "MATCH (n:TASK_MANAGEMENT:PROJECT) RETURN n LIMIT 1",
        "MATCH (n:TASK_MANAGEMENT:TASK) RETURN n LIMIT 1"
    ]
    
    for query in queries:
        print(f"\n--- Query: {query[:50]}... ---")
        
        success, stdout, stderr = execute_claude_command(
            f'Use mcp__agent-db__query_with_cypher with query="{query}"',
            timeout=60
        )
        
        print(f"Success: {success}")
        if success:
            try:
                response = json.loads(stdout)
                results = response.get("results", [])
                print(f"Results count: {len(results)}")
                if results:
                    print(f"Sample result: {json.dumps(results[0], indent=2)[:300]}...")
            except:
                print(f"Response: {stdout[:200]}...")
        else:
            print(f"Error: {stderr[:200]}...")


def main():
    print("Solving MCP Validation Issue")
    print("=" * 40)
    
    # Set environment
    os.environ["USE_REAL_MCP"] = "true"
    
    # Test 1: Different formats
    test_different_formats()
    
    # Test 2: Existing entities
    test_existing_entity_query()
    
    print("\n=== Conclusions ===")
    print("This script will help identify:")
    print("1. What entity data format works")
    print("2. Whether entities parameter should be object or array")
    print("3. What fields are actually required")
    print("4. Whether entities are being created successfully despite validation errors")


if __name__ == "__main__":
    main()