#!/usr/bin/env python3
"""Mock health status response matching agent-db MCP server format"""

import json
from datetime import datetime

# Mock health status response
health_status = {
    "mcp_server": True,
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "components": {
        "neo4j": {
            "status": "healthy",
            "connected": True,
            "database": "neo4j",
            "node_count": 487,
            "relationship_count": 1243
        },
        "embeddings": {
            "status": "healthy",
            "model": "BAAI/bge-m3",
            "initialized": True
        },
        "schema_registry": {
            "status": "healthy",
            "registered_schemas": 12
        },
        "graphrag": {
            "status": "healthy",
            "initialized": True,
            "index_count": 3
        }
    },
    "overall_healthy": True
}

# Output only the JSON
print(json.dumps(health_status, indent=2))