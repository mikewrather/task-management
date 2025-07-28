"""
Notion API Integration
Enhanced Notion API client for creating and managing tasks from voice recordings.
"""

import requests
import os
from typing import Optional, Dict, Any, List
from ..models.voice_file import VoiceFile
from ..models.task import NotionTask
from ..models.notion_goal import NotionGoal
from ..models.notion_note import NotionNote  
from ..models.notion_event import NotionEvent
from ..models.notion_reference import NotionReference
from ..utils.logging import VoiceLogger

class NotionClient:
    """Enhanced Notion API client for task management"""
    
    def __init__(self, api_token: Optional[str] = None, database_id: Optional[str] = None, 
                 logger: Optional[VoiceLogger] = None):
        """
        Initialize Notion client
        
        Args:
            api_token: Notion integration token (from environment if None)
            database_id: Notion database ID for tasks (from environment if None)
            logger: Logger instance for consistent logging
        """
        self.api_token = api_token or os.getenv('NOTION_TOKEN')
        self.database_id = database_id or os.getenv('NOTION_TASKS_DB')
        self.logger = logger or VoiceLogger()
        
        if not self.api_token:
            raise ValueError("Notion API token is required. Set NOTION_TOKEN environment variable.")
        
        if not self.database_id:
            raise ValueError("Notion database ID is required. Set NOTION_TASKS_DB environment variable.")
        
        self.base_url = 'https://api.notion.com/v1'
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        })
    
    def create_task_from_voice(self, voice_file: VoiceFile, transcript: str) -> Optional[NotionTask]:
        """
        Create a Notion task from a voice recording
        
        Args:
            voice_file: VoiceFile object containing metadata
            transcript: Transcribed text from the voice recording
            
        Returns:
            NotionTask object if successful, None if failed
        """
        self.logger.info("📝 Creating Notion task", file_id=voice_file.file_id)
        
        try:
            # Create task data structure
            task_data = self._build_task_data(voice_file, transcript)
            
            # Make API request to create page
            response = self.session.post(
                f'{self.base_url}/pages',
                json=task_data,
                timeout=30
            )
            
            if not response.ok:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Notion API request failed",
                    file_id=voice_file.file_id,
                    status_code=response.status_code,
                    error_details=error_details
                )
                return None
            
            # Parse successful response
            page_data = response.json()
            task_url = page_data.get('url', 'Unknown')
            task_id = page_data.get('id')
            
            # Create NotionTask object
            notion_task = NotionTask.create_from_voice(
                voice_file_id=voice_file.file_id,
                transcript=transcript,
                task_id=task_id,
                url=task_url
            )
            
            self.logger.success(
                "Notion task created successfully",
                file_id=voice_file.file_id,
                task_id=task_id,
                task_url=task_url
            )
            
            return notion_task
            
        except requests.RequestException as e:
            self.logger.error(
                "Network error during Notion API request",
                exception=e,
                file_id=voice_file.file_id
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error during task creation",
                exception=e,
                file_id=voice_file.file_id
            )
            return None
    
    def _build_task_data(self, voice_file: VoiceFile, transcript: str) -> Dict[str, Any]:
        """
        Build Notion page data structure for task creation
        
        Args:
            voice_file: VoiceFile object containing metadata
            transcript: Transcribed text
            
        Returns:
            Dictionary formatted for Notion API
        """
        # Create concise title from transcript
        title_text = transcript[:60] + "..." if len(transcript) > 60 else transcript
        
        task_data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": f"Voice Note: {title_text}"}}]
                },
                "Status": {
                    "status": {"name": "Inbox"}
                },
                "Contexts": {
                    "multi_select": [
                        {"name": "voice"},
                        {"name": "auto-processed"}
                    ]
                }
            }
        }
        
        # Add full transcript as page content for longer texts
        if len(transcript) > 100:
            task_data["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "type": "text", 
                            "text": {"content": f"Full transcript: {transcript}"}
                        }]
                    }
                }
            ]
        
        return task_data
    
    def update_task_status(self, task: NotionTask, new_status: str) -> bool:
        """
        Update the status of an existing Notion task
        
        Args:
            task: NotionTask to update
            new_status: New status value
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Updating task status to '{new_status}'", task_id=task.task_id)
        
        try:
            update_data = {
                "properties": {
                    "Status": {
                        "status": {"name": new_status}
                    }
                }
            }
            
            response = self.session.patch(
                f'{self.base_url}/pages/{task.task_id}',
                json=update_data,
                timeout=30
            )
            
            if response.ok:
                task.update_status(new_status)
                self.logger.success(f"Task status updated to '{new_status}'", task_id=task.task_id)
                return True
            else:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Failed to update task status",
                    task_id=task.task_id,
                    new_status=new_status,
                    error_details=error_details
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Error updating task status",
                exception=e,
                task_id=task.task_id,
                new_status=new_status
            )
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete (archive) a task in Notion
        
        Args:
            task_id: Notion page ID
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Deleting task", task_id=task_id)
        
        try:
            # Archive the page (Notion's way of "deleting")
            archive_data = {
                "archived": True
            }
            
            response = self.session.patch(
                f'{self.base_url}/pages/{task_id}',
                json=archive_data,
                timeout=30
            )
            
            if response.ok:
                self.logger.success(f"Task deleted (archived) successfully", task_id=task_id)
                return True
            else:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Failed to delete task",
                    task_id=task_id,
                    error_details=error_details
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Error deleting task",
                exception=e,
                task_id=task_id
            )
            return False
    
    def get_task(self, task_id: str) -> Optional[NotionTask]:
        """
        Retrieve a task from Notion
        
        Args:
            task_id: Notion page ID
            
        Returns:
            NotionTask object if found, None otherwise
        """
        try:
            response = self.session.get(
                f'{self.base_url}/pages/{task_id}',
                timeout=30
            )
            
            if response.ok:
                page_data = response.json()
                return NotionTask.from_notion_response(page_data)
            else:
                self.logger.warning(f"Task not found or inaccessible", task_id=task_id)
                return None
                
        except Exception as e:
            self.logger.error("Error retrieving task", exception=e, task_id=task_id)
            return None
    
    def query_tasks(self, filter_criteria: Optional[Dict[str, Any]] = None, 
                   limit: int = 100) -> List[NotionTask]:
        """
        Query tasks from the Notion database
        
        Args:
            filter_criteria: Notion database filter criteria
            limit: Maximum number of tasks to return
            
        Returns:
            List of NotionTask objects
        """
        try:
            query_data = {
                "page_size": min(limit, 100)  # Notion API limit
            }
            
            if filter_criteria:
                query_data["filter"] = filter_criteria
            
            response = self.session.post(
                f'{self.base_url}/databases/{self.database_id}/query',
                json=query_data,
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                tasks = []
                
                for page in data.get('results', []):
                    task = NotionTask.from_notion_response(page)
                    if task:
                        tasks.append(task)
                
                self.logger.info(f"Retrieved {len(tasks)} tasks from Notion", count=len(tasks))
                return tasks
            else:
                error_details = self._parse_error_response(response)
                self.logger.error("Failed to query tasks", error_details=error_details)
                return []
                
        except Exception as e:
            self.logger.error("Error querying tasks", exception=e)
            return []
    
    def get_voice_tasks(self, days_back: int = 30) -> List[NotionTask]:
        """
        Get tasks created from voice recordings in the last N days
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of voice-related NotionTask objects
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        filter_criteria = {
            "and": [
                {
                    "property": "Contexts",
                    "multi_select": {
                        "contains": "voice"
                    }
                },
                {
                    "property": "Created time",
                    "created_time": {
                        "on_or_after": cutoff_date.isoformat()
                    }
                }
            ]
        }
        
        return self.query_tasks(filter_criteria)
    
    def query_projects(self, filter_criteria: Optional[Dict[str, Any]] = None, 
                      limit: int = 100) -> List['NotionProject']:
        """
        Query projects from the Notion Projects database
        
        Args:
            filter_criteria: Notion database filter criteria
            limit: Maximum number of projects to return
            
        Returns:
            List of NotionProject objects
        """
        from ..models.notion_project import NotionProject
        
        projects_db_id = os.getenv('NOTION_PROJECTS_DB')
        if not projects_db_id:
            self.logger.error("NOTION_PROJECTS_DB not configured")
            return []
        
        try:
            query_data = {
                "page_size": min(limit, 100)  # Notion API limit
            }
            
            if filter_criteria:
                query_data["filter"] = filter_criteria
            
            response = self.session.post(
                f'{self.base_url}/databases/{projects_db_id}/query',
                json=query_data,
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                projects = []
                
                for page in data.get('results', []):
                    project = NotionProject.from_notion_data(page)
                    if project:
                        projects.append(project)
                
                self.logger.info(f"Retrieved {len(projects)} projects from Notion", count=len(projects))
                return projects
            else:
                error_details = self._parse_error_response(response)
                self.logger.error("Failed to query projects", error_details=error_details)
                return []
                
        except Exception as e:
            self.logger.error("Error querying projects", exception=e)
            return []
    
    def query_areas(self, filter_criteria: Optional[Dict[str, Any]] = None, 
                   limit: int = 100) -> List['NotionArea']:
        """
        Query areas from the Notion Areas database
        
        Args:
            filter_criteria: Notion database filter criteria
            limit: Maximum number of areas to return
            
        Returns:
            List of NotionArea objects
        """
        from ..models.notion_area import NotionArea
        
        areas_db_id = os.getenv('NOTION_AREAS_DB')
        if not areas_db_id:
            self.logger.error("NOTION_AREAS_DB not configured")
            return []
        
        try:
            query_data = {
                "page_size": min(limit, 100)  # Notion API limit
            }
            
            if filter_criteria:
                query_data["filter"] = filter_criteria
            
            response = self.session.post(
                f'{self.base_url}/databases/{areas_db_id}/query',
                json=query_data,
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                areas = []
                
                for page in data.get('results', []):
                    area = NotionArea.from_notion_data(page)
                    if area:
                        areas.append(area)
                
                self.logger.info(f"Retrieved {len(areas)} areas from Notion", count=len(areas))
                return areas
            else:
                error_details = self._parse_error_response(response)
                self.logger.error("Failed to query areas", error_details=error_details)
                return []
                
        except Exception as e:
            self.logger.error("Error querying areas", exception=e)
            return []
    
    def create_project(self, project: 'NotionProject') -> Optional['NotionProject']:
        """
        Create a new project in Notion
        
        Args:
            project: NotionProject object to create
            
        Returns:
            NotionProject object if successful, None if failed
        """
        projects_db_id = os.getenv('NOTION_PROJECTS_DB')
        if not projects_db_id:
            self.logger.error("NOTION_PROJECTS_DB not configured")
            return None
        
        self.logger.info("Creating Notion project", project_name=project.name)
        
        try:
            # Create project data structure
            project_data = self._build_project_data(project, projects_db_id)
            
            # Make API request to create page
            response = self.session.post(
                f'{self.base_url}/pages',
                json=project_data,
                timeout=30
            )
            
            if not response.ok:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Notion API request failed",
                    project_name=project.name,
                    status_code=response.status_code,
                    error_details=error_details
                )
                return None
            
            # Parse successful response
            page_data = response.json()
            from ..models.notion_project import NotionProject
            created_project = NotionProject.from_notion_data(page_data)
            
            self.logger.success(
                "Notion project created successfully",
                project_name=project.name,
                project_id=created_project.project_id if created_project else None
            )
            
            return created_project
            
        except requests.RequestException as e:
            self.logger.error(
                "Network error during Notion API request",
                exception=e,
                project_name=project.name
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error during project creation",
                exception=e,
                project_name=project.name
            )
            return None
    
    def update_project(self, project: 'NotionProject') -> bool:
        """
        Update an existing project in Notion
        
        Args:
            project: NotionProject object with updated data
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Updating project", project_id=project.project_id)
        
        try:
            update_data = self._build_project_update_data(project)
            
            response = self.session.patch(
                f'{self.base_url}/pages/{project.project_id}',
                json=update_data,
                timeout=30
            )
            
            if response.ok:
                self.logger.success(f"Project updated successfully", project_id=project.project_id)
                return True
            else:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Failed to update project",
                    project_id=project.project_id,
                    error_details=error_details
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Error updating project",
                exception=e,
                project_id=project.project_id
            )
            return False
    
    def delete_project(self, project_id: str) -> bool:
        """
        Delete (archive) a project in Notion
        
        Args:
            project_id: Notion page ID
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Deleting project", project_id=project_id)
        
        try:
            # Archive the page (Notion's way of "deleting")
            archive_data = {
                "archived": True
            }
            
            response = self.session.patch(
                f'{self.base_url}/pages/{project_id}',
                json=archive_data,
                timeout=30
            )
            
            if response.ok:
                self.logger.success(f"Project deleted (archived) successfully", project_id=project_id)
                return True
            else:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Failed to delete project",
                    project_id=project_id,
                    error_details=error_details
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Error deleting project",
                exception=e,
                project_id=project_id
            )
            return False
    
    def create_area(self, area: 'NotionArea') -> Optional['NotionArea']:
        """
        Create a new area in Notion
        
        Args:
            area: NotionArea object to create
            
        Returns:
            NotionArea object if successful, None if failed
        """
        areas_db_id = os.getenv('NOTION_AREAS_DB')
        if not areas_db_id:
            self.logger.error("NOTION_AREAS_DB not configured")
            return None
        
        self.logger.info("Creating Notion area", area_name=area.name)
        
        try:
            # Create area data structure
            area_data = self._build_area_data(area, areas_db_id)
            
            # Make API request to create page
            response = self.session.post(
                f'{self.base_url}/pages',
                json=area_data,
                timeout=30
            )
            
            if not response.ok:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Notion API request failed",
                    area_name=area.name,
                    status_code=response.status_code,
                    error_details=error_details
                )
                return None
            
            # Parse successful response
            page_data = response.json()
            from ..models.notion_area import NotionArea
            created_area = NotionArea.from_notion_data(page_data)
            
            self.logger.success(
                "Notion area created successfully",
                area_name=area.name,
                area_id=created_area.area_id if created_area else None
            )
            
            return created_area
            
        except requests.RequestException as e:
            self.logger.error(
                "Network error during Notion API request",
                exception=e,
                area_name=area.name
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error during area creation",
                exception=e,
                area_name=area.name
            )
            return None
    
    def update_area(self, area: 'NotionArea') -> bool:
        """
        Update an existing area in Notion
        
        Args:
            area: NotionArea object with updated data
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Updating area", area_id=area.area_id)
        
        try:
            update_data = self._build_area_update_data(area)
            
            response = self.session.patch(
                f'{self.base_url}/pages/{area.area_id}',
                json=update_data,
                timeout=30
            )
            
            if response.ok:
                self.logger.success(f"Area updated successfully", area_id=area.area_id)
                return True
            else:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Failed to update area",
                    area_id=area.area_id,
                    error_details=error_details
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Error updating area",
                exception=e,
                area_id=area.area_id
            )
            return False
    
    def delete_area(self, area_id: str) -> bool:
        """
        Delete (archive) an area in Notion
        
        Args:
            area_id: Notion page ID
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Deleting area", area_id=area_id)
        
        try:
            # Archive the page (Notion's way of "deleting")
            archive_data = {
                "archived": True
            }
            
            response = self.session.patch(
                f'{self.base_url}/pages/{area_id}',
                json=archive_data,
                timeout=30
            )
            
            if response.ok:
                self.logger.success(f"Area deleted (archived) successfully", area_id=area_id)
                return True
            else:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Failed to delete area",
                    area_id=area_id,
                    error_details=error_details
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Error deleting area",
                exception=e,
                area_id=area_id
            )
            return False
    
    def _build_project_data(self, project: 'NotionProject', database_id: str) -> Dict[str, Any]:
        """
        Build Notion page data structure for project creation
        
        Args:
            project: NotionProject object
            database_id: Database ID for projects
            
        Returns:
            Dictionary formatted for Notion API
        """
        project_data = {
            "parent": {"database_id": database_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": project.name}}]
                },
                "Status": {
                    "select": {"name": project.status}
                },
                "Priority": {
                    "select": {"name": project.priority}
                }
            }
        }
        
        # Add relationships if present
        if project.area_id:
            project_data["properties"]["Area"] = {
                "relation": [{"id": project.area_id}]
            }
        
        if project.goal_id:
            project_data["properties"]["Goal"] = {
                "relation": [{"id": project.goal_id}]
            }
        
        if project.parent_project_id:
            project_data["properties"]["Parent Project"] = {
                "relation": [{"id": project.parent_project_id}]
            }
        
        # Add dates if present
        if project.start_date:
            project_data["properties"]["Start Date"] = {
                "date": {"start": project.start_date.isoformat()}
            }
        
        if project.timeline and project.timeline.start:
            if project.timeline.end:
                project_data["properties"]["Timeline"] = {
                    "date": {
                        "start": project.timeline.start.isoformat(),
                        "end": project.timeline.end.isoformat()
                    }
                }
            else:
                project_data["properties"]["Timeline"] = {
                    "date": {"start": project.timeline.start.isoformat()}
                }
        
        return project_data
    
    def _build_project_update_data(self, project: 'NotionProject') -> Dict[str, Any]:
        """
        Build Notion update data structure for project updates
        
        Args:
            project: NotionProject object with updated data
            
        Returns:
            Dictionary formatted for Notion API
        """
        return {
            "properties": {
                "Name": {
                    "title": [{"text": {"content": project.name}}]
                },
                "Status": {
                    "select": {"name": project.status}
                },
                "Priority": {
                    "select": {"name": project.priority}
                },
                "Archive": {
                    "checkbox": project.archive
                }
            }
        }
    
    def _build_area_data(self, area: 'NotionArea', database_id: str) -> Dict[str, Any]:
        """
        Build Notion page data structure for area creation
        
        Args:
            area: NotionArea object
            database_id: Database ID for areas
            
        Returns:
            Dictionary formatted for Notion API
        """
        area_data = {
            "parent": {"database_id": database_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": area.name}}]
                },
                "Status": {
                    "select": {"name": area.status}
                },
                "Priority": {
                    "select": {"name": area.priority}
                }
            }
        }
        
        # Add relationships if present
        if area.goal_id:
            area_data["properties"]["Goal"] = {
                "relation": [{"id": area.goal_id}]
            }
        
        if area.parent_project_id:
            area_data["properties"]["Parent Project"] = {
                "relation": [{"id": area.parent_project_id}]
            }
        
        # Add dates if present
        if area.start_date:
            area_data["properties"]["Start Date"] = {
                "date": {"start": area.start_date.isoformat()}
            }
        
        if area.timeline and area.timeline.start:
            if area.timeline.end:
                area_data["properties"]["Timeline"] = {
                    "date": {
                        "start": area.timeline.start.isoformat(),
                        "end": area.timeline.end.isoformat()
                    }
                }
            else:
                area_data["properties"]["Timeline"] = {
                    "date": {"start": area.timeline.start.isoformat()}
                }
        
        return area_data
    
    def _build_area_update_data(self, area: 'NotionArea') -> Dict[str, Any]:
        """
        Build Notion update data structure for area updates
        
        Args:
            area: NotionArea object with updated data
            
        Returns:
            Dictionary formatted for Notion API
        """
        return {
            "properties": {
                "Name": {
                    "title": [{"text": {"content": area.name}}]
                },
                "Status": {
                    "select": {"name": area.status}
                },
                "Priority": {
                    "select": {"name": area.priority}
                },
                "Archive": {
                    "checkbox": area.archive
                }
            }
        }
    
    def query_goals(self, filter_criteria: Optional[Dict[str, Any]] = None, 
                   limit: int = 100) -> List[NotionGoal]:
        """
        Query goals from the Notion Goals database
        
        Args:
            filter_criteria: Notion database filter criteria
            limit: Maximum number of goals to return
            
        Returns:
            List of NotionGoal objects
        """
        goals_db_id = os.getenv('NOTION_GOALS_DB')
        if not goals_db_id:
            self.logger.error("NOTION_GOALS_DB not configured")
            return []
        
        try:
            query_data = {
                "page_size": min(limit, 100)  # Notion API limit
            }
            
            if filter_criteria:
                query_data["filter"] = filter_criteria
            
            response = self.session.post(
                f'{self.base_url}/databases/{goals_db_id}/query',
                json=query_data,
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                goals = []
                
                for page in data.get('results', []):
                    goal = NotionGoal.from_notion_data(page)
                    if goal:
                        goals.append(goal)
                
                self.logger.info(f"Retrieved {len(goals)} goals from Notion", count=len(goals))
                return goals
            else:
                error_details = self._parse_error_response(response)
                self.logger.error("Failed to query goals", error_details=error_details)
                return []
                
        except Exception as e:
            self.logger.error("Error querying goals", exception=e)
            return []
    
    def get_goal(self, goal_id: str) -> Optional[NotionGoal]:
        """
        Retrieve a goal from Notion
        
        Args:
            goal_id: Notion page ID
            
        Returns:
            NotionGoal object if found, None otherwise
        """
        try:
            response = self.session.get(
                f'{self.base_url}/pages/{goal_id}',
                timeout=30
            )
            
            if response.ok:
                page_data = response.json()
                return NotionGoal.from_notion_data(page_data)
            else:
                self.logger.warning(f"Goal not found or inaccessible", goal_id=goal_id)
                return None
                
        except Exception as e:
            self.logger.error("Error retrieving goal", exception=e, goal_id=goal_id)
            return None
    
    def create_goal(self, goal: NotionGoal) -> Optional[NotionGoal]:
        """
        Create a new goal in Notion
        
        Args:
            goal: NotionGoal object to create
            
        Returns:
            NotionGoal object if successful, None if failed
        """
        goals_db_id = os.getenv('NOTION_GOALS_DB')
        if not goals_db_id:
            self.logger.error("NOTION_GOALS_DB not configured")
            return None
        
        self.logger.info("Creating Notion goal", goal_name=goal.name)
        
        try:
            # Create goal data structure
            goal_data = self._build_goal_data(goal, goals_db_id)
            
            # Make API request to create page
            response = self.session.post(
                f'{self.base_url}/pages',
                json=goal_data,
                timeout=30
            )
            
            if not response.ok:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Notion API request failed",
                    goal_name=goal.name,
                    status_code=response.status_code,
                    error_details=error_details
                )
                return None
            
            # Parse successful response
            page_data = response.json()
            created_goal = NotionGoal.from_notion_data(page_data)
            
            self.logger.success(
                "Notion goal created successfully",
                goal_name=goal.name,
                goal_id=created_goal.goal_id if created_goal else None
            )
            
            return created_goal
            
        except requests.RequestException as e:
            self.logger.error(
                "Network error during Notion API request",
                exception=e,
                goal_name=goal.name
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error during goal creation",
                exception=e,
                goal_name=goal.name
            )
            return None
    
    def update_goal(self, goal: NotionGoal) -> bool:
        """
        Update an existing goal in Notion
        
        Args:
            goal: NotionGoal object with updated data
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Updating goal", goal_id=goal.goal_id)
        
        try:
            update_data = self._build_goal_update_data(goal)
            
            response = self.session.patch(
                f'{self.base_url}/pages/{goal.goal_id}',
                json=update_data,
                timeout=30
            )
            
            if response.ok:
                self.logger.success(f"Goal updated successfully", goal_id=goal.goal_id)
                return True
            else:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Failed to update goal",
                    goal_id=goal.goal_id,
                    error_details=error_details
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Error updating goal",
                exception=e,
                goal_id=goal.goal_id
            )
            return False
    
    def delete_goal(self, goal_id: str) -> bool:
        """
        Delete (archive) a goal in Notion
        
        Args:
            goal_id: Notion page ID
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Deleting goal", goal_id=goal_id)
        
        try:
            # Archive the page (Notion's way of "deleting")
            archive_data = {
                "archived": True
            }
            
            response = self.session.patch(
                f'{self.base_url}/pages/{goal_id}',
                json=archive_data,
                timeout=30
            )
            
            if response.ok:
                self.logger.success(f"Goal deleted (archived) successfully", goal_id=goal_id)
                return True
            else:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Failed to delete goal",
                    goal_id=goal_id,
                    error_details=error_details
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Error deleting goal",
                exception=e,
                goal_id=goal_id
            )
            return False
    
    def _build_goal_data(self, goal: NotionGoal, database_id: str) -> Dict[str, Any]:
        """
        Build Notion page data structure for goal creation
        
        Args:
            goal: NotionGoal object
            database_id: Database ID for goals
            
        Returns:
            Dictionary formatted for Notion API
        """
        goal_data = {
            "parent": {"database_id": database_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": goal.name}}]
                },
                "Status": {
                    "select": {"name": goal.status}
                },
                "Priority": {
                    "select": {"name": goal.priority}
                },
                "Type": {
                    "select": {"name": goal.goal_type}
                }
            }
        }
        
        # Add optional properties
        if goal.description:
            goal_data["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": goal.description}}]
                    }
                }
            ]
        
        # Add dates if present
        if goal.start_date:
            goal_data["properties"]["Start Date"] = {
                "date": {"start": goal.start_date.isoformat()}
            }
        
        if goal.target_date:
            goal_data["properties"]["Target Date"] = {
                "date": {"start": goal.target_date.isoformat()}
            }
        
        return goal_data
    
    def _build_goal_update_data(self, goal: NotionGoal) -> Dict[str, Any]:
        """
        Build Notion update data structure for goal updates
        
        Args:
            goal: NotionGoal object with updated data
            
        Returns:
            Dictionary formatted for Notion API
        """
        return {
            "properties": {
                "Name": {
                    "title": [{"text": {"content": goal.name}}]
                },
                "Status": {
                    "select": {"name": goal.status}
                },
                "Priority": {
                    "select": {"name": goal.priority}
                },
                "Type": {
                    "select": {"name": goal.goal_type}
                },
                "Archive": {
                    "checkbox": goal.archive
                }
            }
        }
    
    def query_notes(self, filter_criteria: Optional[Dict[str, Any]] = None, 
                   limit: int = 100) -> List[NotionNote]:
        """
        Query notes from the Notion Notes database
        
        Args:
            filter_criteria: Notion database filter criteria
            limit: Maximum number of notes to return
            
        Returns:
            List of NotionNote objects
        """
        notes_db_id = os.getenv('NOTION_NOTES_DB')
        if not notes_db_id:
            self.logger.error("NOTION_NOTES_DB not configured")
            return []
        
        try:
            query_data = {
                "page_size": min(limit, 100)  # Notion API limit
            }
            
            if filter_criteria:
                query_data["filter"] = filter_criteria
            
            response = self.session.post(
                f'{self.base_url}/databases/{notes_db_id}/query',
                json=query_data,
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                notes = []
                
                for page in data.get('results', []):
                    note = NotionNote.from_notion_data(page)
                    if note:
                        notes.append(note)
                
                self.logger.info(f"Retrieved {len(notes)} notes from Notion", count=len(notes))
                return notes
            else:
                error_details = self._parse_error_response(response)
                self.logger.error("Failed to query notes", error_details=error_details)
                return []
                
        except Exception as e:
            self.logger.error("Error querying notes", exception=e)
            return []
    
    def get_note(self, note_id: str) -> Optional[NotionNote]:
        """
        Retrieve a note from Notion
        
        Args:
            note_id: Notion page ID
            
        Returns:
            NotionNote object if found, None otherwise
        """
        try:
            response = self.session.get(
                f'{self.base_url}/pages/{note_id}',
                timeout=30
            )
            
            if response.ok:
                page_data = response.json()
                return NotionNote.from_notion_data(page_data)
            else:
                self.logger.warning(f"Note not found or inaccessible", note_id=note_id)
                return None
                
        except Exception as e:
            self.logger.error("Error retrieving note", exception=e, note_id=note_id)
            return None
    
    def create_note(self, note: NotionNote) -> Optional[NotionNote]:
        """
        Create a new note in Notion
        
        Args:
            note: NotionNote object to create
            
        Returns:
            NotionNote object if successful, None if failed
        """
        notes_db_id = os.getenv('NOTION_NOTES_DB')
        if not notes_db_id:
            self.logger.error("NOTION_NOTES_DB not configured")
            return None
        
        self.logger.info("Creating Notion note", note_title=note.title)
        
        try:
            # Create note data structure
            note_data = self._build_note_data(note, notes_db_id)
            
            # Make API request to create page
            response = self.session.post(
                f'{self.base_url}/pages',
                json=note_data,
                timeout=30
            )
            
            if not response.ok:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Notion API request failed",
                    note_title=note.title,
                    status_code=response.status_code,
                    error_details=error_details
                )
                return None
            
            # Parse successful response
            page_data = response.json()
            created_note = NotionNote.from_notion_data(page_data)
            
            self.logger.success(
                "Notion note created successfully",
                note_title=note.title,
                note_id=created_note.note_id if created_note else None
            )
            
            return created_note
            
        except requests.RequestException as e:
            self.logger.error(
                "Network error during Notion API request",
                exception=e,
                note_title=note.title
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error during note creation",
                exception=e,
                note_title=note.title
            )
            return None
    
    def update_note(self, note: NotionNote) -> bool:
        """
        Update an existing note in Notion
        
        Args:
            note: NotionNote object with updated data
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Updating note", note_id=note.note_id)
        
        try:
            update_data = self._build_note_update_data(note)
            
            response = self.session.patch(
                f'{self.base_url}/pages/{note.note_id}',
                json=update_data,
                timeout=30
            )
            
            if response.ok:
                self.logger.success(f"Note updated successfully", note_id=note.note_id)
                return True
            else:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Failed to update note",
                    note_id=note.note_id,
                    error_details=error_details
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Error updating note",
                exception=e,
                note_id=note.note_id
            )
            return False
    
    def delete_note(self, note_id: str) -> bool:
        """
        Delete (archive) a note in Notion
        
        Args:
            note_id: Notion page ID
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Deleting note", note_id=note_id)
        
        try:
            # Archive the page (Notion's way of "deleting")
            archive_data = {
                "archived": True
            }
            
            response = self.session.patch(
                f'{self.base_url}/pages/{note_id}',
                json=archive_data,
                timeout=30
            )
            
            if response.ok:
                self.logger.success(f"Note deleted (archived) successfully", note_id=note_id)
                return True
            else:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Failed to delete note",
                    note_id=note_id,
                    error_details=error_details
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Error deleting note",
                exception=e,
                note_id=note_id
            )
            return False
    
    def _build_note_data(self, note: NotionNote, database_id: str) -> Dict[str, Any]:
        """
        Build Notion page data structure for note creation
        
        Args:
            note: NotionNote object
            database_id: Database ID for notes
            
        Returns:
            Dictionary formatted for Notion API
        """
        note_data = {
            "parent": {"database_id": database_id},
            "properties": {
                "Title": {
                    "title": [{"text": {"content": note.title}}]
                },
                "Status": {
                    "select": {"name": note.status}
                },
                "Type": {
                    "select": {"name": note.note_type}
                },
                "Priority": {
                    "select": {"name": note.priority}
                }
            }
        }
        
        # Add tags if present
        if note.tags:
            note_data["properties"]["Tags"] = {
                "multi_select": [{"name": tag} for tag in note.tags]
            }
        
        # Add relationships if present
        if note.project_id:
            note_data["properties"]["Project"] = {
                "relation": [{"id": note.project_id}]
            }
        
        if note.area_id:
            note_data["properties"]["Area"] = {
                "relation": [{"id": note.area_id}]
            }
        
        if note.goal_id:
            note_data["properties"]["Goal"] = {
                "relation": [{"id": note.goal_id}]
            }
        
        # Add optional properties
        if note.source_url:
            note_data["properties"]["Source URL"] = {
                "url": note.source_url
            }
        
        if note.author:
            note_data["properties"]["Author"] = {
                "rich_text": [{"text": {"content": note.author}}]
            }
        
        # Add content as page content
        if note.content:
            note_data["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": note.content}}]
                    }
                }
            ]
        
        return note_data
    
    def _build_note_update_data(self, note: NotionNote) -> Dict[str, Any]:
        """
        Build Notion update data structure for note updates
        
        Args:
            note: NotionNote object with updated data
            
        Returns:
            Dictionary formatted for Notion API
        """
        update_data = {
            "properties": {
                "Title": {
                    "title": [{"text": {"content": note.title}}]
                },
                "Status": {
                    "select": {"name": note.status}
                },
                "Type": {
                    "select": {"name": note.note_type}
                },
                "Priority": {
                    "select": {"name": note.priority}
                },
                "Archive": {
                    "checkbox": note.archive
                }
            }
        }
        
        # Add tags if present
        if note.tags:
            update_data["properties"]["Tags"] = {
                "multi_select": [{"name": tag} for tag in note.tags]
            }
        
        # Add optional properties
        if note.source_url:
            update_data["properties"]["Source URL"] = {
                "url": note.source_url
            }
        
        if note.author:
            update_data["properties"]["Author"] = {
                "rich_text": [{"text": {"content": note.author}}]
            }
        
        return update_data
    
    def query_events(self, filter_criteria: Optional[Dict[str, Any]] = None, 
                    limit: int = 100) -> List[NotionEvent]:
        """
        Query events from the Notion Events database
        
        Args:
            filter_criteria: Notion database filter criteria
            limit: Maximum number of events to return
            
        Returns:
            List of NotionEvent objects
        """
        events_db_id = os.getenv('NOTION_EVENTS_DB')
        if not events_db_id:
            self.logger.error("NOTION_EVENTS_DB not configured")
            return []
        
        try:
            query_data = {
                "page_size": min(limit, 100)  # Notion API limit
            }
            
            if filter_criteria:
                query_data["filter"] = filter_criteria
            
            response = self.session.post(
                f'{self.base_url}/databases/{events_db_id}/query',
                json=query_data,
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                events = []
                
                for page in data.get('results', []):
                    event = NotionEvent.from_notion_data(page)
                    if event:
                        events.append(event)
                
                self.logger.info(f"Retrieved {len(events)} events from Notion", count=len(events))
                return events
            else:
                error_details = self._parse_error_response(response)
                self.logger.error("Failed to query events", error_details=error_details)
                return []
                
        except Exception as e:
            self.logger.error("Error querying events", exception=e)
            return []
    
    def get_event(self, event_id: str) -> Optional[NotionEvent]:
        """
        Retrieve an event from Notion
        
        Args:
            event_id: Notion page ID
            
        Returns:
            NotionEvent object if found, None otherwise
        """
        try:
            response = self.session.get(
                f'{self.base_url}/pages/{event_id}',
                timeout=30
            )
            
            if response.ok:
                page_data = response.json()
                return NotionEvent.from_notion_data(page_data)
            else:
                self.logger.warning(f"Event not found or inaccessible", event_id=event_id)
                return None
                
        except Exception as e:
            self.logger.error("Error retrieving event", exception=e, event_id=event_id)
            return None
    
    def create_event(self, event: NotionEvent) -> Optional[NotionEvent]:
        """
        Create a new event in Notion
        
        Args:
            event: NotionEvent object to create
            
        Returns:
            NotionEvent object if successful, None if failed
        """
        events_db_id = os.getenv('NOTION_EVENTS_DB')
        if not events_db_id:
            self.logger.error("NOTION_EVENTS_DB not configured")
            return None
        
        self.logger.info("Creating Notion event", event_title=event.title)
        
        try:
            # Create event data structure
            event_data = self._build_event_data(event, events_db_id)
            
            # Make API request to create page
            response = self.session.post(
                f'{self.base_url}/pages',
                json=event_data,
                timeout=30
            )
            
            if not response.ok:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Notion API request failed",
                    event_title=event.title,
                    status_code=response.status_code,
                    error_details=error_details
                )
                return None
            
            # Parse successful response
            page_data = response.json()
            created_event = NotionEvent.from_notion_data(page_data)
            
            self.logger.success(
                "Notion event created successfully",
                event_title=event.title,
                event_id=created_event.event_id if created_event else None
            )
            
            return created_event
            
        except requests.RequestException as e:
            self.logger.error(
                "Network error during Notion API request",
                exception=e,
                event_title=event.title
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error during event creation",
                exception=e,
                event_title=event.title
            )
            return None
    
    def update_event(self, event: NotionEvent) -> bool:
        """
        Update an existing event in Notion
        
        Args:
            event: NotionEvent object with updated data
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Updating event", event_id=event.event_id)
        
        try:
            update_data = self._build_event_update_data(event)
            
            response = self.session.patch(
                f'{self.base_url}/pages/{event.event_id}',
                json=update_data,
                timeout=30
            )
            
            if response.ok:
                self.logger.success(f"Event updated successfully", event_id=event.event_id)
                return True
            else:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Failed to update event",
                    event_id=event.event_id,
                    error_details=error_details
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Error updating event",
                exception=e,
                event_id=event.event_id
            )
            return False
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete (archive) an event in Notion
        
        Args:
            event_id: Notion page ID
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Deleting event", event_id=event_id)
        
        try:
            # Archive the page (Notion's way of "deleting")
            archive_data = {
                "archived": True
            }
            
            response = self.session.patch(
                f'{self.base_url}/pages/{event_id}',
                json=archive_data,
                timeout=30
            )
            
            if response.ok:
                self.logger.success(f"Event deleted (archived) successfully", event_id=event_id)
                return True
            else:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Failed to delete event",
                    event_id=event_id,
                    error_details=error_details
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Error deleting event",
                exception=e,
                event_id=event_id
            )
            return False
    
    def _build_event_data(self, event: NotionEvent, database_id: str) -> Dict[str, Any]:
        """
        Build Notion page data structure for event creation
        
        Args:
            event: NotionEvent object
            database_id: Database ID for events
            
        Returns:
            Dictionary formatted for Notion API
        """
        event_data = {
            "parent": {"database_id": database_id},
            "properties": {
                "Title": {
                    "title": [{"text": {"content": event.title}}]
                },
                "Status": {
                    "select": {"name": event.status}
                },
                "Type": {
                    "select": {"name": event.event_type}
                },
                "Priority": {
                    "select": {"name": event.priority}
                }
            }
        }
        
        # Add timing properties
        if event.start_time:
            event_data["properties"]["Start Time"] = {
                "date": {"start": event.start_time.isoformat()}
            }
        
        if event.end_time:
            event_data["properties"]["End Time"] = {
                "date": {"start": event.end_time.isoformat()}
            }
        
        if event.duration_minutes:
            event_data["properties"]["Duration"] = {
                "number": event.duration_minutes
            }
        
        # Add location and access details
        if event.location:
            event_data["properties"]["Location"] = {
                "rich_text": [{"text": {"content": event.location}}]
            }
        
        if event.meeting_url:
            event_data["properties"]["Meeting URL"] = {
                "url": event.meeting_url
            }
        
        if event.meeting_id:
            event_data["properties"]["Meeting ID"] = {
                "rich_text": [{"text": {"content": event.meeting_id}}]
            }
        
        # Add participants
        if event.organizer:
            event_data["properties"]["Organizer"] = {
                "rich_text": [{"text": {"content": event.organizer}}]
            }
        
        if event.attendees:
            event_data["properties"]["Attendees"] = {
                "multi_select": [{"name": attendee} for attendee in event.attendees]
            }
        
        # Add relationships if present
        if event.project_id:
            event_data["properties"]["Project"] = {
                "relation": [{"id": event.project_id}]
            }
        
        if event.area_id:
            event_data["properties"]["Area"] = {
                "relation": [{"id": event.area_id}]
            }
        
        if event.goal_id:
            event_data["properties"]["Goal"] = {
                "relation": [{"id": event.goal_id}]
            }
        
        # Add content blocks for agenda and description
        children = []
        
        if event.description:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"Description: {event.description}"}}]
                }
            })
        
        if event.agenda:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"Agenda: {event.agenda}"}}]
                }
            })
        
        if children:
            event_data["children"] = children
        
        return event_data
    
    def _build_event_update_data(self, event: NotionEvent) -> Dict[str, Any]:
        """
        Build Notion update data structure for event updates
        
        Args:
            event: NotionEvent object with updated data
            
        Returns:
            Dictionary formatted for Notion API
        """
        update_data = {
            "properties": {
                "Title": {
                    "title": [{"text": {"content": event.title}}]
                },
                "Status": {
                    "select": {"name": event.status}
                },
                "Type": {
                    "select": {"name": event.event_type}
                },
                "Priority": {
                    "select": {"name": event.priority}
                },
                "Archive": {
                    "checkbox": event.archive
                }
            }
        }
        
        # Add timing properties
        if event.start_time:
            update_data["properties"]["Start Time"] = {
                "date": {"start": event.start_time.isoformat()}
            }
        
        if event.end_time:
            update_data["properties"]["End Time"] = {
                "date": {"start": event.end_time.isoformat()}
            }
        
        if event.duration_minutes:
            update_data["properties"]["Duration"] = {
                "number": event.duration_minutes
            }
        
        # Add location and access details
        if event.location:
            update_data["properties"]["Location"] = {
                "rich_text": [{"text": {"content": event.location}}]
            }
        
        if event.meeting_url:
            update_data["properties"]["Meeting URL"] = {
                "url": event.meeting_url
            }
        
        if event.organizer:
            update_data["properties"]["Organizer"] = {
                "rich_text": [{"text": {"content": event.organizer}}]
            }
        
        if event.attendees:
            update_data["properties"]["Attendees"] = {
                "multi_select": [{"name": attendee} for attendee in event.attendees]
            }
        
        return update_data
    
    def query_references(self, filter_criteria: Optional[Dict[str, Any]] = None, 
                        limit: int = 100) -> List[NotionReference]:
        """
        Query references from the Notion References database
        
        Args:
            filter_criteria: Notion database filter criteria
            limit: Maximum number of references to return
            
        Returns:
            List of NotionReference objects
        """
        references_db_id = os.getenv('NOTION_REFERENCES_DB')
        if not references_db_id:
            self.logger.error("NOTION_REFERENCES_DB not configured")
            return []
        
        try:
            query_data = {
                "page_size": min(limit, 100)  # Notion API limit
            }
            
            if filter_criteria:
                query_data["filter"] = filter_criteria
            
            response = self.session.post(
                f'{self.base_url}/databases/{references_db_id}/query',
                json=query_data,
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                references = []
                
                for page in data.get('results', []):
                    reference = NotionReference.from_notion_data(page)
                    if reference:
                        references.append(reference)
                
                self.logger.info(f"Retrieved {len(references)} references from Notion", count=len(references))
                return references
            else:
                error_details = self._parse_error_response(response)
                self.logger.error("Failed to query references", error_details=error_details)
                return []
                
        except Exception as e:
            self.logger.error("Error querying references", exception=e)
            return []
    
    def get_reference(self, reference_id: str) -> Optional[NotionReference]:
        """
        Retrieve a reference from Notion
        
        Args:
            reference_id: Notion page ID
            
        Returns:
            NotionReference object if found, None otherwise
        """
        try:
            response = self.session.get(
                f'{self.base_url}/pages/{reference_id}',
                timeout=30
            )
            
            if response.ok:
                page_data = response.json()
                return NotionReference.from_notion_data(page_data)
            else:
                self.logger.warning(f"Reference not found or inaccessible", reference_id=reference_id)
                return None
                
        except Exception as e:
            self.logger.error("Error retrieving reference", exception=e, reference_id=reference_id)
            return None
    
    def create_reference(self, reference: NotionReference) -> Optional[NotionReference]:
        """
        Create a new reference in Notion
        
        Args:
            reference: NotionReference object to create
            
        Returns:
            NotionReference object if successful, None if failed
        """
        references_db_id = os.getenv('NOTION_REFERENCES_DB')
        if not references_db_id:
            self.logger.error("NOTION_REFERENCES_DB not configured")
            return None
        
        self.logger.info("Creating Notion reference", reference_title=reference.title)
        
        try:
            # Create reference data structure
            reference_data = self._build_reference_data(reference, references_db_id)
            
            # Make API request to create page
            response = self.session.post(
                f'{self.base_url}/pages',
                json=reference_data,
                timeout=30
            )
            
            if not response.ok:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Notion API request failed",
                    reference_title=reference.title,
                    status_code=response.status_code,
                    error_details=error_details
                )
                return None
            
            # Parse successful response
            page_data = response.json()
            created_reference = NotionReference.from_notion_data(page_data)
            
            self.logger.success(
                "Notion reference created successfully",
                reference_title=reference.title,
                reference_id=created_reference.reference_id if created_reference else None
            )
            
            return created_reference
            
        except requests.RequestException as e:
            self.logger.error(
                "Network error during Notion API request",
                exception=e,
                reference_title=reference.title
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error during reference creation",
                exception=e,
                reference_title=reference.title
            )
            return None
    
    def update_reference(self, reference: NotionReference) -> bool:
        """
        Update an existing reference in Notion
        
        Args:
            reference: NotionReference object with updated data
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Updating reference", reference_id=reference.reference_id)
        
        try:
            update_data = self._build_reference_update_data(reference)
            
            response = self.session.patch(
                f'{self.base_url}/pages/{reference.reference_id}',
                json=update_data,
                timeout=30
            )
            
            if response.ok:
                self.logger.success(f"Reference updated successfully", reference_id=reference.reference_id)
                return True
            else:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Failed to update reference",
                    reference_id=reference.reference_id,
                    error_details=error_details
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Error updating reference",
                exception=e,
                reference_id=reference.reference_id
            )
            return False
    
    def delete_reference(self, reference_id: str) -> bool:
        """
        Delete (archive) a reference in Notion
        
        Args:
            reference_id: Notion page ID
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Deleting reference", reference_id=reference_id)
        
        try:
            # Archive the page (Notion's way of "deleting")
            archive_data = {
                "archived": True
            }
            
            response = self.session.patch(
                f'{self.base_url}/pages/{reference_id}',
                json=archive_data,
                timeout=30
            )
            
            if response.ok:
                self.logger.success(f"Reference deleted (archived) successfully", reference_id=reference_id)
                return True
            else:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "Failed to delete reference",
                    reference_id=reference_id,
                    error_details=error_details
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Error deleting reference",
                exception=e,
                reference_id=reference_id
            )
            return False
    
    def _build_reference_data(self, reference: NotionReference, database_id: str) -> Dict[str, Any]:
        """
        Build Notion page data structure for reference creation
        
        Args:
            reference: NotionReference object
            database_id: Database ID for references
            
        Returns:
            Dictionary formatted for Notion API
        """
        reference_data = {
            "parent": {"database_id": database_id},
            "properties": {
                "Title": {
                    "title": [{"text": {"content": reference.title}}]
                },
                "Type": {
                    "select": {"name": reference.reference_type}
                },
                "Status": {
                    "select": {"name": reference.status}
                },
                "Priority": {
                    "select": {"name": reference.priority}
                }
            }
        }
        
        # Add URL if present
        if reference.url:
            reference_data["properties"]["URL"] = {
                "url": reference.url
            }
        
        # Add author and source
        if reference.author:
            reference_data["properties"]["Author"] = {
                "rich_text": [{"text": {"content": reference.author}}]
            }
        
        if reference.source:
            reference_data["properties"]["Source"] = {
                "rich_text": [{"text": {"content": reference.source}}]
            }
        
        # Add publication date
        if reference.publication_date:
            reference_data["properties"]["Publication Date"] = {
                "date": {"start": reference.publication_date.isoformat()}
            }
        
        # Add tags and categories
        if reference.tags:
            reference_data["properties"]["Tags"] = {
                "multi_select": [{"name": tag} for tag in reference.tags]
            }
        
        if reference.categories:
            reference_data["properties"]["Categories"] = {
                "multi_select": [{"name": category} for category in reference.categories]
            }
        
        # Add ratings
        if reference.rating:
            reference_data["properties"]["Rating"] = {
                "number": reference.rating
            }
        
        if reference.usefulness:
            reference_data["properties"]["Usefulness"] = {
                "number": reference.usefulness
            }
        
        if reference.reading_time_minutes:
            reference_data["properties"]["Reading Time"] = {
                "number": reference.reading_time_minutes
            }
        
        # Add many-to-many relationships
        if reference.project_ids:
            reference_data["properties"]["Projects"] = {
                "relation": [{"id": project_id} for project_id in reference.project_ids]
            }
        
        if reference.area_ids:
            reference_data["properties"]["Areas"] = {
                "relation": [{"id": area_id} for area_id in reference.area_ids]
            }
        
        if reference.goal_ids:
            reference_data["properties"]["Goals"] = {
                "relation": [{"id": goal_id} for goal_id in reference.goal_ids]
            }
        
        if reference.note_ids:
            reference_data["properties"]["Notes"] = {
                "relation": [{"id": note_id} for note_id in reference.note_ids]
            }
        
        # Add content blocks for description, summary, and insights
        children = []
        
        if reference.description:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"Description: {reference.description}"}}]
                }
            })
        
        if reference.summary:
            children.append({
                "object": "block",
                "type": "paragraph", 
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"Summary: {reference.summary}"}}]
                }
            })
        
        if reference.key_insights:
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "Key Insights:"}}]
                }
            })
            for insight in reference.key_insights:
                children.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": insight}}]
                    }
                })
        
        if reference.key_quotes:
            children.append({
                "object": "block",
                "type": "bulleted_list_item", 
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "Key Quotes:"}}]
                }
            })
            for quote in reference.key_quotes:
                children.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": [{"type": "text", "text": {"content": quote}}]
                    }
                })
        
        if children:
            reference_data["children"] = children
        
        return reference_data
    
    def _build_reference_update_data(self, reference: NotionReference) -> Dict[str, Any]:
        """
        Build Notion update data structure for reference updates
        
        Args:
            reference: NotionReference object with updated data
            
        Returns:
            Dictionary formatted for Notion API
        """
        update_data = {
            "properties": {
                "Title": {
                    "title": [{"text": {"content": reference.title}}]
                },
                "Type": {
                    "select": {"name": reference.reference_type}
                },
                "Status": {
                    "select": {"name": reference.status}
                },
                "Priority": {
                    "select": {"name": reference.priority}
                },
                "Archive": {
                    "checkbox": reference.archive
                }
            }
        }
        
        # Add URL if present
        if reference.url:
            update_data["properties"]["URL"] = {
                "url": reference.url
            }
        
        # Add author and source
        if reference.author:
            update_data["properties"]["Author"] = {
                "rich_text": [{"text": {"content": reference.author}}]
            }
        
        if reference.source:
            update_data["properties"]["Source"] = {
                "rich_text": [{"text": {"content": reference.source}}]
            }
        
        # Add tags and categories
        if reference.tags:
            update_data["properties"]["Tags"] = {
                "multi_select": [{"name": tag} for tag in reference.tags]
            }
        
        if reference.categories:
            update_data["properties"]["Categories"] = {
                "multi_select": [{"name": category} for category in reference.categories]
            }
        
        # Add ratings
        if reference.rating:
            update_data["properties"]["Rating"] = {
                "number": reference.rating
            }
        
        if reference.usefulness:
            update_data["properties"]["Usefulness"] = {
                "number": reference.usefulness
            }
        
        # Add access date
        if reference.accessed_date:
            update_data["properties"]["Last Accessed"] = {
                "date": {"start": reference.accessed_date.isoformat()}
            }
        
        return update_data
    
    def _parse_error_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse error response from Notion API"""
        try:
            error_data = response.json()
            
            return {
                'status': response.status_code,
                'code': error_data.get('code'),
                'message': error_data.get('message'),
                'details': error_data.get('details')
            }
        except:
            return {
                'status': response.status_code,
                'message': response.text
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the Notion API connection and database access
        
        Returns:
            Dictionary with connection test results
        """
        results = {
            'api_connection': False,
            'database_access': False,
            'user_info': None,
            'database_info': None,
            'errors': []
        }
        
        try:
            # Test API connection by getting user info
            response = self.session.get(f'{self.base_url}/users/me', timeout=30)
            if response.ok:
                results['api_connection'] = True
                results['user_info'] = response.json()
                self.logger.success("Notion API connection successful")
            else:
                results['errors'].append(f"API connection failed: {response.status_code}")
                
            # Test database access
            response = self.session.get(f'{self.base_url}/databases/{self.database_id}', timeout=30)
            if response.ok:
                results['database_access'] = True
                results['database_info'] = response.json()
                self.logger.success("Notion database access successful")
            else:
                results['errors'].append(f"Database access failed: {response.status_code}")
                
        except Exception as e:
            results['errors'].append(f"Connection test error: {str(e)}")
            self.logger.error("Notion connection test failed", exception=e)
        
        return results
    
    def get_database_schema(self) -> Dict[str, Any]:
        """
        Get the schema of the Notion database
        
        Returns:
            Dictionary with database schema information
        """
        try:
            response = self.session.get(f'{self.base_url}/databases/{self.database_id}', timeout=30)
            
            if response.ok:
                data = response.json()
                return {
                    'title': data.get('title', [{}])[0].get('text', {}).get('content', 'Unknown'),
                    'properties': data.get('properties', {}),
                    'url': data.get('url'),
                    'created_time': data.get('created_time'),
                    'last_edited_time': data.get('last_edited_time')
                }
            else:
                return {'error': f'Failed to get database schema: {response.status_code}'}
                
        except Exception as e:
            return {'error': f'Error getting database schema: {str(e)}'}
    
    def format_database_url(self) -> str:
        """Get the formatted URL for the Notion database"""
        return f"https://www.notion.so/{self.database_id.replace('-', '')}"