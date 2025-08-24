#!/usr/bin/env python3
"""
Test MCP connection through GraphRAG adapter
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter
import os

# Ensure we're using real MCP
os.environ['USE_REAL_MCP'] = 'true'

print("=" * 60)
print("Testing MCP Connection through GraphRAG Adapter")
print("=" * 60)

adapter = GraphRAGTaskAdapter()

# Test 1: Health check
print("\n1. Testing health check...")
health_response = adapter._execute_mcp_command("get_health_status", {})
print(f"Health check response: {health_response}")

# Test 2: Simple query
print("\n2. Testing Cypher query...")
query = "MATCH (n) RETURN DISTINCT labels(n) as labels, count(*) as count ORDER BY count DESC LIMIT 5"
query_response = adapter._execute_mcp_command("execute_cypher", {
    "query": query,
    "parameters": {}
})
print(f"Query response: {query_response}")

# Test 3: Check for TASK nodes specifically
print("\n3. Checking for TASK nodes...")
task_query = """
MATCH (n)
WHERE 'TASK' IN labels(n) OR 'TASK_MANAGEMENT:TASK' IN labels(n)
RETURN labels(n) as labels, count(*) as count
"""
task_response = adapter._execute_mcp_command("execute_cypher", {
    "query": task_query,
    "parameters": {}
})
print(f"Task nodes: {task_response}")

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)