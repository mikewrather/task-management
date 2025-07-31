#!/usr/bin/env python3
"""Re-process recent voice tasks into GraphRAG with the fixed adapter"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from voice_task_manager.utils.database import VoiceDatabase
from voice_task_manager.utils.logging import VoiceLogger
from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter
from voice_task_manager.processors.claude_processor import ClaudeVoiceProcessor
from voice_task_manager.adapters.base import TaskData

# Initialize components
logger = VoiceLogger()
database = VoiceDatabase()
graphrag_adapter = GraphRAGTaskAdapter(logger=logger)
claude_processor = ClaudeVoiceProcessor(adapter=graphrag_adapter, logger=logger)

print("🔄 Re-processing Voice Tasks into GraphRAG\n")
print("This will:")
print("1. Find recent voice tasks in the database")
print("2. Re-process them with Claude for proper categorization")
print("3. Create them in GraphRAG with relationships\n")

# Get recent voice files (last 7 days)
days_back = 7
start_date = datetime.now() - timedelta(days=days_back)
voice_files = database.get_files_by_date_range(start_date, datetime.now())

# Filter for completed files with transcripts
completed_files = [f for f in voice_files if f.status == 'completed' and f.transcript]

print(f"Found {len(completed_files)} completed voice files from the last {days_back} days\n")

if not completed_files:
    print("⚠️  No completed voice files found to re-process")
    exit(0)

# Show what we'll process
for i, vf in enumerate(completed_files[:10], 1):  # Show first 10
    print(f"{i}. {vf.file_id}")
    print(f"   Transcript: {vf.transcript[:80]}..." if len(vf.transcript) > 80 else f"   Transcript: {vf.transcript}")
    print(f"   Processed: {vf.processed_at}")
    print()

if len(completed_files) > 10:
    print(f"... and {len(completed_files) - 10} more files\n")

# Auto-proceed in script mode
print("\n🚀 Proceeding with re-processing...")

print("\n🚀 Starting re-processing...\n")

# Process each file
success_count = 0
error_count = 0
total_tasks_created = 0

for i, voice_file in enumerate(completed_files, 1):
    print(f"\n[{i}/{len(completed_files)}] Processing {voice_file.file_id}...")
    
    try:
        # Re-process with Claude to get proper categorization
        tasks = claude_processor.process_transcript(
            voice_file.transcript,
            voice_file.file_id
        )
        
        if not tasks:
            print("  ⚠️  No tasks extracted")
            continue
        
        # Create each task in GraphRAG
        created_count = 0
        for task in tasks:
            try:
                # Check if task already exists in GraphRAG
                # (This is a simple check - could be enhanced)
                existing_query = f"""
                MATCH (t:TASK)
                WHERE t.name = $name AND t.source = 'voice'
                RETURN t.id as task_id
                LIMIT 1
                """
                
                existing = graphrag_adapter._execute_mcp_command('execute_cypher', {
                    'query': existing_query,
                    'parameters': {'name': task.name}
                })
                
                if existing and len(existing) > 0:
                    print(f"  ⏩ Skipping '{task.name}' - already exists")
                    continue
                
                # Create the task
                task_id = graphrag_adapter.create_task(task)
                if task_id:
                    created_count += 1
                    print(f"  ✅ Created: '{task.name}' → {task.project_name or 'No Project'}")
                else:
                    print(f"  ❌ Failed to create: '{task.name}'")
                    
            except Exception as e:
                print(f"  ❌ Error creating task: {e}")
        
        if created_count > 0:
            success_count += 1
            total_tasks_created += created_count
            print(f"  🎯 Created {created_count} task(s) in GraphRAG")
        
    except Exception as e:
        error_count += 1
        print(f"  ❌ Error processing file: {e}")

# Summary
print("\n" + "="*60)
print("📊 Re-processing Summary:")
print(f"  - Files processed: {len(completed_files)}")
print(f"  - Successful: {success_count}")
print(f"  - Errors: {error_count}")
print(f"  - Total tasks created: {total_tasks_created}")
print("\n✅ Re-processing complete!")

# Verify the results
print("\n🔍 Verifying GraphRAG state...\n")

# Count tasks in GraphRAG
count_query = "MATCH (t:TASK) WHERE t.source = 'voice' RETURN count(t) as count"
count_result = graphrag_adapter._execute_mcp_command('execute_cypher', {
    'query': count_query,
    'parameters': {}
})

if count_result:
    if isinstance(count_result, list) and len(count_result) > 0:
        task_count = count_result[0].get('count', 0)
        print(f"📊 Total voice tasks in GraphRAG: {task_count}")
    else:
        print("⚠️  Could not get task count")

print("\n🎉 Done!")