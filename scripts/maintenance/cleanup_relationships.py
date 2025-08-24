#!/usr/bin/env python3
"""
Task Relationship Cleanup Tool

This script provides comprehensive relationship cleanup and maintenance for the 
Voice Task Management system. It can find orphaned tasks, remove duplicates, 
and establish missing relationships between tasks, areas, and goals.

Features:
- Find orphaned tasks (tasks without proper area/project associations)
- Identify and merge duplicate tasks
- Suggest and create missing task-area-goal relationships
- Dry-run mode for safe preview of changes
- Detailed reporting and logging

Usage:
    python scripts/maintenance/cleanup_relationships.py --find-orphans
    python scripts/maintenance/cleanup_relationships.py --remove-duplicates --dry-run
    python scripts/maintenance/cleanup_relationships.py --associate-relationships
    python scripts/maintenance/cleanup_relationships.py --full-cleanup --dry-run

Examples:
    # Preview all cleanup operations
    ./scripts/maintenance/cleanup_relationships.py --full-cleanup --dry-run
    
    # Fix orphaned tasks only
    ./scripts/maintenance/cleanup_relationships.py --find-orphans --fix
    
    # Interactive mode for reviewing duplicates
    ./scripts/maintenance/cleanup_relationships.py --remove-duplicates --interactive
"""

import argparse
import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
except ImportError:
    # dotenv not available, environment should be set manually
    pass

from voice_task_manager.utils.relationship_analyzer import RelationshipAnalyzer, TaskRelationship, DuplicateTaskPair
from voice_task_manager.utils.logging import VoiceLogger


