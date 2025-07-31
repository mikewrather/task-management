#!/usr/bin/env python3
"""Temporary script to execute Cypher query for projects without area relationships"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter
from voice_task_manager.utils.logging import VoiceLogger
import json

def main():
    # Initialize adapter
    logger = VoiceLogger()
    adapter = GraphRAGTaskAdapter(logger)
    
    # Execute the Cypher query
    query = "MATCH (p:PROJECT) WHERE NOT (p)-[:BELONGS_TO]->(:AREA) RETURN p.name as project_name, p.notion_id as project_id ORDER BY p.name"
    
    response = adapter._execute_mcp_command("execute_cypher", {
        "query": query,
        "parameters": {}
    })
    
    # Print raw JSON result
    print(json.dumps(response, indent=2))

if __name__ == "__main__":
    main()