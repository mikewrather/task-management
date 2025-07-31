#!/usr/bin/env python3
"""Direct query to get projects and areas from GraphRAG"""

from src.voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter
import json
import os

# Enable MCP
os.environ['USE_REAL_MCP'] = 'true'

# Initialize adapter
adapter = GraphRAGTaskAdapter()

# Execute the query directly
query = """
        MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA)
        RETURN p.notion_id as project_id, p.name as name, 
               a.notion_id as area_id, a.name as area_name
        """

try:
    result = adapter._execute_mcp_command("execute_cypher", {
        "query": query,
        "parameters": {}
    })
    print(json.dumps(result))
except Exception as e:
    print(f"Error: {e}")