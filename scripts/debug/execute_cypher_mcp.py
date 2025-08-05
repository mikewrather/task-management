#!/usr/bin/env python3
"""Execute Cypher query using MCP directly"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

# Silence all logging
import logging
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger().setLevel(logging.CRITICAL)

from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter

# Initialize adapter with no logging
adapter = GraphRAGTaskAdapter(logger=None)

# Execute the query using MCP
query = """
        MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA)
        RETURN p.notion_id as project_id, p.name as name, 
               a.notion_id as area_id, a.name as area_name
        """

result = adapter._execute_mcp_command("execute_cypher", {
    "query": query,
    "parameters": {}
})

# Print only the JSON result
import json
if isinstance(result, dict) and result.get('success'):
    print(json.dumps(result))
else:
    print(json.dumps({"error": "Failed to execute query", "details": result}))