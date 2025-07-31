#!/usr/bin/env python3

import json
from neo4j import GraphDatabase

# Neo4j connection details (from .mcp.json)
uri = "bolt://localhost:7687"
username = "neo4j"
password = "agent-db-password"

# The Cypher query
query = """
MATCH (t:TASK)
WHERE t.source = 'voice' AND t.created IS NOT NULL
OPTIONAL MATCH (t)-[:BELONGS_TO]->(p:PROJECT)
OPTIONAL MATCH (p)-[:BELONGS_TO]->(a:AREA)
RETURN t.name as title, p.name as project_name, p.notion_id as project_id,
       a.name as area_name, t.contexts as contexts
ORDER BY t.created DESC
LIMIT 20
"""

# Connect and execute
driver = GraphDatabase.driver(uri, auth=(username, password), encrypted=False)

try:
    with driver.session() as session:
        result = session.run(query)
        records = []
        for record in result:
            records.append({
                "title": record["title"],
                "project_name": record["project_name"],
                "project_id": record["project_id"],
                "area_name": record["area_name"],
                "contexts": record["contexts"]
            })
        print(json.dumps(records))
finally:
    driver.close()