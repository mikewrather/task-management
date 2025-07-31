#!/usr/bin/env python3
"""Execute Cypher query to get voice tasks with project/area relationships"""

import json
import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter
from voice_task_manager.utils.logging import VoiceLogger

# Enable real MCP
os.environ['USE_REAL_MCP'] = 'true'

# Initialize adapter
logger = VoiceLogger()
adapter = GraphRAGTaskAdapter(logger)

# Define the query
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
print("Executing Cypher query...")
response = adapter._execute_mcp_command("execute_cypher", {
    "query": query,
    "parameters": {}
})

# Print raw JSON result
print("\nRaw JSON Result:")
print(json.dumps(response, indent=2))