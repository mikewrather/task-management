#!/usr/bin/env python3
"""Direct health status query without MCP"""

import sys
import json
import os
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import from the project-agents MCP server directly
agents_path = "/home/mike/development/project-agents"
if os.path.exists(agents_path):
    sys.path.insert(0, agents_path)
    try:
        from project_agents_mcp.handlers import get_health_status
        
        # Call the health status function directly
        result = get_health_status({})
        
        # Output only the JSON result
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "type": type(e).__name__
        }))
else:
    print(json.dumps({
        "error": "project-agents directory not found",
        "path": agents_path
    }))