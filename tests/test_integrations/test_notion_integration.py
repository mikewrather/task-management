"""Integration tests for Notion API interactions"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import requests

from src.voice_task_manager.integrations.notion import NotionIntegration
from src.voice_task_manager.models.task import NotionTask


class TestNotionIntegration:
    """Integration tests for Notion API connectivity and task management"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / 'data').mkdir()
            (temp_path / 'logs').mkdir()
            yield temp_path
    
    @pytest.fixture
    def notion_integration(self, temp_project_root):
        """Create a NotionIntegration instance"""
        return NotionIntegration(temp_project_root)
    
    @pytest.fixture
    def sample_task_data(self):
        """Create sample task data for testing"""
        return {
            'title': 'Test Task from Voice',
            'content': 'This is a test task created from voice recording',
            'contexts': ['voice', 'work'],
            'voice_file_id': 'test_file_123'
        }
    
    @pytest.mark.integration
    @patch.dict(os.environ, {
        'NOTION_TOKEN': 'test_notion_token',
        'NOTION_TASKS_DB': 'test_database_id'
    })
    def test_notion_client_initialization(self, notion_integration):
        """Test Notion client is properly initialized"""
        with patch('requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            client = notion_integration._initialize_notion_client()
            
            assert client is not None
            # Verify headers are set correctly
            expected_headers = {
                'Authorization': 'Bearer test_notion_token',
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
            mock_session_instance.headers.update.assert_called_with(expected_headers)
    
    @pytest.mark.integration
    def test_notion_client_missing_credentials(self, notion_integration):
        """Test Notion client initialization without credentials"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Notion token not found"):
                notion_integration._initialize_notion_client()
    
    @pytest.mark.integration
    @patch('requests.Session')
    def test_create_task_success(self, mock_session, notion_integration, sample_task_data):
        """Test successful task creation in Notion"""
        # Mock successful API response
        mock_session_instance = Mock()
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'id': 'task_123',
            'url': 'https://notion.so/task-123',
            'properties': {
                'Title': {'title': [{'text': {'content': 'Test Task from Voice'}}]},
                'Status': {'select': {'name': 'Inbox'}}
            }
        }
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        result = notion_integration.create_task(sample_task_data)
        
        assert result['success'] is True
        assert result['task_id'] == 'task_123'
        assert result['task_url'] == 'https://notion.so/task-123'
        
        # Verify API was called correctly
        mock_session_instance.post.assert_called_once()
        call_args = mock_session_instance.post.call_args
        assert '/pages' in call_args[0][0]
        
        # Verify request payload
        payload = json.loads(call_args[1]['data'])
        assert payload['parent']['database_id'] == 'test_database_id'
        assert 'Test Task from Voice' in str(payload['properties'])
    
    @pytest.mark.integration
    @patch('requests.Session')
    def test_create_task_api_error(self, mock_session, notion_integration, sample_task_data):
        """Test task creation with Notion API error"""
        # Mock API error response
        mock_session_instance = Mock()
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'object': 'error',
            'status': 400,
            'message': 'Invalid request - missing required property'
        }
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        result = notion_integration.create_task(sample_task_data)
        
        assert result['success'] is False
        assert 'Invalid request' in result['error']
        assert result['status_code'] == 400
    
    @pytest.mark.integration
    @patch('requests.Session')
    def test_update_task_success(self, mock_session, notion_integration):
        """Test successful task update in Notion"""
        # Mock successful update response
        mock_session_instance = Mock()
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'id': 'task_123',
            'properties': {
                'Status': {'select': {'name': 'In Progress'}}
            }
        }
        mock_session_instance.patch.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        update_data = {'status': 'In Progress'}
        result = notion_integration.update_task('task_123', update_data)
        
        assert result['success'] is True
        
        # Verify PATCH request was made
        mock_session_instance.patch.assert_called_once()
        call_args = mock_session_instance.patch.call_args
        assert 'task_123' in call_args[0][0]
    
    @pytest.mark.integration
    @patch('requests.Session')
    def test_get_task_success(self, mock_session, notion_integration):
        """Test successful task retrieval from Notion"""
        # Mock successful get response
        mock_session_instance = Mock()
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'id': 'task_123',
            'url': 'https://notion.so/task-123',
            'properties': {
                'Title': {'title': [{'text': {'content': 'Test Task'}}]},
                'Status': {'select': {'name': 'Inbox'}},
                'Contexts': {'multi_select': [{'name': 'voice'}, {'name': 'work'}]}
            }
        }
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        result = notion_integration.get_task('task_123')
        
        assert result['success'] is True
        assert result['task']['id'] == 'task_123'
        assert result['task']['title'] == 'Test Task'
        assert result['task']['status'] == 'Inbox'
    
    @pytest.mark.integration
    @patch('requests.Session')
    def test_query_database_success(self, mock_session, notion_integration):
        """Test successful database query"""
        # Mock successful query response
        mock_session_instance = Mock()
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 'task_1',
                    'properties': {
                        'Title': {'title': [{'text': {'content': 'Task 1'}}]},
                        'Status': {'select': {'name': 'Inbox'}}
                    }
                },
                {
                    'id': 'task_2', 
                    'properties': {
                        'Title': {'title': [{'text': {'content': 'Task 2'}}]},
                        'Status': {'select': {'name': 'Done'}}
                    }
                }
            ],
            'has_more': False
        }
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        query_filter = {
            'property': 'Contexts',
            'multi_select': {'contains': 'voice'}
        }
        
        result = notion_integration.query_database(query_filter)
        
        assert result['success'] is True
        assert len(result['tasks']) == 2
        assert result['tasks'][0]['id'] == 'task_1'
        assert result['tasks'][1]['id'] == 'task_2'
    
    @pytest.mark.integration
    @patch('requests.Session')
    def test_database_connectivity_check(self, mock_session, notion_integration):
        """Test database connectivity check"""
        # Mock successful database info response
        mock_session_instance = Mock()
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'object': 'database',
            'id': 'test_database_id',
            'title': [{'text': {'content': 'Voice Tasks'}}],
            'properties': {
                'Title': {'title': {}},
                'Status': {'select': {}},
                'Contexts': {'multi_select': {}}
            }
        }
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        result = notion_integration.check_database_connectivity()
        
        assert result['success'] is True
        assert result['database_id'] == 'test_database_id'
        assert 'Title' in result['properties']
        assert 'Status' in result['properties']
    
    @pytest.mark.integration
    @patch('requests.Session')
    def test_database_connectivity_invalid_database(self, mock_session, notion_integration):
        """Test connectivity check with invalid database"""  
        # Mock error response for invalid database
        mock_session_instance = Mock()
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.json.return_value = {
            'object': 'error',
            'status': 404,
            'message': 'Could not find database with ID'
        }
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        result = notion_integration.check_database_connectivity()
        
        assert result['success'] is False
        assert result['status_code'] == 404
        assert 'Could not find database' in result['error']
    
    @pytest.mark.integration
    @patch('requests.Session')
    def test_rate_limit_handling(self, mock_session, notion_integration, sample_task_data):
        """Test API rate limit handling with retry logic"""
        mock_session_instance = Mock()
        
        # First call returns rate limit error, second succeeds
        rate_limit_response = Mock()
        rate_limit_response.ok = False
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {'Retry-After': '1'}
        
        success_response = Mock()
        success_response.ok = True
        success_response.json.return_value = {
            'id': 'task_123',
            'url': 'https://notion.so/task-123'
        }
        
        mock_session_instance.post.side_effect = [rate_limit_response, success_response]
        mock_session.return_value = mock_session_instance
        
        with patch('time.sleep') as mock_sleep:
            result = notion_integration.create_task(sample_task_data, max_retries=2)
            
            assert result['success'] is True
            assert result['task_id'] == 'task_123'
            assert mock_session_instance.post.call_count == 2
            mock_sleep.assert_called_once_with(1)
    
    @pytest.mark.integration
    @patch('requests.Session')
    def test_authentication_error_handling(self, mock_session, notion_integration, sample_task_data):
        """Test authentication error handling"""
        # Mock authentication error
        mock_session_instance = Mock()
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.json.return_value = {
            'object': 'error',
            'status': 401,
            'message': 'Unauthorized'
        }
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        result = notion_integration.create_task(sample_task_data)
        
        assert result['success'] is False
        assert result['status_code'] == 401
        assert 'Unauthorized' in result['error']
    
    @pytest.mark.integration
    @patch('requests.Session')
    def test_create_task_with_rich_content(self, mock_session, notion_integration):
        """Test creating task with rich content formatting"""
        # Mock successful response
        mock_session_instance = Mock()
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'id': 'rich_task_123',
            'url': 'https://notion.so/rich-task-123'
        }
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        rich_task_data = {
            'title': 'Task with Rich Content',
            'content': 'This task has **bold text** and [links](https://example.com)',
            'contexts': ['voice', 'urgent'],
            'priority': 'High',
            'due_date': '2025-01-30'
        }
        
        result = notion_integration.create_task(rich_task_data)
        
        assert result['success'] is True
        
        # Verify rich content was properly formatted in request
        call_args = mock_session_instance.post.call_args
        payload = json.loads(call_args[1]['data'])
        
        # Check that rich text formatting is preserved
        assert 'properties' in payload
        assert 'children' in payload or 'content' in str(payload)
    
    @pytest.mark.integration
    @patch('requests.Session')
    def test_bulk_task_operations(self, mock_session, notion_integration):
        """Test bulk task creation and updates"""
        mock_session_instance = Mock()
        
        # Mock successful responses for bulk operations
        create_responses = []
        for i in range(3):
            response = Mock()
            response.ok = True
            response.json.return_value = {
                'id': f'bulk_task_{i}',
                'url': f'https://notion.so/bulk-task-{i}'
            }
            create_responses.append(response)
        
        mock_session_instance.post.side_effect = create_responses
        mock_session.return_value = mock_session_instance
        
        bulk_tasks = [
            {'title': f'Bulk Task {i}', 'content': f'Content {i}'}
            for i in range(3)
        ]
        
        results = notion_integration.create_tasks_batch(bulk_tasks)
        
        assert len(results) == 3
        assert all(result['success'] for result in results)
        assert mock_session_instance.post.call_count == 3
    
    @pytest.mark.integration
    @patch('requests.Session')
    def test_task_search_functionality(self, mock_session, notion_integration):
        """Test task search by various criteria"""
        # Mock search response
        mock_session_instance = Mock()
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 'search_task_1',
                    'properties': {
                        'Title': {'title': [{'text': {'content': 'Voice Task 1'}}]},
                        'Contexts': {'multi_select': [{'name': 'voice'}]}
                    }
                }
            ]
        }
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        search_criteria = {
            'query': 'voice task',
            'filter': {
                'property': 'Contexts',
                'multi_select': {'contains': 'voice'}
            }
        }
        
        result = notion_integration.search_tasks(search_criteria)
        
        assert result['success'] is True
        assert len(result['tasks']) == 1
        assert 'Voice Task 1' in result['tasks'][0]['title']
    
    @pytest.mark.integration
    def test_integration_with_voice_processor(self, notion_integration):
        """Test integration between Notion and voice processor"""
        from src.voice_task_manager.core.processor import VoiceProcessor
        
        with patch.object(notion_integration, 'create_task') as mock_create:
            mock_create.return_value = {
                'success': True,
                'task_id': 'integration_task_123',
                'task_url': 'https://notion.so/integration-task-123'
            }
            
            processor = VoiceProcessor(notion_integration.project_root)
            processor.notion_integration = notion_integration
            
            transcript = "Create a new task for testing integration"
            result = processor._create_notion_task(transcript, 'test_file_123')
            
            assert result['success'] is True
            assert result['task_id'] == 'integration_task_123'
            mock_create.assert_called_once()
    
    @pytest.mark.integration
    @patch('requests.Session')
    def test_webhook_validation(self, mock_session, notion_integration):
        """Test webhook signature validation for Notion events"""
        import hmac
        import hashlib
        
        # Mock webhook payload
        webhook_payload = {
            'object': 'event',
            'id': 'event_123',
            'type': 'page.property_changed',
            'page': {'id': 'task_123'}
        }
        
        # Create test signature
        secret = 'webhook_secret'
        payload_str = json.dumps(webhook_payload)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        result = notion_integration.validate_webhook(
            payload_str,
            signature,
            secret
        )
        
        assert result is True
    
    @pytest.mark.integration
    @patch('requests.Session')
    def test_database_schema_validation(self, mock_session, notion_integration):
        """Test validation of database schema requirements"""
        # Mock database schema response
        mock_session_instance = Mock()
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'properties': {
                'Title': {'title': {}},
                'Status': {'select': {}},
                'Contexts': {'multi_select': {}},
                'Voice_File_ID': {'rich_text': {}},
                'Created': {'created_time': {}}
            }
        }
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        result = notion_integration.validate_database_schema()
        
        assert result['valid'] is True
        assert result['required_properties_present'] is True
        
        # Test with missing required properties
        mock_response.json.return_value = {
            'properties': {
                'Title': {'title': {}},
                # Missing Status and Contexts
            }
        }
        
        result = notion_integration.validate_database_schema()
        
        assert result['valid'] is False
        assert len(result['missing_properties']) > 0