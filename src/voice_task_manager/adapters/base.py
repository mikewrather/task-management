"""Base adapter interface for task storage systems"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class TaskData:
    """Standardized task data structure for all adapters"""
    name: str
    description: Optional[str] = None
    status: str = "Inbox"
    priority: str = "Medium"
    contexts: List[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    area_id: Optional[str] = None
    area_name: Optional[str] = None
    goal_id: Optional[str] = None
    goal_name: Optional[str] = None
    source: str = "voice"
    created_at: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.contexts is None:
            self.contexts = ["voice", "auto-processed"]
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class TaskAdapter(ABC):
    """Abstract base class for task storage adapters"""
    
    @abstractmethod
    def create_task(self, task_data: TaskData) -> Optional[str]:
        """
        Create a task in the storage system
        
        Args:
            task_data: Standardized task data
            
        Returns:
            Task ID if successful, None if failed
        """
        pass
    
    @abstractmethod
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing task
        
        Args:
            task_id: ID of the task to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_task(self, task_id: str) -> Optional[TaskData]:
        """
        Retrieve a task by ID
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            TaskData if found, None otherwise
        """
        pass
    
    @abstractmethod
    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for projects matching the query
        
        Args:
            query: Search query (keywords, description, etc.)
            
        Returns:
            List of matching projects with id, name, area info
        """
        pass
    
    @abstractmethod
    def search_areas(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for areas matching the query
        
        Args:
            query: Search query
            
        Returns:
            List of matching areas with id and name
        """
        pass
    
    @abstractmethod
    def get_categorization_context(self) -> Dict[str, Any]:
        """
        Get context data for intelligent categorization
        
        Returns:
            Dictionary containing:
            - recent_tasks: Recent tasks with their categorizations
            - project_patterns: Common keywords/patterns for projects
            - area_descriptions: Area names and descriptions
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if the adapter can connect to its storage system
        
        Returns:
            True if connection successful, False otherwise
        """
        pass