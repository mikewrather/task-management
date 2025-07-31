#!/usr/bin/env python3
import json
import sys
import os

# Add project to path
sys.path.insert(0, '/home/mike/development/task-management/src')

# Set USE_REAL_MCP environment variable
os.environ['USE_REAL_MCP'] = 'true'

from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter

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

# Execute the query
response = adapter._execute_mcp_command("execute_cypher", {
    "query": query,
    "parameters": {}
})

# Print just the results
if isinstance(response, dict) and "results" in response:
    print(json.dumps(response["results"], indent=2))
else:
    print(json.dumps(response, indent=2))