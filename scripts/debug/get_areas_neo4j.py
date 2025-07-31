#!/usr/bin/env python3
"""Get areas directly from Neo4j"""

from neo4j import GraphDatabase
import json

# Neo4j connection details
uri = "neo4j://localhost:7687"
username = "neo4j"
password = "agent-db-password"

# Create driver
driver = GraphDatabase.driver(uri, auth=(username, password))

try:
    with driver.session() as session:
        # Execute the query
        result = session.run("""
            MATCH (a:AREA)
            RETURN a.notion_id as area_id, a.name as name
        """)
        
        # Convert to list of dictionaries
        areas = []
        for record in result:
            areas.append({
                "area_id": record["area_id"],
                "name": record["name"]
            })
        
        # Print as JSON
        print(json.dumps(areas))
        
finally:
    driver.close()