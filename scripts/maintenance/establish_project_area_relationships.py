#!/usr/bin/env python3
"""Establish missing project-area relationships in GraphRAG"""

import subprocess
import json
import os

# Change to project directory
os.chdir("/home/mike/development/task-management")

# Claude path
claude_path = "/home/mike/.nvm/versions/node/v24.2.0/bin/claude"

# Step 1: Find projects without area relationships
print("🔍 Finding projects without area relationships...\n")

query_prompt = """Use the mcp__agent-db__execute_cypher tool to find projects without area relationships:
{
  "query": "MATCH (p:PROJECT) WHERE NOT (p)-[:BELONGS_TO]->(:AREA) RETURN p.name as project_name, p.notion_id as project_id ORDER BY p.name",
  "parameters": {}
}

Return ONLY the raw JSON result."""

cmd = [
    claude_path,
    "-p", query_prompt,
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        response = json.loads(result.stdout)
        if 'result' in response:
            # Parse the result
            try:
                projects = json.loads(response['result'])
                if projects:
                    print(f"Found {len(projects)} projects without area relationships:\n")
                    for p in projects:
                        print(f"  - {p['project_name']} (ID: {p['project_id']})")
                else:
                    print("✅ All projects have area relationships!")
                    exit(0)
            except:
                print("Could not parse projects list")
                print(response['result'])
                exit(1)
except Exception as e:
    print(f"Error: {e}")
    exit(1)

# Step 2: Get all areas to help with mapping
print("\n📋 Getting all areas...\n")

area_prompt = """Use the mcp__agent-db__execute_cypher tool to get all areas:
{
  "query": "MATCH (a:AREA) RETURN a.name as area_name, a.notion_id as area_id ORDER BY a.name",
  "parameters": {}
}

Return ONLY the raw JSON result."""

cmd[2] = area_prompt

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        response = json.loads(result.stdout)
        if 'result' in response:
            areas = json.loads(response['result'])
            print("Available areas:")
            for a in areas:
                print(f"  - {a['area_name']} (ID: {a['area_id']})")
except Exception as e:
    print(f"Error getting areas: {e}")

# Step 3: Map projects to areas based on names
print("\n🔗 Establishing relationships based on project names...\n")

# Manual mapping based on project names
mappings = [
    # Add mappings here based on the output
    # Format: (project_name, area_name)
]

# Common patterns
for project in projects:
    project_name = project['project_name']
    
    # Auto-detect some patterns
    if 'Sleep Worlds' in project_name or '[Sleep Worlds]' in project_name:
        mappings.append((project_name, 'Sleep Worlds'))
    elif 'Work' in project_name or 'Professional' in project_name:
        mappings.append((project_name, 'Work'))
    elif 'House' in project_name or 'Home' in project_name:
        mappings.append((project_name, 'House'))
    elif 'Health' in project_name or 'Fitness' in project_name:
        mappings.append((project_name, 'Health'))
    elif 'Personal' in project_name:
        mappings.append((project_name, 'Personal Development'))
    elif 'Development' in project_name and 'Sleep' not in project_name:
        mappings.append((project_name, 'Work'))

print(f"Proposed mappings ({len(mappings)}):")
for proj, area in mappings:
    print(f"  {proj} → {area}")

if not mappings:
    print("\n⚠️  No automatic mappings found. Please add manual mappings in the script.")
    exit(1)

# Step 4: Create the relationships
print("\n✨ Creating relationships...\n")

for project_name, area_name in mappings:
    create_prompt = f"""Use the mcp__agent-db__execute_cypher tool to create the relationship:
{{
  "query": "MATCH (p:PROJECT {{name: $project_name}}), (a:AREA {{name: $area_name}}) CREATE (p)-[:BELONGS_TO]->(a) RETURN p.name as project, a.name as area",
  "parameters": {{
    "project_name": "{project_name}",
    "area_name": "{area_name}"
  }}
}}

Return ONLY the raw JSON result."""
    
    cmd[2] = create_prompt
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"✅ Created: {project_name} → {area_name}")
        else:
            print(f"❌ Failed: {project_name} → {area_name}")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n🎉 Done! Run the script again to verify all relationships are established.")