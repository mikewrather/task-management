"""Notion adapter for task storage"""

from typing import Optional, List, Dict, Any
from ..integrations.notion import NotionClient
from ..utils.logging import VoiceLogger
from .base import TaskAdapter, TaskData


class NotionTaskAdapter(TaskAdapter):
    """Adapter for Notion task storage"""
    
    def __init__(self, notion_client: Optional[NotionClient] = None, 
                 logger: Optional[VoiceLogger] = None):
        """
        Initialize Notion adapter
        
        Args:
            notion_client: Existing NotionClient instance or create new
            logger: Logger instance
        """
        self.client = notion_client or NotionClient(logger=logger)
        self.logger = logger or VoiceLogger()
    
    def create_task(self, task_data: TaskData) -> Optional[str]:
        """Create a task in Notion"""
        # Build task with relationships
        task_properties = {
            "parent": {"database_id": self.client.database_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": task_data.name}}]
                },
                "Status": {
                    "status": {"name": task_data.status}
                },
                "Priority": {
                    "select": {"name": task_data.priority}
                },
                "Contexts": {
                    "multi_select": [{"name": ctx} for ctx in task_data.contexts]
                }
            }
        }
        
        # Add project relationship if available
        if task_data.project_id:
            task_properties["properties"]["Project"] = {
                "relation": [{"id": task_data.project_id}]
            }
        
        # Add full description as page content
        if task_data.description:
            task_properties["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": task_data.description}
                        }]
                    }
                }
            ]
        
        try:
            response = self.client.session.post(
                f'{self.client.base_url}/pages',
                json=task_properties,
                timeout=30
            )
            
            if response.ok:
                page_data = response.json()
                return page_data.get('id')
            else:
                self.logger.error("Failed to create Notion task", 
                                status_code=response.status_code)
                return None
                
        except Exception as e:
            self.logger.error("Error creating Notion task", exception=e)
            return None
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a task in Notion"""
        update_data = {"properties": {}}
        
        # Map updates to Notion properties
        if "name" in updates:
            update_data["properties"]["Name"] = {
                "title": [{"text": {"content": updates["name"]}}]
            }
        if "status" in updates:
            update_data["properties"]["Status"] = {
                "status": {"name": updates["status"]}
            }
        if "priority" in updates:
            update_data["properties"]["Priority"] = {
                "select": {"name": updates["priority"]}
            }
        if "project_id" in updates:
            update_data["properties"]["Project"] = {
                "relation": [{"id": updates["project_id"]}]
            }
        
        try:
            response = self.client.session.patch(
                f'{self.client.base_url}/pages/{task_id}',
                json=update_data,
                timeout=30
            )
            return response.ok
        except Exception as e:
            self.logger.error("Error updating task", exception=e, task_id=task_id)
            return False
    
    def get_task(self, task_id: str) -> Optional[TaskData]:
        """Retrieve a task from Notion"""
        task = self.client.get_task(task_id)
        if not task:
            return None
        
        # Convert NotionTask to TaskData
        return TaskData(
            name=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            contexts=task.contexts,
            created_at=task.created_at,
            metadata={"notion_id": task.task_id, "url": task.url}
        )
    
    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        """Search for projects in Notion"""
        # Simple keyword search in project names
        all_projects = self.client.query_projects(limit=100)
        
        query_lower = query.lower()
        matching_projects = []
        
        for project in all_projects:
            if query_lower in project.name.lower():
                matching_projects.append({
                    "id": project.project_id,
                    "name": project.name,
                    "area_id": project.area_id,
                    "area_name": project.area_name,
                    "status": project.status
                })
        
        return matching_projects
    
    def search_areas(self, query: str) -> List[Dict[str, Any]]:
        """Search for areas in Notion"""
        all_areas = self.client.query_areas(limit=100)
        
        query_lower = query.lower()
        matching_areas = []
        
        for area in all_areas:
            if query_lower in area.name.lower():
                matching_areas.append({
                    "id": area.area_id,
                    "name": area.name,
                    "status": area.status
                })
        
        return matching_areas
    
    def get_categorization_context(self) -> Dict[str, Any]:
        """Get context for categorization from Notion"""
        # Get recent voice tasks
        recent_tasks = self.client.get_voice_tasks(days_back=30)
        
        # Get all projects and areas
        projects = self.client.query_projects(limit=100)
        areas = self.client.query_areas(limit=100)
        
        # Build context
        context = {
            "recent_tasks": [],
            "project_patterns": {},
            "area_descriptions": {}
        }
        
        # Add recent task patterns
        for task in recent_tasks[:20]:  # Last 20 voice tasks
            task_info = {
                "title": task.title,
                "project_id": task.project_id,
                "project_name": task.project_name,
                "contexts": task.contexts
            }
            context["recent_tasks"].append(task_info)
        
        # Add project info
        for project in projects:
            context["project_patterns"][project.project_id] = {
                "name": project.name,
                "area_id": project.area_id,
                "area_name": project.area_name,
                "keywords": self._extract_keywords(project.name)
            }
        
        # Add area info
        for area in areas:
            context["area_descriptions"][area.area_id] = {
                "name": area.name,
                "keywords": self._extract_keywords(area.name)
            }
        
        return context
    
    def test_connection(self) -> bool:
        """Test Notion connection"""
        result = self.client.test_connection()
        return result['api_connection'] and result['database_access']
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for matching"""
        # Simple keyword extraction
        words = text.lower().split()
        # Filter out common words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        return keywords