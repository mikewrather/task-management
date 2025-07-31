#!/usr/bin/env python3
"""Execute Cypher query directly using GraphRAG adapter"""

import os
import sys
import json

# Add project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Enable real MCP
os.environ['USE_REAL_MCP'] = 'true'

from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter

# Create adapter
adapter = GraphRAGTaskAdapter()

# Execute Cypher query
query = """
        MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA)
        RETURN p.notion_id as project_id, p.name as name, 
               a.notion_id as area_id, a.name as area_name
        """

result = adapter._execute_mcp_command(
    "execute_cypher",
    {
        "query": query,
        "parameters": {}
    }
)

# Print only the raw JSON result
print(json.dumps(result))