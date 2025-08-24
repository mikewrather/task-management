#!/usr/bin/env python3
"""
Test script to verify that entities are created with embeddings
using the updated GraphRAG adapter.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter
from src.voice_task_manager.adapters.base import TaskData
import logging
logger = logging.getLogger(__name__)

def test_entity_creation():
    """Test creating entities with the GraphRAG adapter"""
    
    print("=" * 60)
    print("Testing Entity Creation with Embeddings")
    print("=" * 60)
    
    # Initialize the adapter
    adapter = GraphRAGTaskAdapter()
    
    # Test 1: Create a task
    print("\n1. Creating a TASK entity...")
    task_data = TaskData(
        name="Test embedding generation for tasks",
        description="This is a test task to verify that embeddings are automatically generated when creating tasks through the GraphRAG adapter",
        status="pending",
        priority="high",
        contexts=["@testing", "@development"],
        source="test_script",
        created_at=datetime.now()
    )
    
    task_id = adapter.create_task(task_data)
    
    if task_id:
        print(f"✅ Task created successfully with ID: {task_id}")
    else:
        print(f"❌ Failed to create task")
    
    # Test 2: Create a project
    print("\n2. Creating a PROJECT entity...")
    project_id = adapter.create_project(
        name="Test Embedding Project",
        description="A test project to verify embedding generation for projects"
    )
    
    if project_id:
        print(f"✅ Project created successfully with ID: {project_id}")
    else:
        print(f"❌ Failed to create project")
    
    # Test 3: Verify embeddings exist
    print("\n3. Verifying embeddings in Neo4j...")
    
    # Check for entities WITH embeddings
    query_with = """
    MATCH (n)
    WHERE n.entity_embedding IS NOT NULL
    AND (n:`TASK_MANAGEMENT:TASK` OR n:`TASK_MANAGEMENT:PROJECT`)
    RETURN labels(n) as labels, count(n) as count
    """
    
    response_with = adapter._execute_mcp_command("execute_cypher", {
        "query": query_with,
        "parameters": {}
    })
    
    if isinstance(response_with, list) and len(response_with) > 0:
        print("\nEntities WITH embeddings:")
        for row in response_with:
            labels = ':'.join(row['labels']) if isinstance(row['labels'], list) else row['labels']
            print(f"   ✅ {labels}: {row['count']} entities have embeddings")
    
    # Check for entities WITHOUT embeddings
    query_without = """
    MATCH (n)
    WHERE n.entity_embedding IS NULL
    AND (n:`TASK_MANAGEMENT:TASK` OR n:`TASK_MANAGEMENT:PROJECT`)
    RETURN labels(n) as labels, count(n) as count
    """
    
    response_without = adapter._execute_mcp_command("execute_cypher", {
        "query": query_without,
        "parameters": {}
    })
    
    if isinstance(response_without, list) and len(response_without) > 0:
        print("\nEntities WITHOUT embeddings:")
        for row in response_without:
            if row['count'] > 0:
                labels = ':'.join(row['labels']) if isinstance(row['labels'], list) else row['labels']
                print(f"   ⚠️ {labels}: {row['count']} entities missing embeddings")
    
    # Test 4: Test duplicate detection
    print("\n4. Testing duplicate detection...")
    duplicate_task = TaskData(
        name="Test embedding generation",  # Similar to first task
        description="Testing embeddings for tasks",  # Similar description
        status="pending",
        priority="medium",
        contexts=["@testing"],
        source="test_script",
        created_at=datetime.now()
    )
    
    dup_task_id = adapter.create_task(duplicate_task)
    
    if dup_task_id:
        print(f"✅ Similar task handled appropriately, ID: {dup_task_id}")
    else:
        print(f"❌ Failed to handle similar task")
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("1. Tasks should be created as TASK_MANAGEMENT:TASK with 'id' property")
    print("2. Projects should be created as TASK_MANAGEMENT:PROJECT with 'name' property")
    print("3. All entities should have entity_embedding property")
    print("4. Duplicate detection should work via semantic similarity")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_entity_creation()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()