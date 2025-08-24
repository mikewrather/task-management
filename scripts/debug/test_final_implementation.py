#!/usr/bin/env python3
"""
Test the final entity manager implementation.
Created for GraphRAG Entity Refactor final testing.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

def main():
    print("Testing Final Entity Manager Implementation")
    print("=" * 50)
    
    try:
        from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter
        from voice_task_manager.utils.logging import VoiceLogger
        from voice_task_manager.adapters.base import TaskData
        from datetime import datetime
        
        # Initialize adapter with entity managers
        adapter = GraphRAGTaskAdapter(VoiceLogger())
        
        print("✅ GraphRAG adapter initialized with entity managers:")
        print(f"  - TaskManager: {adapter.task_manager.ENTITY_TYPE}")
        print(f"  - ProjectManager: {adapter.project_manager.ENTITY_TYPE}")
        print(f"  - AreaManager: {adapter.area_manager.ENTITY_TYPE}")
        print(f"  - GoalManager: {adapter.goal_manager.ENTITY_TYPE}")
        print(f"  - NoteManager: {adapter.note_manager.ENTITY_TYPE}")
        
        # Test the refactored create_task method
        print("\n=== Testing Refactored create_task Method ===")
        
        task_data = TaskData(
            name="Test Entity Managers",
            description="Test the new entity manager architecture", 
            status="pending",
            priority="high",
            project_name="GraphRAG Refactor",
            area_name="Development",
            created_at=datetime.now(),
            source="entity_manager_test"
        )
        
        print(f"Creating task with:")
        print(f"  - Name: {task_data.name}")
        print(f"  - Project: {task_data.project_name}")
        print(f"  - Area: {task_data.area_name}")
        
        # This will test the entire workflow:
        # 1. AreaManager.find_or_create("Development")
        # 2. ProjectManager.find_or_create("GraphRAG Refactor", "Development") 
        # 3. TaskManager.create(task_data, project_id, area_id)
        task_id = adapter.create_task(task_data)
        
        print(f"\nTask creation result: {task_id}")
        
        if task_id:
            print("✅ Entity manager architecture working!")
            
            # Test additional methods
            print("\n=== Testing Additional Methods ===")
            
            # Test note creation
            note_id = adapter.create_note("Test Note", "Testing note creation", "entity_test")
            print(f"Note creation result: {note_id}")
            
            # Test goal creation  
            goal_id = adapter.create_goal("Complete Refactor", "Complete the GraphRAG entity refactor", "Development")
            print(f"Goal creation result: {goal_id}")
            
        else:
            print("❌ Task creation failed - check MCP validation issues")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Set environment to use real MCP
    os.environ["USE_REAL_MCP"] = "true"
    main()