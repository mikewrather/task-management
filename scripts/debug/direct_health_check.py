#!/usr/bin/env python3

import json
from neo4j import GraphDatabase
import sys

# Neo4j connection details (from .mcp.json)
uri = "bolt://localhost:7687"
username = "neo4j"
password = "agent-db-password"

def check_health():
    """Check the health of the Neo4j GraphRAG database"""
    health_status = {
        "success": False,
        "components": {
            "neo4j": {
                "status": "unknown",
                "message": ""
            },
            "graphrag": {
                "status": "unknown",
                "node_counts": {}
            }
        },
        "message": ""
    }
    
    try:
        # Connect to Neo4j
        driver = GraphDatabase.driver(uri, auth=(username, password), encrypted=False)
        
        with driver.session() as session:
            # Test basic connectivity
            result = session.run("RETURN 1 as test")
            test_value = result.single()["test"]
            
            if test_value == 1:
                health_status["components"]["neo4j"]["status"] = "healthy"
                health_status["components"]["neo4j"]["message"] = "Neo4j connection successful"
                
                # Get node counts for GraphRAG entities
                node_types = ["TASK", "PROJECT", "AREA", "RESOURCE", "TAG", "CONTACT", "ITEM"]
                node_counts = {}
                
                for node_type in node_types:
                    count_result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                    count = count_result.single()["count"]
                    node_counts[node_type] = count
                
                health_status["components"]["graphrag"]["status"] = "healthy"
                health_status["components"]["graphrag"]["node_counts"] = node_counts
                health_status["success"] = True
                health_status["message"] = "All systems operational"
            else:
                health_status["components"]["neo4j"]["status"] = "unhealthy"
                health_status["components"]["neo4j"]["message"] = "Connection test failed"
                health_status["message"] = "Neo4j connection test failed"
                
        driver.close()
        
    except Exception as e:
        health_status["components"]["neo4j"]["status"] = "unhealthy"
        health_status["components"]["neo4j"]["message"] = str(e)
        health_status["message"] = f"Failed to connect to Neo4j: {str(e)}"
    
    return health_status

if __name__ == "__main__":
    health = check_health()
    print(json.dumps(health, indent=2))