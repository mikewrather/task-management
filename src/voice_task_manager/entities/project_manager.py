"""
Project entity manager for GraphRAG adapter.
"""

import uuid
from typing import Optional, List, Dict, Any

from .base_manager import BaseEntityManager


class ProjectManager(BaseEntityManager):
    """Manager for PROJECT entities with validation and relationship handling."""
    
    ENTITY_TYPE = "TASK_MANAGEMENT:PROJECT"
    REQUIRED_FIELDS = ["name"]
    OPTIONAL_FIELDS = ["description", "status", "priority"]
    
    def create(self, name: str, description: str = "", area_id: Optional[str] = None) -> Optional[str]:
        """
        Create project with area relationship.
        
        Args:
            name: Project name (required)
            description: Project description (optional)
            area_id: Optional area ID for relationship
            
        Returns:
            Project ID if successful, None if failed
        """
        # Build entity data
        entity_data = {
            "name": name,  # Required
        }
        
        # Add optional fields
        if description:
            entity_data["description"] = description
        
        # Set default status
        entity_data["status"] = "active"
        
        # Create the entity
        project_id = self.create_entity(entity_data)
        
        if not project_id:
            return None
        
        # Create area relationship if provided
        if area_id:
            success = self.adapter._create_relationship(
                project_id, area_id, "BELONGS_TO", "AREA"
            )
            if success:
                self.logger.info(f"Created AREA relationship: Project {name} -> Area {area_id}")
            else:
                self.logger.error(f"Failed to create AREA relationship for project {name}")
        
        return project_id
    
    def find_or_create(self, name: str, area_name: str = None) -> Optional[str]:
        """
        Find existing project by name or create new one.
        
        Args:
            name: Project name to find or create
            area_name: Optional area name for context
            
        Returns:
            Project ID if found/created, None if failed
        """
        # First try to find existing project
        existing_projects = self.find_by_name(name)
        
        if existing_projects:
            project_id = existing_projects[0].get("p", {}).get("id") or existing_projects[0].get("id")
            if project_id:
                self.logger.info(f"Found existing project: {name} ({project_id})")
                return project_id
        
        # Create new project if not found
        self.logger.info(f"Creating new project: {name}")
        
        # Get area ID if area_name provided
        area_id = None
        if area_name:
            area_id = self.adapter.area_manager.find_or_create(area_name)
        
        return self.create(name, f"Project for {area_name or 'general'} tasks", area_id)
    
    def find_by_name(self, name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find projects by name using semantic search."""
        
        query_params = {
            "query": f"Find projects named: {name}",
            "max_results": limit
        }
        
        response = self.adapter._execute_mcp_command("query_natural_language", query_params)
        
        if response.get("success") and response.get("results"):
            return response["results"]
        
        return []
    
    def get_project_tasks(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all tasks belonging to this project using natural language query."""
        
        response = self.adapter._execute_mcp_command("query_natural_language", {
            "query": f"Find all tasks that belong to project with ID {project_id}, ordered by most recent",
            "max_results": 50
        })
        
        # Handle both dict and list response formats
        if isinstance(response, dict):
            if not response.get("success"):
                return []
            results = response.get("results", [])
        elif isinstance(response, list):
            results = response
        else:
            return []
        
        # Filter for TASK entities and format response
        tasks = []
        for result in results:
            if result.get("labels") and "TASK" in result["labels"]:
                tasks.append({
                    "task_id": result.get("id"),
                    "task_name": result.get("name"),
                    "task_description": result.get("description"),
                    "task_status": result.get("status")
                })
        
        return tasks