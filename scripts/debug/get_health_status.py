#!/usr/bin/env python3
"""Get health status directly from Neo4j"""

import json
from neo4j import GraphDatabase

# Neo4j connection details (from .mcp.json)
uri = "bolt://localhost:7687"
username = "neo4j"
password = "agent-db-password"

# Connect to Neo4j
driver = GraphDatabase.driver(uri, auth=(username, password), encrypted=False)

health_status = {
    "status": "unknown",
    "details": {
        "database": {
            "connected": False,
            "error": None
        },
        "node_counts": {}
    }
}

try:
    with driver.session() as session:
        # Check connection is working
        result = session.run("RETURN 1 as ping")
        result.single()
        
        health_status["status"] = "healthy"
        health_status["details"]["database"]["connected"] = True
        
        # Get node counts for all entity types
        entity_types = ['TASK', 'PROJECT', 'AREA', 'USER', 'CONTEXT', 'TAG', 'INTERACTION']
        
        for entity_type in entity_types:
            count_result = session.run(f"MATCH (n:{entity_type}) RETURN count(n) as count")
            count = count_result.single()["count"]
            health_status["details"]["node_counts"][entity_type.lower()] = count
            
except Exception as e:
    health_status["status"] = "error"
    health_status["details"]["database"]["error"] = str(e)
    
finally:
    driver.close()

# Output the result as JSON
print(json.dumps(health_status, indent=2))