#!/usr/bin/env python3
"""
Script to delete duplicate voice note tasks from Notion database.

This script identifies and deletes duplicate voice note tasks, keeping only the oldest one.
All duplicates have the same title pattern: "Voice Note: I need a new task to create a view that will let me see all..."

Usage:
    python scripts/delete-duplicate-voice-tasks.py [--dry-run] [--limit N]
    
Options:
    --dry-run    Show what would be deleted without actually deleting
    --limit N    Limit number of deletions to N (for safety)
"""

import json
import subprocess
import sys
from datetime import datetime
from typing import List, Dict, Any
import argparse


def run_vtm_command(cmd: List[str]) -> Dict[str, Any]:
    """Run a vtm command and return parsed JSON result."""
    try:
        # Build command with proper virtual environment activation
        full_cmd = f"cd /home/mike/development/task-management && source .venv/bin/activate && {' '.join(cmd)}"
        
        result = subprocess.run(
            full_cmd,
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error running command: {' '.join(cmd)}")
            print(f"Error: {result.stderr}")
            return {"success": False, "error": result.stderr}
        
        # Parse JSON from stdout, filtering out log lines
        try:
            lines = result.stdout.strip().split('\n')
            # Find the JSON content (lines that start with { or [)
            json_lines = []
            json_started = False
            for line in lines:
                if line.strip().startswith('{') or line.strip().startswith('['):
                    json_started = True
                if json_started:
                    json_lines.append(line)
            
            if json_lines:
                json_content = '\n'.join(json_lines)
                return json.loads(json_content)
            else:
                # No JSON found, return raw output
                return {"success": True, "raw_output": result.stdout}
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Raw output: {result.stdout}")
            return {"success": False, "error": f"JSON decode error: {e}"}
            
    except Exception as e:
        print(f"Exception running command: {e}")
        return {"success": False, "error": str(e)}


def get_voice_tasks() -> List[Dict[str, Any]]:
    """Get all voice note tasks from Notion."""
    print("🔍 Fetching voice note tasks from Notion...")
    
    result = run_vtm_command(["vtm", "list", "tasks", "--context", "voice", "--limit", "100", "--format", "json"])
    
    if not result.get("success", True):
        print(f"❌ Failed to fetch tasks: {result.get('error', 'Unknown error')}")
        return []
    
    # Handle the response format
    if "data" in result:
        tasks = result["data"]
    else:
        # Assume the result itself is the task list
        tasks = result if isinstance(result, list) else []
    
    print(f"📊 Found {len(tasks)} voice note tasks total")
    return tasks


def identify_duplicates(tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group tasks by title to identify duplicates."""
    print("🔍 Identifying duplicate tasks by title...")
    
    groups = {}
    for task in tasks:
        title = task.get("title", "").strip()
        if title not in groups:
            groups[title] = []
        groups[title].append(task)
    
    # Filter to only groups with duplicates
    duplicates = {title: task_list for title, task_list in groups.items() if len(task_list) > 1}
    
    print(f"📋 Found {len(duplicates)} distinct titles with duplicates:")
    for title, task_list in duplicates.items():
        print(f"   • '{title[:60]}...' - {len(task_list)} copies")
    
    return duplicates


def delete_task(task_id: str, dry_run: bool = False) -> bool:
    """Delete a task using the new delete functionality."""
    if dry_run:
        print(f"   🧪 [DRY RUN] Would delete task: {task_id}")
        return True
    
    print(f"   🗑️  Deleting task: {task_id}")
    
    # Use the MCP server delete functionality
    try:
        import sys
        sys.path.insert(0, '/home/mike/development/task-management')
        from notion_mcp_server import delete_task as mcp_delete_task
        import asyncio
        
        result = asyncio.run(mcp_delete_task(task_id=task_id, confirm=True))
        
        if result.get("success", False):
            print(f"   ✅ Successfully deleted task: {task_id}")
            return True
        else:
            print(f"   ❌ Failed to delete task {task_id}: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception deleting task {task_id}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Delete duplicate voice note tasks")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    parser.add_argument("--limit", type=int, help="Limit number of deletions for safety")
    args = parser.parse_args()
    
    print("🧹 Duplicate Voice Task Cleanup Tool")
    print("=" * 50)
    
    if args.dry_run:
        print("🧪 DRY RUN MODE - No actual deletions will be performed")
        print()
    
    # Get all voice tasks
    tasks = get_voice_tasks()
    if not tasks:
        print("❌ No tasks found or error fetching tasks")
        return 1
    
    # Identify duplicates
    duplicates = identify_duplicates(tasks)
    if not duplicates:
        print("✅ No duplicate tasks found!")
        return 0
    
    # Process each duplicate group
    total_to_delete = 0
    total_deleted = 0
    
    for title, task_list in duplicates.items():
        print(f"\n📋 Processing duplicates for: '{title[:60]}...'")
        print(f"   Found {len(task_list)} copies")
        
        # Sort by creation date to keep the oldest
        task_list.sort(key=lambda t: t.get("created_at", ""))
        oldest_task = task_list[0]
        to_delete = task_list[1:]  # All except the oldest
        
        print(f"   ✅ Keeping oldest: {oldest_task['task_id']} (created: {oldest_task.get('created_at', 'Unknown')})")
        print(f"   🗑️  Will delete {len(to_delete)} duplicates:")
        
        for i, task in enumerate(to_delete):
            if args.limit and total_to_delete >= args.limit:
                print(f"   ⚠️  Reached deletion limit of {args.limit}, stopping")
                break
                
            print(f"      {i+1}. {task['task_id']} (created: {task.get('created_at', 'Unknown')})")
            
            if delete_task(task['task_id'], dry_run=args.dry_run):
                total_deleted += 1
            
            total_to_delete += 1
            
            if args.limit and total_to_delete >= args.limit:
                break
    
    print(f"\n📊 Summary:")
    print(f"   • Total duplicate groups: {len(duplicates)}")
    print(f"   • Total tasks to delete: {total_to_delete}")
    if not args.dry_run:
        print(f"   • Successfully deleted: {total_deleted}")
        print(f"   • Failed deletions: {total_to_delete - total_deleted}")
    else:
        print(f"   • Would delete: {total_to_delete} tasks")
    
    if not args.dry_run and total_deleted > 0:
        print(f"\n✅ Cleanup complete! Deleted {total_deleted} duplicate voice note tasks.")
    elif args.dry_run:
        print(f"\n🧪 Dry run complete. Run without --dry-run to actually delete the duplicates.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())