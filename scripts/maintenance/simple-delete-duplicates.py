#!/usr/bin/env python3
"""
Simple script to delete duplicate voice note tasks using MCP server functionality.
"""

import sys
import asyncio
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/home/mike/development/task-management')

async def main():
    print("🧹 Deleting Duplicate Voice Note Tasks")
    print("=" * 50)
    
    try:
        # Import MCP server functions
        from notion_mcp_server import list_tasks, delete_task
        
        print("🔍 Fetching voice note tasks...")
        
        # Get voice tasks
        result = await list_tasks(context="voice", limit=100, format="json")
        
        if not result.get("success", False):
            print(f"❌ Failed to fetch tasks: {result.get('error', 'Unknown error')}")
            return 1
        
        tasks = result.get("data", [])
        print(f"📊 Found {len(tasks)} voice note tasks")
        
        if not tasks:
            print("✅ No tasks found!")
            return 0
        
        # Group by title to find duplicates
        groups = {}
        for task in tasks:
            title = task.get("title", "").strip()
            if title not in groups:
                groups[title] = []
            groups[title].append(task)
        
        # Find duplicate groups
        duplicates = {title: task_list for title, task_list in groups.items() if len(task_list) > 1}
        
        if not duplicates:
            print("✅ No duplicate tasks found!")
            return 0
        
        print(f"🔍 Found {len(duplicates)} groups with duplicates:")
        
        total_deleted = 0
        for title, task_list in duplicates.items():
            print(f"\n📋 Group: '{title[:60]}...'")
            print(f"   Found {len(task_list)} copies")
            
            # Sort by creation date (keep oldest)
            task_list.sort(key=lambda t: t.get("created_at", ""))
            oldest = task_list[0]
            to_delete = task_list[1:]
            
            print(f"   ✅ Keeping: {oldest['task_id']} (created: {oldest.get('created_at', 'Unknown')})")
            
            # Delete the duplicates
            for i, task in enumerate(to_delete):
                task_id = task['task_id']
                print(f"   🗑️  Deleting {i+1}/{len(to_delete)}: {task_id}")
                
                try:
                    delete_result = await delete_task(task_id=task_id, confirm=True)
                    if delete_result.get("success", False):
                        print(f"      ✅ Success")
                        total_deleted += 1
                    else:
                        print(f"      ❌ Failed: {delete_result.get('error', 'Unknown error')}")
                except Exception as e:
                    print(f"      ❌ Exception: {e}")
        
        print(f"\n📊 Summary:")
        print(f"   • Total duplicates found: {sum(len(tasks) - 1 for tasks in duplicates.values())}")
        print(f"   • Successfully deleted: {total_deleted}")
        print(f"   • Failed deletions: {sum(len(tasks) - 1 for tasks in duplicates.values()) - total_deleted}")
        
        if total_deleted > 0:
            print(f"\n✅ Cleanup complete! Deleted {total_deleted} duplicate tasks.")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))