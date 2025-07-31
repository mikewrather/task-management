#!/usr/bin/env python3
import json
from neo4j import GraphDatabase

# Database connection details
URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "agent-db-password"

def get_voice_tasks():
    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    
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
    
    with driver.session() as session:
        result = session.run(query)
        records = list(result)
        
    driver.close()
    
    # Convert to JSON-serializable format
    data = []
    for record in records:
        data.append({
            "title": record["title"],
            "project_name": record["project_name"],
            "project_id": record["project_id"],
            "area_name": record["area_name"],
            "contexts": record["contexts"]
        })
    
    return json.dumps(data, indent=2)

if __name__ == "__main__":
    print(get_voice_tasks())