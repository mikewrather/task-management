"""Unit tests for storage adapters"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from voice_task_manager.adapters.base import TaskAdapter, TaskData
from voice_task_manager.adapters.notion import NotionTaskAdapter
from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter


class TestTaskData:
    """Test TaskData model"""
    
    def test_task_data_creation(self):
        """Test creating TaskData with all fields"""
        task = TaskData(
            name="Test Task",
            description="Test Description",
            status="Inbox",
            priority="High",
            contexts=["@home", "@computer"],
            project_id="proj123",
            project_name="Test Project",
            area_id="area456",
            area_name="Work",
            goal_id="goal789",
            goal_name="Q4 Goals",
            source="voice",
            metadata={"voice_file_id": "file123"}
        )
        
        assert task.name == "Test Task"
        assert task.status == "Inbox"
        assert task.priority == "High"
        assert "@home" in task.contexts
        assert task.project_name == "Test Project"
        assert task.metadata["voice_file_id"] == "file123"
    
    def test_task_data_defaults(self):
        """Test TaskData with default values"""
        task = TaskData(name="Minimal Task")
        
        assert task.name == "Minimal Task"
        assert task.description is None
        assert task.status == "Inbox"
        assert task.priority == "Medium"
        assert task.contexts == ['voice', 'auto-processed']  # Default contexts
        assert task.project_id is None
        assert task.source == "voice"  # Default source
        assert task.created_at is not None


class TestNotionTaskAdapter:
    """Test Notion task adapter"""
    
    @pytest.fixture
    def mock_notion(self):
        """Mock Notion integration"""
        with patch('voice_task_manager.adapters.notion.NotionClient') as mock:
            yield mock
    
    @pytest.fixture
    def adapter(self, mock_notion):
        """Create adapter with mocked Notion"""
        return NotionTaskAdapter()
    
    def test_create_task_success(self, adapter, mock_notion):
        """Test successful task creation"""
        # Setup
        task_data = TaskData(
            name="Test Task",
            description="Test Description",
            contexts=["@home"]
        )
        mock_notion.return_value.create_task.return_value = "task123"
        
        # Execute
        result = adapter.create_task(task_data)
        
        # Verify
        assert result == "task123"
        mock_notion.return_value.create_task.assert_called_once()
    
    def test_create_task_with_relationships(self, adapter, mock_notion):
        """Test task creation with project and area"""
        # Setup
        task_data = TaskData(
            name="Test Task",
            project_id="proj123",
            area_id="area456"
        )
        mock_notion.return_value.create_task.return_value = "task123"
        
        # Execute
        result = adapter.create_task(task_data)
        
        # Verify
        assert result == "task123"
        # Check that relationships were included in the call
        call_args = mock_notion.return_value.create_task.call_args[1]
        assert call_args.get("project_id") == "proj123"
        assert call_args.get("area_id") == "area456"


class TestGraphRAGTaskAdapter:
    """Test GraphRAG task adapter"""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked logger"""
        with patch('voice_task_manager.adapters.graphrag.VoiceLogger'):
            return GraphRAGTaskAdapter()
    
    def test_execute_mcp_command_mock_mode(self, adapter):
        """Test MCP command execution in mock mode"""
        # Setup
        adapter.use_real_mcp = False
        
        # Execute
        result = adapter._execute_mcp_command("create_entity", {
            "entity_type": "TASK",
            "properties": {"name": "Test"}
        })
        
        # Verify
        assert result["success"] is True
        assert "entity" in result
        assert result["entity"]["type"] == "TASK"
    
    @patch('subprocess.run')
    def test_execute_mcp_command_real_mode(self, mock_run, adapter):
        """Test MCP command execution in real mode"""
        # Setup
        adapter.use_real_mcp = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"result": "{\\"success\\": true, \\"entity\\": {\\"id\\": \\"123\\"}}"}'
        )
        
        # Execute
        result = adapter._execute_mcp_command("create_entity", {
            "entity_type": "TASK"
        })
        
        # Verify
        assert result["success"] is True
        assert result["entity"]["id"] == "123"
    
    def test_test_connection(self, adapter):
        """Test connection testing"""
        # Setup
        adapter._execute_mcp_command = Mock(return_value={
            "components": {"neo4j": "healthy"}
        })
        
        # Execute
        result = adapter.test_connection()
        
        # Verify
        assert result is True
        adapter._execute_mcp_command.assert_called_with("get_health_status", {})