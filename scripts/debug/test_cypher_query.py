#!/usr/bin/env python3
"""Test Cypher query execution directly"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter
from voice_task_manager.utils.env_handler import EnvHandler

# Load environment
env = EnvHandler()

# Initialize adapter
adapter = GraphRAGTaskAdapter(env)

# Execute the query
query = """
        MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA)
        RETURN p.notion_id as project_id, p.name as name, 
               a.notion_id as area_id, a.name as area_name
        """

try:
    result = adapter._execute_cypher(query, {})
    print(result)
except Exception as e:
    print(f"Error: {e}")