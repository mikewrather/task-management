#!/usr/bin/env python3
"""
Update edges (relationships) for existing TASK_MANAGEMENT:* nodes

This script provides functionality to:
1. Add missing relationships between tasks, projects, and areas
2. Update existing relationships
3. Fix orphaned nodes by establishing proper connections
4. Detect and create semantic relationships based on embeddings

Usage:
    python scripts/maintenance/update_task_edges.py --add-missing
    python scripts/maintenance/update_task_edges.py --fix-orphans
    python scripts/maintenance/update_task_edges.py --semantic-link
    python scripts/maintenance/update_task_edges.py --dry-run
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter
from src.voice_task_manager.utils.logging import VoiceLogger


class TaskEdgeUpdater:
    """Update relationships for TASK_MANAGEMENT nodes"""
    
    def __init__(self, dry_run: bool = False):
        """Initialize the edge updater"""
        self.dry_run = dry_run
        self.logger = VoiceLogger()
        self.adapter = GraphRAGTaskAdapter()
        self.stats = {
            "relationships_added": 0,
            "orphans_fixed": 0,
            "semantic_links": 0,
            "errors": 0
        }
    
    def find_orphaned_tasks(self) -> List[Dict[str, Any]]:
        """Find tasks without project or area relationships"""
        query = """
        MATCH (t:`TASK_MANAGEMENT:TASK`)
        WHERE NOT (t)-[:BELONGS_TO]->()
        AND NOT (t)-[:RELATES_TO]->()
        RETURN t.id as task_id, t.name as name, t.description as description
        LIMIT 100
        """
        
        response = self.adapter._execute_mcp_command("execute_cypher", {
            "query": query,
            "parameters": {}
        })
        
        if isinstance(response, list):
            return response
        return response.get("results", []) if response else []
    
    def find_orphaned_projects(self) -> List[Dict[str, Any]]:
        """Find projects without area relationships"""
        query = """
        MATCH (p:`TASK_MANAGEMENT:PROJECT`)
        WHERE NOT (p)-[:BELONGS_TO]->()
        RETURN p.name as project_name, id(p) as project_id
        LIMIT 100
        """
        
        response = self.adapter._execute_mcp_command("execute_cypher", {
            "query": query,
            "parameters": {}
        })
        
        if isinstance(response, list):
            return response
        return response.get("results", []) if response else []
    
    def find_potential_relationships(self, task: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Find potential projects and areas for a task based on semantic similarity"""
        
        # Search for similar projects
        project_query = """
        MATCH (t:`TASK_MANAGEMENT:TASK` {id: $task_id})
        MATCH (p:`TASK_MANAGEMENT:PROJECT`)
        WHERE p.entity_embedding IS NOT NULL
        AND t.entity_embedding IS NOT NULL
        WITH t, p,
             gds.similarity.cosine(t.entity_embedding, p.entity_embedding) AS similarity
        WHERE similarity > 0.7
        RETURN p.name as project_name, id(p) as project_id, similarity
        ORDER BY similarity DESC
        LIMIT 3
        """
        
        project_response = self.adapter._execute_mcp_command("execute_cypher", {
            "query": project_query,
            "parameters": {"task_id": task['task_id']}
        })
        
        # Search for areas based on project names or task description
        area_query = """
        MATCH (a:AREA)
        RETURN a.name as area_name, id(a) as area_id
        """
        
        area_response = self.adapter._execute_mcp_command("execute_cypher", {
            "query": area_query,
            "parameters": {}
        })
        
        projects = project_response if isinstance(project_response, list) else []
        areas = area_response if isinstance(area_response, list) else []
        
        return {
            "projects": projects,
            "areas": areas
        }
    
    def create_relationship(self, from_id: str, to_id: str, 
                          relationship_type: str, from_label: str, to_label: str) -> bool:
        """Create or update a relationship between two nodes"""
        
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would create: ({from_label}:{from_id})-[:{relationship_type}]->({to_label}:{to_id})")
            return True
        
        # Use MERGE to create relationship if it doesn't exist
        query = f"""
        MATCH (from:`{from_label}` {{id: $from_id}})
        MATCH (to:`{to_label}`)
        WHERE id(to) = $to_id
        MERGE (from)-[r:{relationship_type}]->(to)
        SET r.created_at = coalesce(r.created_at, datetime()),
            r.updated_at = datetime()
        RETURN r
        """
        
        response = self.adapter._execute_mcp_command("execute_cypher", {
            "query": query,
            "parameters": {
                "from_id": from_id,
                "to_id": int(to_id) if to_id.isdigit() else to_id
            }
        })
        
        success = bool(response) if isinstance(response, list) else response.get("success", False)
        
        if success:
            self.logger.success(f"✅ Created: ({from_label}:{from_id})-[:{relationship_type}]->({to_label}:{to_id})")
            self.stats["relationships_added"] += 1
        else:
            self.logger.error(f"❌ Failed to create relationship")
            self.stats["errors"] += 1
        
        return success
    
    def fix_orphaned_tasks(self, auto_link: bool = False):
        """Fix orphaned tasks by establishing relationships"""
        
        self.logger.info("🔍 Finding orphaned tasks...")
        orphans = self.find_orphaned_tasks()
        
        if not orphans:
            self.logger.success("✅ No orphaned tasks found!")
            return
        
        self.logger.info(f"Found {len(orphans)} orphaned tasks")
        
        for task in orphans:
            self.logger.info(f"\n📝 Task: {task['name']}")
            
            # Find potential relationships
            suggestions = self.find_potential_relationships(task)
            
            if suggestions['projects']:
                self.logger.info("  Suggested projects:")
                for proj in suggestions['projects']:
                    self.logger.info(f"    - {proj['project_name']} (similarity: {proj.get('similarity', 0):.2f})")
                
                if auto_link and suggestions['projects']:
                    # Link to the most similar project
                    best_project = suggestions['projects'][0]
                    self.create_relationship(
                        task['task_id'],
                        str(best_project['project_id']),
                        "BELONGS_TO",
                        "TASK_MANAGEMENT:TASK",
                        "TASK_MANAGEMENT:PROJECT"
                    )
                    self.stats["orphans_fixed"] += 1
    
    def add_missing_relationships(self):
        """Add missing relationships based on naming patterns"""
        
        self.logger.info("🔗 Adding missing relationships based on patterns...")
        
        # Find tasks with project_name but no BELONGS_TO relationship
        query = """
        MATCH (t:`TASK_MANAGEMENT:TASK`)
        WHERE t.project_name IS NOT NULL 
        AND t.project_name <> ''
        AND NOT (t)-[:BELONGS_TO]->()
        WITH t
        MATCH (p:`TASK_MANAGEMENT:PROJECT`)
        WHERE toLower(p.name) = toLower(t.project_name)
        RETURN t.id as task_id, t.name as task_name, 
               p.name as project_name, id(p) as project_id
        LIMIT 50
        """
        
        response = self.adapter._execute_mcp_command("execute_cypher", {
            "query": query,
            "parameters": {}
        })
        
        matches = response if isinstance(response, list) else []
        
        for match in matches:
            self.logger.info(f"Linking task '{match['task_name']}' to project '{match['project_name']}'")
            self.create_relationship(
                match['task_id'],
                str(match['project_id']),
                "BELONGS_TO",
                "TASK_MANAGEMENT:TASK",
                "TASK_MANAGEMENT:PROJECT"
            )
    
    def create_semantic_relationships(self, min_similarity: float = 0.8):
        """Create relationships based on semantic similarity of embeddings"""
        
        self.logger.info(f"🧠 Creating semantic relationships (min similarity: {min_similarity})...")
        
        # Find highly similar tasks that aren't linked
        query = """
        MATCH (t1:`TASK_MANAGEMENT:TASK`), (t2:`TASK_MANAGEMENT:TASK`)
        WHERE t1.entity_embedding IS NOT NULL
        AND t2.entity_embedding IS NOT NULL
        AND id(t1) < id(t2)
        AND NOT (t1)-[:RELATED_TO]-(t2)
        WITH t1, t2,
             gds.similarity.cosine(t1.entity_embedding, t2.entity_embedding) AS similarity
        WHERE similarity > $min_similarity
        RETURN t1.id as task1_id, t1.name as task1_name,
               t2.id as task2_id, t2.name as task2_name,
               similarity
        ORDER BY similarity DESC
        LIMIT 20
        """
        
        response = self.adapter._execute_mcp_command("execute_cypher", {
            "query": query,
            "parameters": {"min_similarity": min_similarity}
        })
        
        similar_pairs = response if isinstance(response, list) else []
        
        for pair in similar_pairs:
            self.logger.info(f"Linking similar tasks (similarity: {pair['similarity']:.2f}):")
            self.logger.info(f"  - {pair['task1_name']}")
            self.logger.info(f"  - {pair['task2_name']}")
            
            if not self.dry_run:
                # Create bidirectional RELATED_TO relationship
                query = """
                MATCH (t1:`TASK_MANAGEMENT:TASK` {id: $task1_id})
                MATCH (t2:`TASK_MANAGEMENT:TASK` {id: $task2_id})
                MERGE (t1)-[r:RELATED_TO]-(t2)
                SET r.similarity = $similarity,
                    r.created_at = datetime()
                RETURN r
                """
                
                self.adapter._execute_mcp_command("execute_cypher", {
                    "query": query,
                    "parameters": {
                        "task1_id": pair['task1_id'],
                        "task2_id": pair['task2_id'],
                        "similarity": pair['similarity']
                    }
                })
                self.stats["semantic_links"] += 1
    
    def print_summary(self):
        """Print summary of operations"""
        
        print("\n" + "=" * 60)
        print("📊 Summary of Operations")
        print("=" * 60)
        
        if self.dry_run:
            print("🔸 DRY RUN MODE - No changes were made")
        
        print(f"✅ Relationships added: {self.stats['relationships_added']}")
        print(f"🔧 Orphans fixed: {self.stats['orphans_fixed']}")
        print(f"🧠 Semantic links created: {self.stats['semantic_links']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print("=" * 60)


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description="Update edges for TASK_MANAGEMENT nodes"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    
    parser.add_argument(
        "--add-missing",
        action="store_true",
        help="Add missing relationships based on patterns"
    )
    
    parser.add_argument(
        "--fix-orphans",
        action="store_true",
        help="Fix orphaned tasks by establishing relationships"
    )
    
    parser.add_argument(
        "--auto-link",
        action="store_true",
        help="Automatically link orphans to best matches"
    )
    
    parser.add_argument(
        "--semantic-link",
        action="store_true",
        help="Create relationships based on semantic similarity"
    )
    
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.8,
        help="Minimum similarity for semantic linking (default: 0.8)"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all update operations"
    )
    
    args = parser.parse_args()
    
    # Initialize updater
    updater = TaskEdgeUpdater(dry_run=args.dry_run)
    
    # Run requested operations
    if args.all or args.add_missing:
        updater.add_missing_relationships()
    
    if args.all or args.fix_orphans:
        updater.fix_orphaned_tasks(auto_link=args.auto_link)
    
    if args.all or args.semantic_link:
        updater.create_semantic_relationships(min_similarity=args.min_similarity)
    
    # Print summary
    updater.print_summary()


if __name__ == "__main__":
    main()