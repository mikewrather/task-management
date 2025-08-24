#!/usr/bin/env python3
"""Test GraphRAG write functionality to diagnose task creation failures"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter
from src.voice_task_manager.adapters.base import TaskData
from src.voice_task_manager.utils.logging import VoiceLogger
from datetime import datetime
import os

# Ensure we use real MCP
os.environ['USE_REAL_MCP'] = 'true'

# Initialize logger
logger = VoiceLogger()

print("🔍 Testing GraphRAG Write Functionality")
print("=" * 50)

# Initialize adapter
print("\n📊 Initializing GraphRAG adapter...")
adapter = GraphRAGTaskAdapter(logger=logger)

# Test connection first
print("\n🔌 Testing connection...")
if adapter.test_connection():
    print("✅ Connection successful")
else:
    print("❌ Connection failed")
    sys.exit(1)

# Create test task
task = TaskData(
    name="Test task from debugging",
    description="Testing graph write failure diagnosis",
    status="not started",
    priority="medium",
    contexts=["debugging", "graphrag"],
    created_at=datetime.now(),
    source="voice",
    project_name="Test Project",
    area_name="Development"
)

print("\n📝 Creating task with following data:")
print(f"  Name: {task.name}")
print(f"  Project: {task.project_name}")
print(f"  Area: {task.area_name}")
print(f"  Status: {task.status}")
print(f"  Priority: {task.priority}")

print("\n⚡ Executing task creation...")
result = adapter.create_task(task)

print("\n" + "=" * 50)
if result:
    print(f"✅ SUCCESS: Task created with ID: {result}")
    
    # Try to retrieve the task to verify
    print(f"\n🔍 Retrieving task {result} to verify...")
    retrieved = adapter.get_task(result)
    if retrieved:
        print(f"✅ Task retrieved successfully")
        print(f"  Name: {retrieved.name}")
        print(f"  Project: {retrieved.project_name}")
    else:
        print("❌ Failed to retrieve created task")
else:
    print("❌ FAILED: Task creation failed")
    print("\n📋 Check logs for detailed error information:")
    print("  - logs/voice-errors.log")
    print("  - logs/voice-automation.log")