#!/usr/bin/env python3
import json
from neo4j import GraphDatabase
import os

# Load database credentials
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "agent-db-password")

# Create driver
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

# Execute query
query = """
MATCH (a:AREA)
RETURN a.notion_id as area_id, a.name as name
"""

try:
    with driver.session() as session:
        result = session.run(query)
        records = list(result)
        
        # Convert to JSON-serializable format
        data = []
        for record in records:
            data.append(dict(record))
        
        # Print JSON result
        print(json.dumps(data, indent=2))
        
except Exception as e:
    print(json.dumps({"error": str(e)}))
finally:
    driver.close()