#!/usr/bin/env python3
"""
Test entity managers to verify they work correctly.
Created for GraphRAG Entity Refactor Phase 4.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

def main():
    print("Testing Entity Managers")
    print("=" * 30)
    
    try:
        from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter
        from voice_task_manager.utils.logging import VoiceLogger
        from voice_task_manager.adapters.base import TaskData
        from datetime import datetime
        
        # Initialize adapter with entity managers
        adapter = GraphRAGTaskAdapter(VoiceLogger())
        
        print("✅ GraphRAG adapter initialized with entity managers")
        print(f"- Task Manager: {type(adapter.task_manager).__name__}")
        print(f"- Project Manager: {type(adapter.project_manager).__name__}")
        print(f"- Area Manager: {type(adapter.area_manager).__name__}")
        print(f"- Goal Manager: {type(adapter.goal_manager).__name__}")
        print(f"- Note Manager: {type(adapter.note_manager).__name__}")
        
        # Test 1: Create area
        print("\n=== Test 1: Create Area ===")
        area_id = adapter.create_area("Health Test", "Test area for health-related tasks")
        print(f"Area creation result: {area_id}")
        
        # Test 2: Create project  
        print("\n=== Test 2: Create Project ===")
        project_id = adapter.create_project("Medical Appointments Test", "Test project for medical appointments", "Health Test")
        print(f"Project creation result: {project_id}")
        
        # Test 3: Create task
        print("\n=== Test 3: Create Task ===")
        task_data = TaskData(
            name="Call Dr. Smith Test",
            description="Test task - call doctor about test results", 
            status="pending",
            priority="high",
            project_name="Medical Appointments Test",
            area_name="Health Test",
            created_at=datetime.now(),
            source="test_script"
        )
        
        task_id = adapter.create_task(task_data)
        print(f"Task creation result: {task_id}")
        
        # Test 4: Create note
        print("\n=== Test 4: Create Note ===")
        note_id = adapter.create_note("Test Note", "This is a test note content", "testing context")
        print(f"Note creation result: {note_id}")
        
        print("\n=== Test Summary ===")
        if all([area_id, project_id, task_id, note_id]):
            print("✅ All entity types created successfully!")
        else:
            print("❌ Some entity creation failed")
            print(f"Results: Area={area_id}, Project={project_id}, Task={task_id}, Note={note_id}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Set environment to use real MCP
    os.environ["USE_REAL_MCP"] = "true"
    main()