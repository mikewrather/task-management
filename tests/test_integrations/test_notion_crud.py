"""Comprehensive tests for CRUD operations on all Notion entity types"""

import pytest
import os
import json
from unittest.mock import Mock, patch
from datetime import datetime, date

from src.voice_task_manager.integrations.notion import NotionClient
from src.voice_task_manager.models.notion_project import NotionProject, ProjectStatus
from src.voice_task_manager.models.notion_area import NotionArea, AreaStatus  
from src.voice_task_manager.models.notion_goal import NotionGoal, GoalStatus, GoalType
from src.voice_task_manager.models.notion_note import NotionNote, NoteStatus, NoteType
from src.voice_task_manager.models.notion_event import NotionEvent, EventStatus, EventType
from src.voice_task_manager.models.notion_reference import NotionReference, ReferenceType, ReferenceStatus


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

    # Test Task deletion (newly added functionality)
    def test_delete_task_success(self, notion_client):
        """Test successful task deletion (archiving)"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'id': 'task_123',
            'archived': True
        }
        
        # Mock the session's patch method
        with patch.object(notion_client.session, 'patch', return_value=mock_response) as mock_patch:
            result = notion_client.delete_task('task_123')
            
            assert result is True
            mock_patch.assert_called_once()
            call_args = mock_patch.call_args
            assert 'task_123' in call_args[0][0]
            
            # Verify archive payload
            assert call_args[1]['json']['archived'] is True

    # Test Project CRUD operations
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
        mock_post.return_value = mock_response
        
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

    @patch('requests.patch')
    def test_update_project_success(self, mock_patch, notion_client):
        """Test successful project update"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'id': 'project_123',
            'properties': {
                'Name': {'title': [{'text': {'content': 'Updated Project'}}]},
                'Status': {'select': {'name': 'On Hold'}}
            }
        }
        mock_patch.return_value = mock_response
        
        project = NotionProject(
            notion_id='project_123',
            name='Updated Project',
            status=ProjectStatus.ON_HOLD
        )
        
        result = notion_client.update_project(project)
        
        assert result is True
        mock_patch.assert_called_once()

    @patch('requests.patch')
    def test_delete_project_success(self, mock_patch, notion_client):
        """Test successful project deletion (archiving)"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'id': 'project_123',
            'archived': True
        }
        mock_patch.return_value = mock_response
        
        result = notion_client.delete_project('project_123')
        
        assert result is True
        mock_patch.assert_called_once()

    # Test Area CRUD operations
    @patch('requests.post')
    def test_create_area_success(self, mock_post, notion_client):
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
        mock_post.return_value = mock_response
        
        area = NotionArea(
            name='Health & Fitness',
            description='Maintaining physical and mental wellness',
            status=AreaStatus.ACTIVE
        )
        
        result = notion_client.create_area(area)
        
        assert result is not None
        assert result.name == 'Health & Fitness'
        assert result.status == AreaStatus.ACTIVE
        mock_post.assert_called_once()

    # Test Goal CRUD operations  
    @patch('requests.post')
    def test_create_goal_success(self, mock_post, notion_client):
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
        mock_post.return_value = mock_response
        
        goal = NotionGoal(
            name='Read 50 Books',
            description='Read 50 books by end of year',
            goal_type=GoalType.PERSONAL,
            status=GoalStatus.ACTIVE,
            target_date=date(2025, 12, 31),
            progress=10
        )
        
        result = notion_client.create_goal(goal)
        
        assert result is not None
        assert result.name == 'Read 50 Books'
        assert result.goal_type == GoalType.PERSONAL
        mock_post.assert_called_once()

    @patch('requests.patch')
    def test_delete_goal_success(self, mock_patch, notion_client):
        """Test successful goal deletion"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'id': 'goal_123',
            'archived': True
        }
        mock_patch.return_value = mock_response
        
        result = notion_client.delete_goal('goal_123')
        
        assert result is True
        mock_patch.assert_called_once()

    # Test Note CRUD operations
    @patch('requests.post')
    def test_create_note_success(self, mock_post, notion_client):
        """Test successful note creation"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'id': 'note_123',
            'url': 'https://notion.so/note-123',
            'properties': {
                'Title': {'title': [{'text': {'content': 'Meeting Notes'}}]},
                'Type': {'select': {'name': 'Meeting'}},
                'Status': {'select': {'name': 'Published'}}
            }
        }
        mock_post.return_value = mock_response
        
        note = NotionNote(
            title='Meeting Notes',
            content='Notes from the weekly team meeting',
            note_type=NoteType.MEETING,
            status=NoteStatus.PUBLISHED,
            tags=['meeting', 'team']
        )
        
        result = notion_client.create_note(note)
        
        assert result is not None
        assert result.title == 'Meeting Notes'
        assert result.note_type == NoteType.MEETING
        mock_post.assert_called_once()

    # Test Event CRUD operations
    @patch('requests.post')
    def test_create_event_success(self, mock_post, notion_client):
        """Test successful event creation"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'id': 'event_123',
            'url': 'https://notion.so/event-123',
            'properties': {
                'Title': {'title': [{'text': {'content': 'Team Standup'}}]},
                'Type': {'select': {'name': 'Meeting'}},
                'Status': {'select': {'name': 'Scheduled'}}
            }
        }
        mock_post.return_value = mock_response
        
        event = NotionEvent(
            title='Team Standup',
            description='Daily team standup meeting',
            event_type=EventType.MEETING,
            status=EventStatus.SCHEDULED,
            start_date=datetime(2025, 1, 29, 9, 0),
            end_date=datetime(2025, 1, 29, 9, 30)
        )
        
        result = notion_client.create_event(event)
        
        assert result is not None
        assert result.title == 'Team Standup'
        assert result.event_type == EventType.MEETING
        mock_post.assert_called_once()

    @patch('requests.patch')
    def test_delete_event_success(self, mock_patch, notion_client):
        """Test successful event deletion"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'id': 'event_123',
            'archived': True
        }
        mock_patch.return_value = mock_response
        
        result = notion_client.delete_event('event_123')
        
        assert result is True
        mock_patch.assert_called_once()

    # Test Reference CRUD operations
    @patch('requests.post')
    def test_create_reference_success(self, mock_post, notion_client):
        """Test successful reference creation"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'id': 'reference_123',
            'url': 'https://notion.so/reference-123',
            'properties': {
                'Title': {'title': [{'text': {'content': 'Important Article'}}]},
                'Type': {'select': {'name': 'Article'}},
                'Status': {'select': {'name': 'Active'}}
            }
        }
        mock_post.return_value = mock_response
        
        reference = NotionReference(
            title='Important Article',
            url='https://example.com/article',
            reference_type=ReferenceType.ARTICLE,
            status=ReferenceStatus.ACTIVE,
            rating=5,
            key_insights='Great insights on productivity',
            projects=['project_1'],
            areas=['area_1']
        )
        
        result = notion_client.create_reference(reference)
        
        assert result is not None
        assert result.title == 'Important Article'
        assert result.reference_type == ReferenceType.ARTICLE
        mock_post.assert_called_once()

    # Test error handling across all entities
    @patch('requests.post')
    def test_error_handling_across_entities(self, mock_post, notion_client):
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
        mock_post.return_value = mock_response
        
        # Test project creation error
        project = NotionProject(name='Test Project', status=ProjectStatus.ACTIVE)
        result = notion_client.create_project(project)
        assert result is None
        
        # Test area creation error
        area = NotionArea(name='Test Area', status=AreaStatus.ACTIVE)
        result = notion_client.create_area(area)
        assert result is None
        
        # Test goal creation error
        goal = NotionGoal(name='Test Goal', goal_type=GoalType.PERSONAL, status=GoalStatus.ACTIVE)
        result = notion_client.create_goal(goal)
        assert result is None

    # Test query operations
    @patch('requests.post')
    def test_query_operations_success(self, mock_post, notion_client):
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
        mock_post.return_value = mock_response
        
        # Test project queries
        projects = notion_client.query_projects()
        assert len(projects) == 1
        
        # Test area queries
        areas = notion_client.query_areas()
        assert len(areas) == 1
        
        # Test goal queries  
        goals = notion_client.query_goals()
        assert len(goals) == 1
        
        # Test note queries
        notes = notion_client.query_notes()
        assert len(notes) == 1
        
        # Test event queries
        events = notion_client.query_events()
        assert len(events) == 1
        
        # Test reference queries
        references = notion_client.query_references()
        assert len(references) == 1
        
        # Verify all queries were made
        assert mock_post.call_count == 6