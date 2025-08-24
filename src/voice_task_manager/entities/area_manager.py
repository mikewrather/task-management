"""
Area entity manager for GraphRAG adapter.
"""

from typing import Optional, List, Dict, Any

from .base_manager import BaseEntityManager


class AreaManager(BaseEntityManager):
    """Manager for AREA entities with validation and relationship handling."""
    
    ENTITY_TYPE = "TASK_MANAGEMENT:AREA"
    REQUIRED_FIELDS = ["name"]
    OPTIONAL_FIELDS = ["description", "parent_area"]
    
    def create(self, name: str, description: str = "", parent_area_id: Optional[str] = None) -> Optional[str]:
        """
        Create area with optional parent relationship.
        
        Args:
            name: Area name (required)
            description: Area description (optional)
            parent_area_id: Optional parent area ID for hierarchical organization
            
        Returns:
            Area ID if successful, None if failed
        """
        # Build entity data
        entity_data = {
            "name": name,  # Required
        }
        
        # Add optional fields
        if description:
            entity_data["description"] = description
        if parent_area_id:
            entity_data["parent_area"] = parent_area_id
        
        # Create the entity
        area_id = self.create_entity(entity_data)
        
        if not area_id:
            return None
        
        # Create parent relationship if provided
        if parent_area_id:
            success = self.adapter._create_relationship(
                area_id, parent_area_id, "CHILD_OF", "AREA"
            )
            if success:
                self.logger.info(f"Created parent AREA relationship: {name} -> {parent_area_id}")
            else:
                self.logger.error(f"Failed to create parent AREA relationship for {name}")
        
        return area_id
    
    def find_or_create(self, name: str, parent_area_name: str = None) -> Optional[str]:
        """
        Find existing area by name or create new one.
        
        Args:
            name: Area name to find or create
            parent_area_name: Optional parent area name for hierarchy
            
        Returns:
            Area ID if found/created, None if failed
        """
        # First try to find existing area
        existing_areas = self.find_by_name(name)
        
        if existing_areas:
            area_id = existing_areas[0].get("a", {}).get("id") or existing_areas[0].get("id")
            if area_id:
                self.logger.info(f"Found existing area: {name} ({area_id})")
                return area_id
        
        # Create new area if not found
        self.logger.info(f"Creating new area: {name}")
        
        # Get parent area ID if parent_area_name provided
        parent_area_id = None
        if parent_area_name:
            parent_area_id = self.find_or_create(parent_area_name)  # Recursive
        
        return self.create(name, f"Area for {name} related tasks", parent_area_id)
    
    def find_by_name(self, name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find areas by name using semantic search."""
        
        query_params = {
            "query": f"Find areas named: {name}",
            "max_results": limit
        }
        
        response = self.adapter._execute_mcp_command("query_natural_language", query_params)
        
        if response.get("success") and response.get("results"):
            return response["results"]
        
        return []
    
    def get_area_projects(self, area_id: str) -> List[Dict[str, Any]]:
        """Get all projects belonging to this area using natural language query."""
        
        response = self.adapter._execute_mcp_command("query_natural_language", {
            "query": f"Find all projects that belong to area with ID {area_id}, ordered by name",
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
        
        # Filter for PROJECT entities and format response
        projects = []
        for result in results:
            if result.get("labels") and "PROJECT" in result["labels"]:
                projects.append({
                    "project_id": result.get("id"),
                    "project_name": result.get("name"),
                    "project_description": result.get("description"),
                    "project_status": result.get("status")
                })
        
        return projects
    
    def get_area_hierarchy(self, area_id: str) -> Dict[str, Any]:
        """Get the full hierarchy for this area (parent and children) using natural language."""
        
        response = self.adapter._execute_mcp_command("query_natural_language", {
            "query": f"Find the hierarchy for area with ID {area_id} including parent and child areas",
            "max_results": 20
        })
        
        # Handle response format
        if isinstance(response, dict):
            if not response.get("success"):
                return {}
            results = response.get("results", [])
        elif isinstance(response, list):
            results = response
        else:
            return {}
        
        # Find the target area and build hierarchy
        target_area = None
        parent_area = None
        child_areas = []
        
        for result in results:
            if result.get("labels") and "AREA" in result["labels"]:
                if result.get("id") == area_id:
                    target_area = result
                # Note: Hierarchy relationships would need additional logic
                # For now, return basic area info
        
        if target_area:
            return {
                "area_name": target_area.get("name"),
                "parent_name": None,  # Would need additional query
                "parent_id": None,
                "children": []  # Would need additional query
            }
        
        return {}