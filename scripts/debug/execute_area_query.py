#!/usr/bin/env python3
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter

# Initialize adapter
adapter = GraphRAGTaskAdapter()

# Execute the query
query = """
MATCH (a:AREA)
RETURN a.notion_id as area_id, a.name as name
"""

try:
    # Use the _execute_mcp_command method with the execute_cypher tool
    result = adapter._execute_mcp_command("execute_cypher", {
        "query": query.strip(),
        "parameters": {}
    })
    print(json.dumps(result, indent=2))
except Exception as e:
    print(json.dumps({"error": str(e)}))