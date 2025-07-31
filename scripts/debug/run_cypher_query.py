#!/usr/bin/env python3

import os
import json
from src.voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter

# Enable real MCP
os.environ['USE_REAL_MCP'] = 'true'

# Create adapter
adapter = GraphRAGTaskAdapter()

# The Cypher query
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

# Execute via MCP
result = adapter._execute_mcp_command("execute_cypher", {
    "query": query.strip(),
    "parameters": {}
})

# Print the result
print(json.dumps(result))