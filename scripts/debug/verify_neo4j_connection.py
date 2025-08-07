#!/usr/bin/env python3
"""
Verify Neo4j Database Connection

Check which Neo4j database the MCP server is connected to and compare
with what our GraphRAG adapter sees.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter
from voice_task_manager.utils.logging import VoiceLogger

def main():
    logger = VoiceLogger()
    adapter = GraphRAGTaskAdapter(logger=logger)
    
    print("🔍 Verifying Neo4j database connections...")
    print(f"📍 MCP Config: {project_root}/.mcp.json")
    
    # Check MCP server environment
    print(f"\n🌍 MCP Server Environment:")
    print(f"   NEO4J_PASSWORD: {'***' if os.getenv('NEO4J_PASSWORD') else 'NOT SET'}")
    print(f"   NEO4J_ENCRYPTED: {os.getenv('NEO4J_ENCRYPTED', 'NOT SET')}")
    print(f"   USE_REAL_MCP: {os.getenv('USE_REAL_MCP', 'NOT SET')}")
    
    # Test MCP connection with node count query
    print(f"\n📊 Querying via MCP server...")
    
    queries = [
        ("All nodes", "MATCH (n) RETURN count(n) as total_nodes"),
        ("Task nodes", "MATCH (n:TASK) RETURN count(n) as task_count"),
        ("Project nodes", "MATCH (n:PROJECT) RETURN count(n) as project_count"), 
        ("Area nodes", "MATCH (n:AREA) RETURN count(n) as area_count"),
        ("Goal nodes", "MATCH (n:GOAL) RETURN count(n) as goal_count"),
        ("All relationships", "MATCH ()-[r]->() RETURN count(r) as total_relationships"),
    ]
    
    results = {}
    
    for name, query in queries:
        try:
            print(f"   Running: {name}...")
            result = adapter._execute_mcp_command("execute_cypher", {
                "query": query,
                "parameters": {}
            })
            
            if result.get("success"):
                records = result.get("records", [])
                if records:
                    count = list(records[0].values())[0]
                    results[name] = count
                    print(f"   ✅ {name}: {count}")
                else:
                    results[name] = 0
                    print(f"   ⚠️ {name}: 0")
            else:
                print(f"   ❌ {name}: FAILED - {result.get('error')}")
                results[name] = "ERROR"
                
        except Exception as e:
            print(f"   ❌ {name}: EXCEPTION - {e}")
            results[name] = "EXCEPTION"
    
    # Summary
    print(f"\n📋 Database Summary:")
    for name, count in results.items():
        print(f"   {name}: {count}")
    
    # Check for orphaned tasks if we have data
    if results.get("Task nodes", 0) > 0:
        print(f"\n🔗 Checking task relationships...")
        orphan_query = """
        MATCH (t:TASK)
        WHERE NOT (t)-[:BELONGS_TO]->() 
        AND NOT (t)-[:CONTRIBUTES_TO]->()
        RETURN count(t) as orphaned_tasks
        """
        
        try:
            result = adapter._execute_mcp_command("execute_cypher", {
                "query": orphan_query,
                "parameters": {}
            })
            
            if result.get("success"):
                records = result.get("records", [])
                if records:
                    orphan_count = records[0]["orphaned_tasks"]
                    print(f"   ⚠️ Orphaned tasks (no relationships): {orphan_count}")
                    
                    if orphan_count > 0:
                        print(f"\n💡 Found {orphan_count} orphaned tasks!")
                        print(f"   These are the yellow nodes with no connections in your graph.")
                        print(f"   Run cleanup to establish relationships.")
            
        except Exception as e:
            print(f"   ❌ Orphan check failed: {e}")
    
    # Connection verification
    print(f"\n🎯 Database Status:")
    total_nodes = results.get("All nodes", 0)
    if total_nodes == 0:
        print(f"   ❌ Database appears empty or disconnected")
        print(f"   📝 Check MCP server configuration and credentials")
    elif total_nodes > 0:
        print(f"   ✅ Connected to database with {total_nodes} nodes")
        if results.get("Task nodes", 0) > 0:
            print(f"   📊 Task data exists - relationship cleanup may be needed")

if __name__ == "__main__":
    main()