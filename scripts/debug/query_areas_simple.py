#!/usr/bin/env python3
"""Query areas directly from GraphRAG"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter

# Enable real MCP
os.environ['USE_REAL_MCP'] = 'true'

try:
    # Create adapter
    adapter = GraphRAGTaskAdapter()
    
    # Execute the query
    query = """
    MATCH (a:AREA)
    RETURN a.notion_id as area_id, a.name as name
    """
    
    result = adapter._execute_mcp_command("execute_cypher", {
        "query": query,
        "parameters": {}
    })
    
    # Print only the result
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"error": str(e)}))