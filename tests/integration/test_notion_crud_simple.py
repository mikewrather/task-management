"""Simple working tests for Notion CRUD operations"""

import pytest
import os
from unittest.mock import Mock, patch
from datetime import datetime, date

from voice_task_manager.integrations.notion import NotionClient
from voice_task_manager.models.notion_project import NotionProject, ProjectStatus
from voice_task_manager.models.notion_area import NotionArea, AreaStatus  
from voice_task_manager.models.notion_goal import NotionGoal, GoalStatus, GoalType


class TestNotionCrudOperations:
    """Test comprehensive CRUD operations for all entity types"""
    
    @pytest.fixture
    def notion_client(self):
        """Create a NotionClient instance with mocked environment"""
        with patch.dict(os.environ, {
            'NOTION_TOKEN': 'test_notion_token',
            'NOTION_TASKS_DB': 'test_tasks_db',
            'NOTION_PROJECTS_DB': 'test_projects_db',
            'NOTION_AREAS_DB': 'test_areas_db',
            'NOTION_GOALS_DB': 'test_goals_db',
            'NOTION_NOTES_DB': 'test_notes_db',
            'NOTION_EVENTS_DB': 'test_events_db',
            'NOTION_REFERENCES_DB': 'test_references_db'
        }):
            return NotionClient()

    def test_delete_task_success(self, notion_client):
        """Test successful task deletion (archiving)"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'id': 'task_123',
            'archived': True
        }
        
        with patch.object(notion_client.session, 'patch', return_value=mock_response) as mock_patch:
            result = notion_client.delete_task('task_123')
            
            assert result is True
            mock_patch.assert_called_once()
            call_args = mock_patch.call_args
            assert 'task_123' in call_args[0][0]
            
            # Verify archive payload
            assert call_args[1]['json']['archived'] is True

    def test_create_project_success(self, notion_client):
        """Test successful project creation"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'id': 'project_123',
            'url': 'https://notion.so/project-123',
            'properties': {
                'Name': {'title': [{'text': {'content': 'Test Project'}}]},
                'Status': {'select': {'name': 'Active'}}
            }
        }
        
        with patch.object(notion_client.session, 'post', return_value=mock_response) as mock_post:
            project = NotionProject(
                name='Test Project',
                description='A test project for validation',
                status=ProjectStatus.ACTIVE,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 12, 31)
            )
            
            result = notion_client.create_project(project)
            
            assert result is not None
            assert result.name == 'Test Project'
            assert result.status == ProjectStatus.ACTIVE
            mock_post.assert_called_once()