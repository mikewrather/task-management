"""Tests for the new CRUD methods added to NotionClient"""

import pytest
import os
from unittest.mock import Mock, patch
from datetime import datetime, date

from src.voice_task_manager.integrations.notion import NotionClient
from src.voice_task_manager.models.notion_project import NotionProject, ProjectStatus, DateRange
from src.voice_task_manager.models.notion_area import NotionArea, AreaStatus  
from src.voice_task_manager.models.notion_goal import NotionGoal, GoalStatus, GoalType


@pytest.fixture
def notion_client():
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


def test_delete_task_success(notion_client):
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
        assert call_args[1]['json']['archived'] is True


def test_create_project_success(notion_client):
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
            project_id='',  # Will be filled by API
            name='Test Project',
            status=ProjectStatus.IN_PROGRESS.value,
            notes='A test project for validation',
            timeline=DateRange(
                start=datetime(2025, 1, 1),
                end=datetime(2025, 12, 31)
            )
        )
        
        result = notion_client.create_project(project)
        
        assert result is not None
        assert result.name == 'Test Project'
        assert result.status == ProjectStatus.IN_PROGRESS.value
        mock_post.assert_called_once()


def test_delete_project_success(notion_client):
    """Test successful project deletion (archiving)"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        'id': 'project_123',
        'archived': True
    }
    
    with patch.object(notion_client.session, 'patch', return_value=mock_response) as mock_patch:
        result = notion_client.delete_project('project_123')
        
        assert result is True
        mock_patch.assert_called_once()
        call_args = mock_patch.call_args
        assert 'project_123' in call_args[0][0]
        assert call_args[1]['json']['archived'] is True


def test_create_area_success(notion_client):
    """Test successful area creation"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        'id': 'area_123',
        'url': 'https://notion.so/area-123',
        'properties': {
            'Name': {'title': [{'text': {'content': 'Health & Fitness'}}]},
            'Status': {'select': {'name': 'Active'}}
        }
    }
    
    with patch.object(notion_client.session, 'post', return_value=mock_response) as mock_post:
        area = NotionArea(
            area_id='',  # Will be filled by API
            name='Health & Fitness',
            status=AreaStatus.IN_PROGRESS.value,
            notes='Maintaining physical and mental wellness'
        )
        
        result = notion_client.create_area(area)
        
        assert result is not None
        assert result.name == 'Health & Fitness'
        assert result.status == AreaStatus.IN_PROGRESS.value
        mock_post.assert_called_once()


def test_delete_area_success(notion_client):
    """Test successful area deletion (archiving)"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        'id': 'area_123',
        'archived': True
    }
    
    with patch.object(notion_client.session, 'patch', return_value=mock_response) as mock_patch:
        result = notion_client.delete_area('area_123')
        
        assert result is True
        mock_patch.assert_called_once()


def test_create_goal_success(notion_client):
    """Test successful goal creation"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        'id': 'goal_123',
        'url': 'https://notion.so/goal-123',
        'properties': {
            'Name': {'title': [{'text': {'content': 'Read 50 Books'}}]},
            'Type': {'select': {'name': 'Personal'}},
            'Status': {'select': {'name': 'Active'}}
        }
    }
    
    with patch.object(notion_client.session, 'post', return_value=mock_response) as mock_post:
        goal = NotionGoal(
            goal_id='',  # Will be filled by API
            name='Read 50 Books',
            description='Read 50 books by end of year',
            goal_type=GoalType.PERSONAL.value,
            status=GoalStatus.IN_PROGRESS.value,
            target_date=date(2025, 12, 31),
            progress=10
        )
        
        result = notion_client.create_goal(goal)
        
        assert result is not None
        assert result.name == 'Read 50 Books'
        assert result.goal_type == GoalType.PERSONAL.value
        mock_post.assert_called_once()


def test_delete_goal_success(notion_client):
    """Test successful goal deletion"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        'id': 'goal_123', 
        'archived': True
    }
    
    with patch.object(notion_client.session, 'patch', return_value=mock_response) as mock_patch:
        result = notion_client.delete_goal('goal_123')
        
        assert result is True
        mock_patch.assert_called_once()


def test_query_operations_success(notion_client):
    """Test successful query operations for all entity types"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        'results': [
            {
                'id': 'item_1',
                'properties': {
                    'Name': {'title': [{'text': {'content': 'Test Item'}}]},
                    'Status': {'select': {'name': 'Active'}}
                }
            }
        ],
        'has_more': False
    }
    
    # Ensure environment variables are set during test execution
    with patch.dict(os.environ, {
        'NOTION_PROJECTS_DB': 'test_projects_db',
        'NOTION_AREAS_DB': 'test_areas_db',
        'NOTION_GOALS_DB': 'test_goals_db',
    }):
        with patch.object(notion_client.session, 'post', return_value=mock_response) as mock_post:
            # Test project queries
            projects = notion_client.query_projects()
            assert len(projects) == 1
            
            # Test area queries
            areas = notion_client.query_areas()
            assert len(areas) == 1
            
            # Test goal queries  
            goals = notion_client.query_goals()
            assert len(goals) == 1
            
            # Verify queries were made
            assert mock_post.call_count == 3


def test_error_handling_across_entities(notion_client):
    """Test consistent error handling for all entity types"""
    # Mock authentication error
    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = 401
    mock_response.json.return_value = {
        'object': 'error',
        'status': 401,
        'message': 'Unauthorized'
    }
    
    with patch.object(notion_client.session, 'post', return_value=mock_response):
        # Test project creation error
        project = NotionProject(project_id='', name='Test Project', status=ProjectStatus.IN_PROGRESS.value)
        result = notion_client.create_project(project)
        assert result is None
        
        # Test area creation error
        area = NotionArea(area_id='', name='Test Area', status=AreaStatus.IN_PROGRESS.value)
        result = notion_client.create_area(area)
        assert result is None
        
        # Test goal creation error
        goal = NotionGoal(goal_id='', name='Test Goal', goal_type=GoalType.PERSONAL.value, status=GoalStatus.IN_PROGRESS.value)
        result = notion_client.create_goal(goal)
        assert result is None