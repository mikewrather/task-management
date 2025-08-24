"""
Task entity manager for GraphRAG adapter.
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base_manager import BaseEntityManager
from ..adapters.base import TaskData


class TaskManager(BaseEntityManager):
    """Manager for TASK entities with validation and relationship handling."""
    
    ENTITY_TYPE = "TASK_MANAGEMENT:TASK" 
    REQUIRED_FIELDS = ["id", "description"]
    OPTIONAL_FIELDS = ["name", "status", "priority", "contexts", "created", "source", 
                      "project_name", "area_name", "goal_name"]
    
    def create(self, task_data: TaskData, project_id: Optional[str] = None, 
               area_id: Optional[str] = None) -> Optional[str]:
        """
        Create task with validation and relationship management.
        
        Args:
            task_data: TaskData object with task information
            project_id: Optional project ID for relationship
            area_id: Optional area ID for relationship
            
        Returns:
            Task ID if successful, None if failed
        """
        # Generate unique task ID
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        # Build entity data with REQUIRED fields first
        entity_data = {
            "id": task_id,  # Required
            "description": task_data.description or task_data.name  # Required
        }
        
        # Add optional fields if present
        if task_data.name:
            entity_data["name"] = task_data.name
        if task_data.status:
            entity_data["status"] = task_data.status
        if task_data.priority:
            entity_data["priority"] = task_data.priority
        if task_data.contexts:
            entity_data["contexts"] = task_data.contexts
        if task_data.created_at:
            entity_data["created"] = task_data.created_at.isoformat()
        if task_data.source:
            entity_data["source"] = task_data.source
        if task_data.project_name:
            entity_data["project_name"] = task_data.project_name
        if task_data.area_name:
            entity_data["area_name"] = task_data.area_name
        if task_data.goal_name:
            entity_data["goal_name"] = task_data.goal_name
        
        # Add Notion ID if migrating
        if task_data.metadata.get("notion_id"):
            entity_data["notion_id"] = task_data.metadata["notion_id"]
        
        # Create the entity
        created_task_id = self.create_entity(entity_data)
        
        if not created_task_id:
            return None
        
        # Create relationships if we have related entity IDs
        self._create_relationships(created_task_id, project_id, area_id, task_data)
        
        return created_task_id
    
    def _create_relationships(self, task_id: str, project_id: Optional[str], 
                            area_id: Optional[str], task_data: TaskData):
        """Create relationships between task and related entities."""
        
        # Create project relationship if available
        if project_id:
            success = self.adapter._create_relationship(
                task_id, project_id, "BELONGS_TO", "PROJECT"
            )
            if success:
                self.logger.info(f"Created PROJECT relationship: Task {task_id} -> {task_data.project_name}")
            else:
                self.logger.error(f"Failed to create PROJECT relationship for task {task_id}")
        
        # Create area relationship if available (even without project)
        if area_id:
            success = self.adapter._create_relationship(
                task_id, area_id, "RELATES_TO", "AREA"
            )
            if success:
                self.logger.info(f"Created AREA relationship: Task {task_id} -> {task_data.area_name}")
            else:
                self.logger.error(f"Failed to create AREA relationship for task {task_id}")
        
        # Create goal relationship if available
        if task_data.goal_node_id:
            success = self.adapter._create_relationship(
                task_id, task_data.goal_node_id, "CONTRIBUTES_TO", "GOAL"
            )
            if success:
                self.logger.info(f"Created GOAL relationship: Task {task_id} -> {task_data.goal_name}")
            else:
                self.logger.error(f"Failed to create GOAL relationship for task {task_id}")
    
    def find_by_description(self, description: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find tasks with similar descriptions using semantic search."""
        
        query_params = {
            "query": f"Find tasks with description similar to: {description}",
            "max_results": limit
        }
        
        response = self.adapter._execute_mcp_command("query_natural_language", query_params)
        
        if response.get("success") and response.get("results"):
            return response["results"]
        
        return []
    
    def update(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update task properties."""
        
        # Validate update fields
        invalid_fields = set(updates.keys()) - set(self.REQUIRED_FIELDS + self.OPTIONAL_FIELDS)
        if invalid_fields:
            self.logger.error(f"Invalid update fields for {self.ENTITY_TYPE}: {invalid_fields}")
            return False
        
        # Build Cypher update query
        set_clauses = []
        for key, value in updates.items():
            if isinstance(value, str):
                escaped_value = value.replace("'", "\\'")
                set_clauses.append(f"t.{key} = '{escaped_value}'")
            elif isinstance(value, (int, float, bool)):
                set_clauses.append(f"t.{key} = {value}")
            elif value is None:
                set_clauses.append(f"t.{key} = null")
        
        if not set_clauses:
            self.logger.warning("No valid update clauses generated")
            return False
        
        update_query = f"""
        MATCH (t:TASK_MANAGEMENT:TASK {{id: '{task_id}'}})
        SET {', '.join(set_clauses)}
        RETURN t.id as updated_id
        """
        
        response = self.adapter._execute_mcp_command("execute_cypher", {
            "query": update_query.strip()
        })
        
        if response.get("success") and response.get("results"):
            self.logger.success(f"✅ Updated task: {task_id}")
            return True
        else:
            self.logger.error(f"Failed to update task {task_id}: {response.get('error')}")
            return False