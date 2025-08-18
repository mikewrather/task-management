#!/usr/bin/env python3
"""
List recent tasks to see what's in the database
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter
from src.voice_task_manager.utils.logging import VoiceLogger

def list_recent_tasks():
    """List recent tasks from the database"""
    
    logger = VoiceLogger()
    adapter = GraphRAGTaskAdapter()
    
    print("=" * 60)
    print("📋 Listing recent tasks in database...")
    print("=" * 60)
    
    # Try both label formats
    queries = [
        ("TASK_MANAGEMENT:TASK (new format)", """
        MATCH (t:`TASK_MANAGEMENT:TASK`)
        RETURN t.id as task_id,
               t.name as name,
               t.description as description,
               t.status as status,
               t.created as created,
               t.entity_embedding IS NOT NULL as has_embedding,
               labels(t) as labels
        ORDER BY t.created DESC
        LIMIT 20
        """),
        ("TASK (old format)", """
        MATCH (t:TASK)
        RETURN id(t) as task_id,
               t.name as name,
               t.description as description,
               t.status as status,
               t.created as created,
               t.entity_embedding IS NOT NULL as has_embedding,
               labels(t) as labels
        ORDER BY t.created DESC
        LIMIT 20
        """)
    ]
    
    for label_type, query in queries:
        print(f"\n🔍 Checking {label_type}...")
        
        response = adapter._execute_mcp_command("execute_cypher", {
            "query": query,
            "parameters": {}
        })
        
        tasks = response if isinstance(response, list) else response.get("results", [])
        
        if tasks:
            print(f"✅ Found {len(tasks)} tasks with {label_type}:\n")
            
            for i, task in enumerate(tasks, 1):
                print(f"{i}. Task ID: {task['task_id']}")
                print(f"   Name: {task['name']}")
                print(f"   Description: {task['description'][:100] if task['description'] else 'None'}...")
                print(f"   Status: {task['status']}")
                print(f"   Has Embedding: {task['has_embedding']}")
                print(f"   Labels: {task['labels']}")
                print(f"   Created: {task['created']}")
                print("-" * 40)
        else:
            print(f"❌ No tasks found with {label_type}")
    
    # Count total tasks
    print("\n" + "=" * 60)
    print("📊 Task Statistics")
    print("=" * 60)
    
    count_queries = [
        ("TASK_MANAGEMENT:TASK", "MATCH (t:`TASK_MANAGEMENT:TASK`) RETURN count(t) as count"),
        ("TASK", "MATCH (t:TASK) RETURN count(t) as count"),
        ("All nodes", "MATCH (n) RETURN count(n) as count"),
        ("Nodes with embeddings", "MATCH (n) WHERE n.entity_embedding IS NOT NULL RETURN count(n) as count")
    ]
    
    for label, query in count_queries:
        response = adapter._execute_mcp_command("execute_cypher", {
            "query": query,
            "parameters": {}
        })
        
        result = response if isinstance(response, list) else response.get("results", [])
        if result:
            count = result[0]['count']
            print(f"  {label}: {count}")
    
    # Search for tasks with "block" or similar keywords anywhere
    print("\n" + "=" * 60)
    print("🔍 Broad keyword search for 'block', 'move', 'yard', etc...")
    print("=" * 60)
    
    broad_query = """
    MATCH (n)
    WHERE ANY(prop in keys(n) WHERE 
        toString(n[prop]) =~ '(?i).*(block|concrete|move|yard|garden|heavy).*'
    )
    RETURN labels(n) as labels,
           n.name as name,
           n.description as description,
           id(n) as node_id
    LIMIT 10
    """
    
    response = adapter._execute_mcp_command("execute_cypher", {
        "query": broad_query,
        "parameters": {}
    })
    
    results = response if isinstance(response, list) else response.get("results", [])
    
    if results:
        print(f"\n✅ Found {len(results)} nodes with related keywords:")
        for r in results:
            print(f"  - {r['labels']}: {r['name']}")
            if r['description']:
                print(f"    {r['description'][:100]}...")
    else:
        print("❌ No nodes found with those keywords")


if __name__ == "__main__":
    list_recent_tasks()