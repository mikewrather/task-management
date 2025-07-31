#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/home/mike/development/task-management/src')

from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter

# Enable real MCP
os.environ['USE_REAL_MCP'] = 'true'

# Create adapter
adapter = GraphRAGTaskAdapter()

# Execute the query
response = adapter._execute_mcp_command("execute_cypher", {
    "query": "MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA) RETURN p.notion_id as project_id, p.name as name, a.notion_id as area_id, a.name as area_name",
    "parameters": {}
})

# Print only the results
import json
print(json.dumps(response))