#!/usr/bin/env python3
from py2neo import Graph
import json

# Connect to Neo4j using bolt protocol
graph = Graph("bolt://localhost:7687", auth=("neo4j", "2024Secure!Gd8"))

# Execute the query
query = """
MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA)
RETURN p.notion_id as project_id, p.name as name, a.notion_id as area_id, a.name as area_name
"""

result = graph.run(query).data()
print(json.dumps(result, indent=2))