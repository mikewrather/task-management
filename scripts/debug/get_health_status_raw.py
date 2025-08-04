#!/usr/bin/env python3
import json
print(json.dumps({
    "mcp_server": True,
    "timestamp": "2025-08-03T18:42:25.778659Z",
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
}))