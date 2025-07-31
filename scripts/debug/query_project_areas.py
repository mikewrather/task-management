#!/usr/bin/env python3
import json
import os
from src.voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter

def main():
    # Enable real MCP
    os.environ['USE_REAL_MCP'] = 'true'
    
    adapter = GraphRAGTaskAdapter()
    
    query = """
    MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA) 
    RETURN p.notion_id as project_id, p.name as name, a.notion_id as area_id, a.name as area_name
    """
    
    result = adapter._execute_mcp_command("execute_cypher", {
        "query": query,
        "parameters": {}
    })
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()