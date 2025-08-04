#!/usr/bin/env python3
"""Direct health status query from agent-db MCP server."""

import subprocess
import json
import sys

def get_health_status():
    """Query health status from agent-db MCP server."""
    # Use the MCP CLI to query the agent-db server
    cmd = [
        "mcp-cli",
        "call",
        "agent-db",
        "get_health_status",
        "{}"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout
        else:
            # Fallback to direct Neo4j query
            return query_neo4j_directly()
    except Exception as e:
        return query_neo4j_directly()

def query_neo4j_directly():
    """Query Neo4j directly using bolt protocol."""
    try:
        from neo4j import GraphDatabase
        
        # Connection parameters
        uri = "bolt://localhost:7687"
        auth = ("neo4j", "agent-db-password")
        
        driver = GraphDatabase.driver(uri, auth=auth)
        
        with driver.session() as session:
            # Get node counts
            result = session.run("""
                MATCH (n)
                WITH labels(n)[0] AS label, count(n) AS count
                RETURN label, count
                ORDER BY label
            """)
            
            nodes = {}
            for record in result:
                nodes[record["label"]] = record["count"]
            
            # Get relationship counts
            result = session.run("""
                MATCH ()-[r]->()
                WITH type(r) AS type, count(r) AS count
                RETURN type, count
                ORDER BY type
            """)
            
            relationships = {}
            for record in result:
                relationships[record["type"]] = record["count"]
            
            # Build health status response
            health_status = {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "name": "neo4j",
                    "version": "5.x"
                },
                "statistics": {
                    "nodes": nodes,
                    "relationships": relationships,
                    "total_nodes": sum(nodes.values()),
                    "total_relationships": sum(relationships.values())
                }
            }
            
            return json.dumps(health_status, indent=2)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "database": {
                "connected": False
            }
        })

if __name__ == "__main__":
    print(get_health_status())