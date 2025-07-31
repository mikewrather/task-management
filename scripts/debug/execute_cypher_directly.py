#!/usr/bin/env python3
"""Execute Cypher query using GraphRAG adapter"""

import os
import json

# Enable real MCP
os.environ['USE_REAL_MCP'] = 'true'

from src.voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter

# Create adapter and execute query
adapter = GraphRAGTaskAdapter()

query = """
        MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA)
        RETURN p.notion_id as project_id, p.name as name, 
               a.notion_id as area_id, a.name as area_name
        """

response = adapter._execute_mcp_command("execute_cypher", {
    "query": query,
    "parameters": {}
})

# Print raw JSON response
print(json.dumps(response, indent=2))