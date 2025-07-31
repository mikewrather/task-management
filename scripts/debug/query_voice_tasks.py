#!/usr/bin/env python3
import os
import sys
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Enable real MCP
os.environ['USE_REAL_MCP'] = 'true'

from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter

# Create adapter
adapter = GraphRAGTaskAdapter()

# Execute the Cypher query
query = """
        MATCH (t:TASK)
        WHERE t.source = 'voice' AND t.created IS NOT NULL
        OPTIONAL MATCH (t)-[:BELONGS_TO]->(p:PROJECT)
        OPTIONAL MATCH (p)-[:BELONGS_TO]->(a:AREA)
        RETURN t.name as title, p.name as project_name, p.notion_id as project_id,
               a.name as area_name, t.contexts as contexts
        ORDER BY t.created DESC
        LIMIT 20
        """

result = adapter._execute_mcp_command("execute_cypher", {
    "query": query,
    "parameters": {}
})

# Print only the raw JSON result
print(json.dumps(result))