#!/usr/bin/env python3
import os
import sys
import json

# Silence all output
sys.stderr = open(os.devnull, 'w')
old_stdout = sys.stdout
sys.stdout = open(os.devnull, 'w')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

try:
    from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter
    
    adapter = GraphRAGTaskAdapter()
    
    query = """
        MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA)
        RETURN p.notion_id as project_id, p.name as name, 
               a.notion_id as area_id, a.name as area_name
        """
    
    result = adapter._execute_mcp_command("execute_cypher", {
        "query": query,
        "parameters": {}
    })
    
    # Restore stdout for final output
    sys.stdout = old_stdout
    
    # Output only the results if successful
    if isinstance(result, dict) and result.get('success'):
        print(json.dumps(result))
    else:
        print(json.dumps({"error": "Query failed"}))
        
except Exception as e:
    sys.stdout = old_stdout
    print(json.dumps({"error": str(e)}))