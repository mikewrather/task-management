"""
Goal entity manager for GraphRAG adapter.
"""

from typing import Optional, List, Dict, Any

from .base_manager import BaseEntityManager


class GoalManager(BaseEntityManager):
    """Manager for GOAL entities with validation and relationship handling."""
    
    ENTITY_TYPE = "TASK_MANAGEMENT:GOAL"
    REQUIRED_FIELDS = ["name"]
    OPTIONAL_FIELDS = ["description", "status", "target_date", "area_name"]
    
    def create(self, name: str, description: str = "", area_id: Optional[str] = None, 
              target_date: Optional[str] = None) -> Optional[str]:
        """
        Create goal with area relationship.
        
        Args:
            name: Goal name (required)
            description: Goal description (optional)
            area_id: Optional area ID for relationship
            target_date: Optional target completion date
            
        Returns:
            Goal ID if successful, None if failed
        """
        # Build entity data
        entity_data = {
            "name": name,  # Required
        }
        
        # Add optional fields
        if description:
            entity_data["description"] = description
        if target_date:
            entity_data["target_date"] = target_date
        
        # Set default status
        entity_data["status"] = "active"
        
        # Create the entity
        goal_id = self.create_entity(entity_data)
        
        if not goal_id:
            return None
        
        # Create area relationship if provided
        if area_id:
            success = self.adapter._create_relationship(
                goal_id, area_id, "BELONGS_TO", "AREA"
            )
            if success:
                self.logger.info(f"Created AREA relationship: Goal {name} -> Area {area_id}")
            else:
                self.logger.error(f"Failed to create AREA relationship for goal {name}")
        
        return goal_id
    
    def find_or_create(self, name: str, area_name: str = None) -> Optional[str]:
        """
        Find existing goal by name or create new one.
        
        Args:
            name: Goal name to find or create
            area_name: Optional area name for context
            
        Returns:
            Goal ID if found/created, None if failed
        """
        # First try to find existing goal
        existing_goals = self.find_by_name(name)
        
        if existing_goals:
            goal_id = existing_goals[0].get("g", {}).get("id") or existing_goals[0].get("id")
            if goal_id:
                self.logger.info(f"Found existing goal: {name} ({goal_id})")
                return goal_id
        
        # Create new goal if not found
        self.logger.info(f"Creating new goal: {name}")
        
        # Get area ID if area_name provided
        area_id = None
        if area_name:
            area_id = self.adapter.area_manager.find_or_create(area_name)
        
        return self.create(name, f"Goal for {area_name or 'general'} objectives", area_id)
    
    def find_by_name(self, name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find goals by name using semantic search."""
        
        query_params = {
            "query": f"Find goals named: {name}",
            "max_results": limit
        }
        
        response = self.adapter._execute_mcp_command("query_natural_language", query_params)
        
        if response.get("success") and response.get("results"):
            return response["results"]
        
        return []
    
    def get_goal_tasks(self, goal_id: str) -> List[Dict[str, Any]]:
        """Get all tasks contributing to this goal."""
        
        query = f"""
        MATCH (g:TASK_MANAGEMENT:GOAL {{id: '{goal_id}'}})<-[:CONTRIBUTES_TO]-(t:TASK_MANAGEMENT:TASK)
        RETURN t.id as task_id, t.name as task_name, t.description as task_description, t.status as task_status
        ORDER BY t.created DESC
        """
        
        response = self.adapter._execute_mcp_command("execute_cypher", {"query": query})
        
        if response.get("success") and response.get("results"):
            return response["results"]
        
        return []