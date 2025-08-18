#!/usr/bin/env python3
"""
Find and analyze the concrete blocks task to debug relationship assignment
"""

import sys
import os
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter
from src.voice_task_manager.utils.logging import VoiceLogger

def find_concrete_blocks_task():
    """Find the task about moving concrete blocks"""
    
    logger = VoiceLogger()
    adapter = GraphRAGTaskAdapter()
    
    print("=" * 60)
    print("🔍 Searching for concrete blocks task...")
    print("=" * 60)
    
    # Search for the task - try both old and new labels
    search_queries = [
        # New label format
        """
        MATCH (t:`TASK_MANAGEMENT:TASK`)
        WHERE toLower(t.name) CONTAINS 'concrete' 
           OR toLower(t.description) CONTAINS 'concrete'
           OR toLower(t.name) CONTAINS 'block'
           OR toLower(t.description) CONTAINS 'block'
        RETURN t.id as task_id, 
               t.name as name, 
               t.description as description,
               t.project_name as project_name,
               t.area_name as area_name,
               t.status as status,
               t.created as created,
               t.entity_embedding IS NOT NULL as has_embedding,
               labels(t) as labels
        """,
        # Old label format
        """
        MATCH (t:TASK)
        WHERE toLower(t.name) CONTAINS 'concrete' 
           OR toLower(t.description) CONTAINS 'concrete'
           OR toLower(t.name) CONTAINS 'block'
           OR toLower(t.description) CONTAINS 'block'
        RETURN id(t) as task_id, 
               t.name as name, 
               t.description as description,
               t.project_name as project_name,
               t.area_name as area_name,
               t.status as status,
               t.created as created,
               t.entity_embedding IS NOT NULL as has_embedding,
               labels(t) as labels
        """
    ]
    
    tasks = []
    for i, query in enumerate(search_queries):
        print(f"\nTrying query format {i+1}...")
        response = adapter._execute_mcp_command("execute_cypher", {
            "query": query,
            "parameters": {}
        })
        
        result = response if isinstance(response, list) else response.get("results", [])
        if result:
            tasks = result
            print(f"✅ Found tasks with query format {i+1}")
            break
    
    if not tasks:
        print("❌ No tasks found mentioning concrete or blocks")
        return None
    
    print(f"\n✅ Found {len(tasks)} task(s):\n")
    
    for task in tasks:
        print(f"Task ID: {task['task_id']}")
        print(f"  Name: {task['name']}")
        print(f"  Description: {task['description'][:100]}...")
        print(f"  Project: {task['project_name'] or 'None'}")
        print(f"  Area: {task['area_name'] or 'None'}")
        print(f"  Status: {task['status']}")
        print(f"  Has Embedding: {task['has_embedding']}")
        print(f"  Created: {task['created']}")
        print("-" * 40)
    
    # For each task, check its relationships
    print("\n" + "=" * 60)
    print("📊 Analyzing relationships for found tasks...")
    print("=" * 60)
    
    for task in tasks:
        print(f"\n🔗 Relationships for task: {task['task_id']}")
        
        # Check existing relationships
        rel_query = """
        MATCH (t:`TASK_MANAGEMENT:TASK` {id: $task_id})
        OPTIONAL MATCH (t)-[r1:BELONGS_TO]->(p:`TASK_MANAGEMENT:PROJECT`)
        OPTIONAL MATCH (t)-[r2:RELATES_TO]->(a:AREA)
        OPTIONAL MATCH (t)-[r3:CONTRIBUTES_TO]->(g:GOAL)
        RETURN 
            p.name as project,
            a.name as area,
            g.name as goal,
            r1 IS NOT NULL as has_project,
            r2 IS NOT NULL as has_area,
            r3 IS NOT NULL as has_goal
        """
        
        rel_response = adapter._execute_mcp_command("execute_cypher", {
            "query": rel_query,
            "parameters": {"task_id": task['task_id']}
        })
        
        relationships = rel_response if isinstance(rel_response, list) else rel_response.get("results", [])
        
        if relationships:
            rel = relationships[0]
            print(f"  ✓ Project: {rel['project'] or 'None'} (linked: {rel['has_project']})")
            print(f"  ✓ Area: {rel['area'] or 'None'} (linked: {rel['has_area']})")
            print(f"  ✓ Goal: {rel['goal'] or 'None'} (linked: {rel['has_goal']})")
        else:
            print("  ❌ No relationships found")
    
    # Search for potential projects and areas to link to
    print("\n" + "=" * 60)
    print("🎯 Finding potential projects and areas to link...")
    print("=" * 60)
    
    # Find all projects
    project_query = """
    MATCH (p:`TASK_MANAGEMENT:PROJECT`)
    RETURN p.name as name, 
           p.description as description,
           id(p) as node_id
    ORDER BY p.name
    """
    
    proj_response = adapter._execute_mcp_command("execute_cypher", {
        "query": project_query,
        "parameters": {}
    })
    
    projects = proj_response if isinstance(proj_response, list) else []
    
    print(f"\n📁 Available Projects ({len(projects)}):")
    for p in projects[:10]:  # Show first 10
        print(f"  - {p['name']} (ID: {p['node_id']})")
        if p['description']:
            print(f"    {p['description'][:80]}...")
    
    # Find all areas
    area_query = """
    MATCH (a:AREA)
    RETURN a.name as name,
           a.description as description,
           id(a) as node_id
    ORDER BY a.name
    """
    
    area_response = adapter._execute_mcp_command("execute_cypher", {
        "query": area_query,
        "parameters": {}
    })
    
    areas = area_response if isinstance(area_response, list) else []
    
    print(f"\n🏠 Available Areas ({len(areas)}):")
    for a in areas[:10]:  # Show first 10
        print(f"  - {a['name']} (ID: {a['node_id']})")
        if a.get('description'):
            print(f"    {a['description'][:80]}...")
    
    # Suggest based on keywords
    print("\n" + "=" * 60)
    print("💡 Suggestions based on task content...")
    print("=" * 60)
    
    # Keywords that might indicate house/home projects
    house_keywords = ['concrete', 'block', 'yard', 'garden', 'home', 'house', 'build', 'construction']
    
    print("\nBased on keywords, this task might belong to:")
    print("  - Area: 'House' or 'Home' (physical home projects)")
    print("  - Project: Could be a yard/garden/construction project")
    
    # If task has embeddings, find similar tasks with relationships
    if tasks and tasks[0]['has_embedding']:
        print("\n🧠 Finding similar tasks with relationships (using embeddings)...")
        
        similar_query = """
        MATCH (t1:`TASK_MANAGEMENT:TASK` {id: $task_id})
        MATCH (t2:`TASK_MANAGEMENT:TASK`)
        WHERE t1 <> t2
        AND t1.entity_embedding IS NOT NULL
        AND t2.entity_embedding IS NOT NULL
        AND ((t2)-[:BELONGS_TO]->() OR (t2)-[:RELATES_TO]->())
        WITH t1, t2,
             gds.similarity.cosine(t1.entity_embedding, t2.entity_embedding) AS similarity
        WHERE similarity > 0.6
        MATCH (t2)-[:BELONGS_TO|RELATES_TO]->(related)
        RETURN t2.name as similar_task,
               labels(related)[0] as related_type,
               related.name as related_name,
               similarity
        ORDER BY similarity DESC
        LIMIT 5
        """
        
        sim_response = adapter._execute_mcp_command("execute_cypher", {
            "query": similar_query,
            "parameters": {"task_id": tasks[0]['task_id']}
        })
        
        similar = sim_response if isinstance(sim_response, list) else []
        
        if similar:
            print("\nSimilar tasks and their relationships:")
            for s in similar:
                print(f"  - '{s['similar_task']}' (similarity: {s['similarity']:.2f})")
                print(f"    → {s['related_type']}: {s['related_name']}")
    
    return tasks[0] if tasks else None


def suggest_relationships_for_task(task_id: str):
    """Suggest and optionally create relationships for a specific task"""
    
    adapter = GraphRAGTaskAdapter()
    
    print(f"\n" + "=" * 60)
    print(f"🔧 Manual relationship creation for task: {task_id}")
    print("=" * 60)
    
    # Example of how to create a relationship
    print("\nTo create a relationship, use one of these patterns:")
    print("\n1. Link to a project:")
    print(f'   adapter._create_relationship("{task_id}", "<project_node_id>", "BELONGS_TO", "TASK_MANAGEMENT:PROJECT")')
    
    print("\n2. Link to an area:")
    print(f'   adapter._create_relationship("{task_id}", "<area_node_id>", "RELATES_TO", "AREA")')
    
    print("\n3. Link to a goal:")
    print(f'   adapter._create_relationship("{task_id}", "<goal_node_id>", "CONTRIBUTES_TO", "GOAL")')


if __name__ == "__main__":
    task = find_concrete_blocks_task()
    
    if task:
        suggest_relationships_for_task(task['task_id'])