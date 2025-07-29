#!/usr/bin/env python3
"""
Direct script to delete duplicate voice note tasks using NotionClient.
"""

import sys
import asyncio
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/home/mike/development/task-management')

async def main():
    print("🧹 Deleting Duplicate Voice Note Tasks (Direct Method)")
    print("=" * 60)
    
    try:
        # Import NotionClient directly
        from src.voice_task_manager.integrations.notion import NotionClient
        
        print("🔍 Initializing Notion client...")
        notion = NotionClient()
        
        print("📊 Fetching voice note tasks...")
        
        # Get voice tasks directly from NotionClient
        tasks = await notion.list_tasks(
            contexts=["voice"],
            limit=200  # Get more to capture all duplicates
        )
        
        if not tasks:
            print("✅ No tasks found!")
            return 0
        
        print(f"📋 Found {len(tasks)} voice note tasks total")
        
        # Group by title to find duplicates
        groups = {}
        for task in tasks:
            title = task.title.strip() if task.title else ""
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
        total_to_delete = 0
        
        for title, task_list in duplicates.items():
            print(f"\n📋 Group: '{title[:60]}...'")
            print(f"   Found {len(task_list)} copies")
            
            # Sort by creation date (keep oldest)
            task_list.sort(key=lambda t: t.created_at if t.created_at else datetime.min)
            oldest = task_list[0]
            to_delete = task_list[1:]
            
            print(f"   ✅ Keeping: {oldest.id} (created: {oldest.created_at})")
            
            # Delete the duplicates
            for i, task in enumerate(to_delete):
                task_id = task.id
                print(f"   🗑️  Deleting {i+1}/{len(to_delete)}: {task_id}")
                total_to_delete += 1
                
                try:
                    success = await notion.delete_task(task_id)
                    if success:
                        print(f"      ✅ Successfully deleted")
                        total_deleted += 1
                    else:
                        print(f"      ❌ Failed to delete")
                except Exception as e:
                    print(f"      ❌ Exception: {e}")
        
        print(f"\n📊 Summary:")
        print(f"   • Total duplicates found: {total_to_delete}")
        print(f"   • Successfully deleted: {total_deleted}")
        print(f"   • Failed deletions: {total_to_delete - total_deleted}")
        
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