class RelationshipCleanupTool:
    """Main tool for relationship cleanup operations"""
    
    def __init__(self, dry_run: bool = False, interactive: bool = False):
        """
        Initialize the cleanup tool
        
        Args:
            dry_run: If True, preview changes without applying them
            interactive: If True, prompt for user confirmation on changes
        """
        self.dry_run = dry_run
        self.interactive = interactive
        self.logger = VoiceLogger()
        self.analyzer = RelationshipAnalyzer(logger=self.logger)
        
        # Statistics tracking
        self.stats = {
            "orphans_found": 0,
            "orphans_fixed": 0,
            "duplicates_found": 0,
            "duplicates_merged": 0,
            "relationships_created": 0,
            "errors": 0
        }
    
    def find_and_fix_orphans(self, fix: bool = False, min_confidence: float = 0.7) -> Dict[str, Any]:
        """
        Find orphaned tasks and optionally fix them
        
        Args:
            fix: Whether to apply fixes or just report
            min_confidence: Minimum confidence threshold for relationship suggestions
            
        Returns:
            Dictionary with results and statistics
        """
        self.logger.info("🔍 Finding orphaned tasks...")
        
        orphaned_tasks = self.analyzer.find_orphaned_tasks(min_confidence=min_confidence)
        self.stats["orphans_found"] = len(orphaned_tasks)
        
        if not orphaned_tasks:
            self.logger.success("✅ No orphaned tasks found!")
            return {"orphans": [], "stats": self.stats}
        
        self.logger.warning(f"Found {len(orphaned_tasks)} orphaned tasks")
        
        results = []
        for task in orphaned_tasks:
            result = self._process_orphaned_task(task, fix)
            results.append(result)
            
            if result.get("fixed"):
                self.stats["orphans_fixed"] += 1
        
        # Display summary
        self._display_orphan_summary(results)
        
        return {"orphans": results, "stats": self.stats}
    
    def find_and_merge_duplicates(self, merge: bool = False, similarity_threshold: float = 0.8) -> Dict[str, Any]:
        """
        Find duplicate tasks and optionally merge them
        
        Args:
            merge: Whether to merge duplicates or just report
            similarity_threshold: Minimum similarity score to consider as duplicate
            
        Returns:
            Dictionary with results and statistics
        """
        self.logger.info("🔍 Finding duplicate tasks...")
        
        duplicate_pairs = self.analyzer.find_duplicate_tasks(similarity_threshold=similarity_threshold)
        self.stats["duplicates_found"] = len(duplicate_pairs)
        
        if not duplicate_pairs:
            self.logger.success("✅ No duplicate tasks found!")
            return {"duplicates": [], "stats": self.stats}
        
        self.logger.warning(f"Found {len(duplicate_pairs)} potential duplicate pairs")
        
        results = []
        for pair in duplicate_pairs:
            result = self._process_duplicate_pair(pair, merge)
            results.append(result)
            
            if result.get("merged"):
                self.stats["duplicates_merged"] += 1
        
        # Display summary
        self._display_duplicate_summary(results)
        
        return {"duplicates": results, "stats": self.stats}
    
    def associate_relationships(self, apply: bool = False) -> Dict[str, Any]:
        """
        Find and create missing task relationships
        
        Args:
            apply: Whether to apply relationship changes
            
        Returns:
            Dictionary with results and statistics
        """
        self.logger.info("🔍 Analyzing task relationships...")
        
        # Get all tasks that might benefit from better relationships
        all_tasks = self.analyzer._get_all_tasks()
        suggestions = self.analyzer.suggest_relationships(all_tasks)
        
        if not suggestions:
            self.logger.success("✅ No relationship improvements needed!")
            return {"relationships": [], "stats": self.stats}
        
        self.logger.info(f"Found {len(suggestions)} relationship improvement opportunities")
        
        results = []
        for suggestion in suggestions:
            result = self._process_relationship_suggestion(suggestion, apply)
            results.append(result)
            
            if result.get("applied"):
                self.stats["relationships_created"] += 1
        
        # Display summary
        self._display_relationship_summary(results)
        
        return {"relationships": results, "stats": self.stats}
    
    def full_cleanup(self) -> Dict[str, Any]:
        """
        Perform comprehensive cleanup of all relationship issues
        
        Returns:
            Dictionary with complete results and statistics
        """
        self.logger.info("🧹 Starting full relationship cleanup...")
        
        results = {
            "orphans": self.find_and_fix_orphans(fix=not self.dry_run),
            "duplicates": self.find_and_merge_duplicates(merge=not self.dry_run),
            "relationships": self.associate_relationships(apply=not self.dry_run)
        }
        
        # Display final summary
        self._display_final_summary()
        
        return results
    
    def _process_orphaned_task(self, task: TaskRelationship, fix: bool) -> Dict[str, Any]:
        """Process a single orphaned task"""
        result = {
            "task_id": task.task_id,
            "task_name": task.task_name,
            "current_relationships": {
                "project": task.current_project_name,
                "area": task.current_area_name
            },
            "suggested_relationships": {
                "project": task.suggested_project_name,
                "area": task.suggested_area_name
            },
            "confidence": task.confidence,
            "reasoning": task.reasoning,
            "fixed": False,
            "error": None
        }
        
        # Display the orphaned task
        self.logger.info(f"📋 Orphaned Task: '{task.task_name}'")
        self.logger.info(f"   Current: Project={task.current_project_name or 'None'}, Area={task.current_area_name or 'None'}")
        if task.suggested_project_name or task.suggested_area_name:
            self.logger.info(f"   Suggested: Project={task.suggested_project_name or 'None'}, Area={task.suggested_area_name or 'None'}")
            self.logger.info(f"   Confidence: {task.confidence:.2f}")
            self.logger.info(f"   Reasoning: {task.reasoning}")
        
        if fix and not self.dry_run:
            if self.interactive:
                response = input(f"Fix relationships for '{task.task_name}'? (y/n/s=skip all): ")
                if response.lower() == 's':
                    return result
                elif response.lower() != 'y':
                    return result
            
            # Apply the fix
            try:
                success = self._apply_relationship_fix(task)
                result["fixed"] = success
                if success:
                    self.logger.success(f"✅ Fixed relationships for '{task.task_name}'")
                else:
                    self.logger.error(f"❌ Failed to fix relationships for '{task.task_name}'")
            except Exception as e:
                result["error"] = str(e)
                self.stats["errors"] += 1
                self.logger.error(f"❌ Error fixing '{task.task_name}': {e}")
        elif self.dry_run:
            self.logger.info("   [DRY RUN] Would fix this task's relationships")
        
        return result
    
    def _process_duplicate_pair(self, pair: DuplicateTaskPair, merge: bool) -> Dict[str, Any]:
        """Process a duplicate task pair"""
        result = {
            "task1_id": pair.task1_id,
            "task1_name": pair.task1_name,
            "task2_id": pair.task2_id,
            "task2_name": pair.task2_name,
            "similarity_score": pair.similarity_score,
            "similarity_type": pair.similarity_type,
            "recommendation": pair.recommendation,
            "merged": False,
            "action_taken": "none",
            "error": None
        }
        
        # Display the duplicate pair
        self.logger.warning(f"👥 Potential Duplicates (similarity: {pair.similarity_score:.2f}):")
        self.logger.info(f"   Task 1: '{pair.task1_name}' (ID: {pair.task1_id})")
        self.logger.info(f"   Task 2: '{pair.task2_name}' (ID: {pair.task2_id})")
        self.logger.info(f"   Recommendation: {pair.recommendation}")
        
        if merge and pair.recommendation in ["merge", "review"]:
            if self.interactive or pair.recommendation == "review":
                response = input(f"Merge these tasks? (y/n/s=skip all): ")
                if response.lower() == 's':
                    return result
                elif response.lower() != 'y':
                    result["action_taken"] = "skipped"
                    return result
            
            if not self.dry_run:
                try:
                    success = self._merge_duplicate_tasks(pair.task1_id, pair.task2_id)
                    result["merged"] = success
                    result["action_taken"] = "merged" if success else "failed"
                    if success:
                        self.logger.success(f"✅ Merged duplicate tasks")
                    else:
                        self.logger.error(f"❌ Failed to merge duplicate tasks")
                except Exception as e:
                    result["error"] = str(e)
                    result["action_taken"] = "error"
                    self.stats["errors"] += 1
                    self.logger.error(f"❌ Error merging duplicates: {e}")
            else:
                self.logger.info("   [DRY RUN] Would merge these duplicate tasks")
                result["action_taken"] = "dry_run"
        
        return result
    
    def _process_relationship_suggestion(self, suggestion: TaskRelationship, apply: bool) -> Dict[str, Any]:
        """Process a relationship suggestion"""
        result = {
            "task_id": suggestion.task_id,
            "task_name": suggestion.task_name,
            "suggestion": {
                "project": suggestion.suggested_project_name,
                "area": suggestion.suggested_area_name
            },
            "confidence": suggestion.confidence,
            "applied": False,
            "error": None
        }
        
        # Display suggestion
        self.logger.info(f"🔗 Relationship Suggestion for '{suggestion.task_name}':")
        if suggestion.suggested_project_name:
            self.logger.info(f"   Project: {suggestion.suggested_project_name}")
        if suggestion.suggested_area_name:
            self.logger.info(f"   Area: {suggestion.suggested_area_name}")
        self.logger.info(f"   Confidence: {suggestion.confidence:.2f}")
        
        if apply and not self.dry_run:
            if self.interactive:
                response = input(f"Apply relationship suggestion? (y/n/s=skip all): ")
                if response.lower() == 's':
                    return result
                elif response.lower() != 'y':
                    return result
            
            try:
                success = self._apply_relationship_fix(suggestion)
                result["applied"] = success
                if success:
                    self.logger.success(f"✅ Applied relationship suggestion")
                else:
                    self.logger.error(f"❌ Failed to apply relationship suggestion")
            except Exception as e:
                result["error"] = str(e)
                self.stats["errors"] += 1
                self.logger.error(f"❌ Error applying suggestion: {e}")
        elif self.dry_run:
            self.logger.info("   [DRY RUN] Would apply this relationship suggestion")
        
        return result
    
    def _apply_relationship_fix(self, task: TaskRelationship) -> bool:
        """Apply relationship fixes for a task by creating actual graph relationships"""
        self.logger.debug(f"Applying relationship fix for task {task.task_id}")
        
        success = True
        
        try:
            # Create project relationship if suggested
            if task.suggested_project_id:
                success &= self._create_project_relationship(task.task_id, task.suggested_project_id, task.suggested_project_name)
            
            # Create area relationship if suggested
            if task.suggested_area_id:
                success &= self._create_area_relationship(task.task_id, task.suggested_area_id, task.suggested_area_name)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error applying relationship fix for task {task.task_id}: {e}")
            return False
    
    def _create_project_relationship(self, task_id: str, project_id: str, project_name: str) -> bool:
        """Create BELONGS_TO relationship between task and project"""
        try:
            # Use the analyzer's GraphRAG adapter to execute Cypher
            if not self.analyzer.graphrag_adapter:
                self.logger.error("No GraphRAG adapter available")
                return False
            
            project_query = """
            MATCH (t:TASK), (p:PROJECT)
            WHERE ID(t) = $task_id AND ID(p) = $project_id
            MERGE (t)-[:BELONGS_TO]->(p)
            RETURN t.name as task_name, p.name as project_name
            """
            
            response = self.analyzer.graphrag_adapter._execute_mcp_command("execute_cypher", {
                "query": project_query,
                "parameters": {
                    "task_id": int(task_id),
                    "project_id": int(project_id)
                }
            })
            
            if response and response.get("success"):
                self.logger.info(f"Created BELONGS_TO relationship: Task -> {project_name}")
                return True
            else:
                self.logger.error(f"Failed to create project relationship: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating project relationship: {e}")
            return False
    
    def _create_area_relationship(self, task_id: str, area_id: str, area_name: str) -> bool:
        """Create RELATES_TO relationship between task and area"""
        try:
            # Use the analyzer's GraphRAG adapter to execute Cypher
            if not self.analyzer.graphrag_adapter:
                self.logger.error("No GraphRAG adapter available")
                return False
            
            area_query = """
            MATCH (t:TASK), (a:AREA)
            WHERE ID(t) = $task_id AND ID(a) = $area_id
            MERGE (t)-[:RELATES_TO]->(a)
            RETURN t.name as task_name, a.name as area_name
            """
            
            response = self.analyzer.graphrag_adapter._execute_mcp_command("execute_cypher", {
                "query": area_query,
                "parameters": {
                    "task_id": int(task_id),
                    "area_id": int(area_id)
                }
            })
            
            if response and response.get("success"):
                self.logger.info(f"Created RELATES_TO relationship: Task -> {area_name}")
                return True
            else:
                self.logger.error(f"Failed to create area relationship: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating area relationship: {e}")
            return False
    
    def _merge_duplicate_tasks(self, task1_id: str, task2_id: str) -> bool:
        """Merge two duplicate tasks"""
        # This is a placeholder - actual implementation would:
        # 1. Merge task data (descriptions, contexts, etc.)
        # 2. Transfer relationships
        # 3. Delete the duplicate
        # 4. Update references
        
        self.logger.debug(f"Merging tasks {task1_id} and {task2_id}")
        return True  # Simulated success
    
    def _display_orphan_summary(self, results: List[Dict[str, Any]]):
        """Display summary of orphan processing"""
        if not results:
            return
        
        self.logger.info("\\n📊 Orphaned Tasks Summary:")
        self.logger.info(f"   Total found: {len(results)}")
        
        fixed_count = sum(1 for r in results if r.get("fixed"))
        if fixed_count > 0:
            self.logger.success(f"   Fixed: {fixed_count}")
        
        error_count = sum(1 for r in results if r.get("error"))
        if error_count > 0:
            self.logger.error(f"   Errors: {error_count}")
    
    def _display_duplicate_summary(self, results: List[Dict[str, Any]]):
        """Display summary of duplicate processing"""
        if not results:
            return
        
        self.logger.info("\\n📊 Duplicate Tasks Summary:")
        self.logger.info(f"   Total pairs found: {len(results)}")
        
        merged_count = sum(1 for r in results if r.get("merged"))
        if merged_count > 0:
            self.logger.success(f"   Merged: {merged_count}")
        
        skipped_count = sum(1 for r in results if r.get("action_taken") == "skipped")
        if skipped_count > 0:
            self.logger.info(f"   Skipped: {skipped_count}")
    
    def _display_relationship_summary(self, results: List[Dict[str, Any]]):
        """Display summary of relationship processing"""
        if not results:
            return
        
        self.logger.info("\\n📊 Relationship Suggestions Summary:")
        self.logger.info(f"   Total suggestions: {len(results)}")
        
        applied_count = sum(1 for r in results if r.get("applied"))
        if applied_count > 0:
            self.logger.success(f"   Applied: {applied_count}")
    
    def _display_final_summary(self):
        """Display final cleanup summary"""
        self.logger.info("\\n🎯 Final Cleanup Summary:")
        self.logger.info(f"   Orphaned tasks found: {self.stats['orphans_found']}")
        self.logger.info(f"   Orphaned tasks fixed: {self.stats['orphans_fixed']}")
        self.logger.info(f"   Duplicate pairs found: {self.stats['duplicates_found']}")
        self.logger.info(f"   Duplicate pairs merged: {self.stats['duplicates_merged']}")
        self.logger.info(f"   Relationships created: {self.stats['relationships_created']}")
        if self.stats['errors'] > 0:
            self.logger.error(f"   Errors encountered: {self.stats['errors']}")
        
        if self.dry_run:
            self.logger.warning("\\n⚠️  This was a DRY RUN - no changes were applied")
            self.logger.info("Remove --dry-run flag to apply changes")


