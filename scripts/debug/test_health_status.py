#!/usr/bin/env python3
"""Test MCP health status directly"""

import os
import sys
sys.path.insert(0, '/home/mike/development/task-management/src')

from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter

# Enable real MCP
os.environ['USE_REAL_MCP'] = 'true'

# Create adapter
adapter = GraphRAGTaskAdapter()

# Execute health status check
result = adapter._execute_mcp_command("get_health_status", {})

# Print the result
import json
print(json.dumps(result, indent=2))