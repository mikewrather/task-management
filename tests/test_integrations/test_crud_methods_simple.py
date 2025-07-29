"""Simple working tests for the new CRUD methods added to NotionClient"""

import pytest
import os
from unittest.mock import Mock, patch

from src.voice_task_manager.integrations.notion import NotionClient


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
    """Test successful task deletion (archiving) - newly added method"""
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


def test_delete_project_success(notion_client):
    """Test successful project deletion (archiving) - newly added method"""
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


def test_delete_area_success(notion_client):
    """Test successful area deletion (archiving) - newly added method"""
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
        call_args = mock_patch.call_args
        assert 'area_123' in call_args[0][0]
        assert call_args[1]['json']['archived'] is True


def test_delete_goal_success(notion_client):
    """Test successful goal deletion (archiving) - newly added method"""
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


def test_delete_note_success(notion_client):
    """Test successful note deletion (archiving) - newly added method"""
    mock_response = Mock()
    mock_response.ok = True  
    mock_response.json.return_value = {
        'id': 'note_123',
        'archived': True
    }
    
    with patch.object(notion_client.session, 'patch', return_value=mock_response) as mock_patch:
        result = notion_client.delete_note('note_123')
        
        assert result is True
        mock_patch.assert_called_once()


def test_delete_event_success(notion_client):
    """Test successful event deletion (archiving) - newly added method"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        'id': 'event_123',
        'archived': True
    }
    
    with patch.object(notion_client.session, 'patch', return_value=mock_response) as mock_patch:
        result = notion_client.delete_event('event_123')
        
        assert result is True
        mock_patch.assert_called_once()


def test_delete_reference_success(notion_client):
    """Test successful reference deletion (archiving) - newly added method"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        'id': 'reference_123',
        'archived': True
    }
    
    with patch.object(notion_client.session, 'patch', return_value=mock_response) as mock_patch:
        result = notion_client.delete_reference('reference_123')
        
        assert result is True
        mock_patch.assert_called_once()


def test_query_operations_success(notion_client):
    """Test successful query operations for all entity types - newly extended methods"""
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
        'NOTION_NOTES_DB': 'test_notes_db',
        'NOTION_EVENTS_DB': 'test_events_db',
        'NOTION_REFERENCES_DB': 'test_references_db'
    }):
        with patch.object(notion_client.session, 'post', return_value=mock_response) as mock_post:
            # Test project queries (existing method)
            projects = notion_client.query_projects()
            assert len(projects) == 1
            
            # Test area queries (existing method)
            areas = notion_client.query_areas()
            assert len(areas) == 1
            
            # Test goal queries (newly added method)
            goals = notion_client.query_goals()
            assert len(goals) == 1
            
            # Test note queries (newly added method)
            notes = notion_client.query_notes()
            assert len(notes) == 1
            
            # Test event queries (newly added method)
            events = notion_client.query_events()
            assert len(events) == 1
            
            # Test reference queries (newly added method)
            references = notion_client.query_references()
            assert len(references) == 1
            
            # Verify all queries were made
            assert mock_post.call_count == 6


def test_error_handling_deletion_methods(notion_client):
    """Test error handling for all deletion methods"""
    # Mock authentication error
    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = 401
    mock_response.json.return_value = {
        'object': 'error',
        'status': 401,
        'message': 'Unauthorized'
    }
    
    with patch.object(notion_client.session, 'patch', return_value=mock_response):
        # Test all delete methods return False on error
        assert notion_client.delete_task('task_123') is False
        assert notion_client.delete_project('project_123') is False
        assert notion_client.delete_area('area_123') is False
        assert notion_client.delete_goal('goal_123') is False
        assert notion_client.delete_note('note_123') is False
        assert notion_client.delete_event('event_123') is False
        assert notion_client.delete_reference('reference_123') is False