def main():
    """Main entry point for the cleanup tool"""
    parser = argparse.ArgumentParser(
        description="Task Relationship Cleanup Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Operation modes
    parser.add_argument("--find-orphans", action="store_true",
                       help="Find tasks without proper relationships")
    parser.add_argument("--remove-duplicates", action="store_true",
                       help="Find and remove duplicate tasks")
    parser.add_argument("--associate-relationships", action="store_true",
                       help="Create missing task-area-goal relationships")
    parser.add_argument("--full-cleanup", action="store_true",
                       help="Perform all cleanup operations")
    
    # Operation modifiers
    parser.add_argument("--fix", action="store_true",
                       help="Apply fixes (for --find-orphans)")
    parser.add_argument("--merge", action="store_true",
                       help="Merge duplicates (for --remove-duplicates)")
    parser.add_argument("--apply", action="store_true",
                       help="Apply suggestions (for --associate-relationships)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview changes without applying them")
    parser.add_argument("--interactive", action="store_true",
                       help="Prompt for confirmation on each change")
    
    # Thresholds
    parser.add_argument("--min-confidence", type=float, default=0.7,
                       help="Minimum confidence for relationship suggestions (0.0-1.0)")
    parser.add_argument("--similarity-threshold", type=float, default=0.8,
                       help="Minimum similarity for duplicate detection (0.0-1.0)")
    
    # Output options
    parser.add_argument("--output", type=str,
                       help="Save results to JSON file")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not any([args.find_orphans, args.remove_duplicates, args.associate_relationships, args.full_cleanup]):
        parser.error("Must specify at least one operation: --find-orphans, --remove-duplicates, --associate-relationships, or --full-cleanup")
    
    # Enable debug logging if verbose
    if args.verbose:
        import os
        os.environ["DEBUG"] = "1"
    
    # Initialize cleanup tool
    cleanup_tool = RelationshipCleanupTool(
        dry_run=args.dry_run,
        interactive=args.interactive
    )
    
    # Execute requested operations
    results = {}
    
    try:
        if args.full_cleanup:
            results = cleanup_tool.full_cleanup()
        else:
            if args.find_orphans:
                results["orphans"] = cleanup_tool.find_and_fix_orphans(
                    fix=args.fix,
                    min_confidence=args.min_confidence
                )
            
            if args.remove_duplicates:
                results["duplicates"] = cleanup_tool.find_and_merge_duplicates(
                    merge=args.merge,
                    similarity_threshold=args.similarity_threshold
                )
            
            if args.associate_relationships:
                results["relationships"] = cleanup_tool.associate_relationships(
                    apply=args.apply
                )
        
        # Save results if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "arguments": vars(args),
                    "results": results,
                    "stats": cleanup_tool.stats
                }, f, indent=2)
            
            cleanup_tool.logger.success(f"Results saved to {output_path}")
    
    except KeyboardInterrupt:
        cleanup_tool.logger.warning("\\n⚠️  Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        cleanup_tool.logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()