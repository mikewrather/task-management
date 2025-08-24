"""Unit tests for storage adapters"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from voice_task_manager.adapters.base import TaskAdapter, TaskData
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
            project_node_id=123,
            project_name="Test Project",
            area_node_id=456,
            area_name="Work",
            goal_node_id=789,
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
        assert task.project_node_id is None
        assert task.source == "voice"  # Default source
        assert task.created_at is not None



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