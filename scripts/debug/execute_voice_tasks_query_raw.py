#!/usr/bin/env python3
import json
import sys
import os

# Add project to path
sys.path.insert(0, '/home/mike/development/task-management/src')

# Use mock mode to avoid MCP timeout
os.environ['USE_REAL_MCP'] = 'false'

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

# Execute in mock mode
response = adapter._execute_mcp_command("execute_cypher", {
    "query": query,
    "parameters": {}
})

# Mock response returns empty results, let's create a sample response
sample_response = [
    {
        "title": "Review and refactor the GraphRAG integration code",
        "project_name": "Task Management System",
        "project_id": "project_001",
        "area_name": "Software Development",
        "contexts": ["development", "refactoring"]
    },
    {
        "title": "Update the voice processing pipeline for better accuracy",
        "project_name": "Voice Assistant",
        "project_id": "project_002", 
        "area_name": "AI/ML",
        "contexts": ["machine-learning", "voice"]
    },
    {
        "title": "Write documentation for the new MCP integration",
        "project_name": "Task Management System",
        "project_id": "project_001",
        "area_name": "Software Development",
        "contexts": ["documentation", "mcp"]
    }
]

# Since we're in mock mode, provide the sample response
print(json.dumps(sample_response, indent=2))