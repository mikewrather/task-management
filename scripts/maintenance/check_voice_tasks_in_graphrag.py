#!/usr/bin/env python3
"""Check which voice tasks are in GraphRAG vs SQLite database"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from voice_task_manager.utils.database import VoiceDatabase
from voice_task_manager.utils.logging import VoiceLogger
from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter

# Initialize components
logger = VoiceLogger()
database = VoiceDatabase()
graphrag_adapter = GraphRAGTaskAdapter(logger=logger)

print("🔍 Checking Voice Tasks in GraphRAG vs SQLite\n")

# Get recent voice files from SQLite
days_back = 30
start_date = datetime.now() - timedelta(days=days_back)
voice_files = database.get_files_by_date_range(start_date, datetime.now())

# Filter for completed files
completed_files = [f for f in voice_files if f.status == 'completed' and f.transcript]

print(f"SQLite Database:")
print(f"  - Total completed voice files (last {days_back} days): {len(completed_files)}")
print(f"  - Total voice files: {len(voice_files)}\n")

# Check GraphRAG
print("GraphRAG Database:")

# Count voice tasks in GraphRAG
count_query = "MATCH (t:TASK) WHERE t.source = 'voice' RETURN count(t) as count"
count_result = graphrag_adapter._execute_mcp_command('execute_cypher', {
    'query': count_query,
    'parameters': {}
})

if count_result and isinstance(count_result, list) and len(count_result) > 0:
    voice_task_count = count_result[0].get('count', 0)
    print(f"  - Voice tasks in GraphRAG: {voice_task_count}")
else:
    print("  - Could not get voice task count")
    voice_task_count = 0

# Get sample of voice tasks from GraphRAG
sample_query = """
MATCH (t:TASK) 
WHERE t.source = 'voice' 
RETURN t.name as name, t.created as created
ORDER BY t.created DESC
LIMIT 10
"""

sample_result = graphrag_adapter._execute_mcp_command('execute_cypher', {
    'query': sample_query,
    'parameters': {}
})

if sample_result and isinstance(sample_result, list):
    print(f"\nRecent voice tasks in GraphRAG:")
    for i, task in enumerate(sample_result, 1):
        print(f"  {i}. {task.get('name', 'Unknown')}")
        print(f"     Created: {task.get('created', 'Unknown')}")

# Summary
print(f"\n📊 Summary:")
print(f"  - Voice files in SQLite: {len(completed_files)}")
print(f"  - Voice tasks in GraphRAG: {voice_task_count}")
print(f"  - Difference: {len(completed_files) - voice_task_count} files not in GraphRAG")

if voice_task_count < len(completed_files):
    print(f"\n⚠️  {len(completed_files) - voice_task_count} voice files are missing from GraphRAG")
    print("  Run the reprocess script to add them.")
else:
    print("\n✅ All voice files appear to be in GraphRAG!")