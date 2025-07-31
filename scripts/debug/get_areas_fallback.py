#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/home/mike/development/task-management/src')

from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter

# Don't use real MCP, let it fallback to mock
os.environ['USE_REAL_MCP'] = 'false'
adapter = GraphRAGTaskAdapter()

query = """
MATCH (a:AREA)
RETURN a.notion_id as area_id, a.name as name
"""

result = adapter._execute_mcp_command("execute_cypher", {"query": query, "parameters": {}})
import json
print(json.dumps(result))