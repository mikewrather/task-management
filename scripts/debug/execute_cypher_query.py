#!/usr/bin/env python3
"""Execute a Cypher query directly against Neo4j"""

import json
import os
import sys
from pathlib import Path
from neo4j import GraphDatabase

# Neo4j connection details
NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'agent-db-password')

def execute_query(query, parameters=None):
    """Execute a Cypher query and return results"""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            result = session.run(query, parameters or {})
            # Convert result to list of dicts
            records = []
            for record in result:
                records.append(dict(record))
            return records
    finally:
        driver.close()

if __name__ == "__main__":
    # The query to execute
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
    
    try:
        result = execute_query(query)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e), "type": type(e).__name__}, indent=2))