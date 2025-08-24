"""
Unit tests for TaskManager entity manager.
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime

from voice_task_manager.entities.task_manager import TaskManager
from voice_task_manager.adapters.base import TaskData


class TestTaskManager(unittest.TestCase):
    """Test TaskManager validation and creation logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_adapter = Mock()
        self.mock_logger = Mock()
        self.mock_adapter.logger = self.mock_logger
        self.task_manager = TaskManager(self.mock_adapter)
    
    def test_validate_minimal_task(self):
        """Test validation with minimal required fields."""
        entity_data = {
            "id": "task_123",
            "name": "Test Task",
            "description": "Test description"
        }
        
        is_valid, error = self.task_manager.validate_entity(entity_data)
        
        self.assertTrue(is_valid)
        self.assertEqual(error, "Valid")
    
    def test_validate_missing_required_fields(self):
        """Test validation failure with missing required fields."""
        entity_data = {
            "id": "task_123"
            # Missing name and description
        }
        
        is_valid, error = self.task_manager.validate_entity(entity_data)
        
        self.assertFalse(is_valid)
        self.assertIn("Missing required fields", error)
        self.assertIn("name", error)
        self.assertIn("description", error)
    
    def test_validate_full_task(self):
        """Test validation with all fields."""
        entity_data = {
            "id": "task_123",
            "name": "Test Task",
            "description": "Test description",
            "status": "pending",
            "priority": "high",
            "contexts": ["work", "urgent"],
            "created": "2025-01-01T00:00:00",
            "source": "voice"
        }
        
        is_valid, error = self.task_manager.validate_entity(entity_data)
        
        self.assertTrue(is_valid)
        self.assertEqual(error, "Valid")
    
    def test_create_task_success(self):
        """Test successful task creation."""
        # Mock successful MCP response
        self.mock_adapter._execute_mcp_command.return_value = {
            "success": True,
            "results": [{"entity_id": "task_created_123"}],
            "embeddings_created": 1
        }
        
        task_data = TaskData(
            name="Test Task",
            description="Test description",
            status="pending",
            created_at=datetime.now(),
            source="test"
        )
        
        task_id = self.task_manager.create(task_data)
        
        self.assertIsNotNone(task_id)
        self.assertEqual(task_id, "task_created_123")
        
        # Verify MCP was called with correct parameters
        self.mock_adapter._execute_mcp_command.assert_called_once()
        call_args = self.mock_adapter._execute_mcp_command.call_args
        self.assertEqual(call_args[0][0], "create_entities")
        
        # Check entities parameter is array format
        params = call_args[0][1]
        self.assertEqual(params["entity_type"], "TASK_MANAGEMENT:TASK_MANAGEMENT:TASK")
        self.assertIsInstance(params["entities"], list)
        self.assertEqual(len(params["entities"]), 1)
        self.assertTrue(params["check_duplicates"])
    
    def test_create_task_validation_failure(self):
        """Test handling of validation errors."""
        # Mock validation error response
        self.mock_adapter._execute_mcp_command.return_value = {
            "success": False,
            "error": "validation error: required field 'name' is missing"
        }
        
        task_data = TaskData(
            name="",  # Empty name should cause validation error
            description="Test description",
            created_at=datetime.now(),
            source="test"
        )
        
        task_id = self.task_manager.create(task_data)
        
        self.assertIsNone(task_id)
        
        # Verify error was logged
        self.mock_logger.error.assert_called()
    
    def test_add_default_required_fields(self):
        """Test adding default values for missing required fields."""
        entity_data = {"id": "task_123"}
        
        updated_data = self.task_manager._add_default_required_fields(entity_data)
        
        self.assertIn("name", updated_data)
        self.assertIn("description", updated_data)
        self.assertEqual(updated_data["id"], "task_123")
    
    def test_fix_field_formats(self):
        """Test fixing common field format issues."""
        entity_data = {
            "id": "task_123",
            "name": "Test",
            "description": None,  # Should be converted to empty string
            "created": "2025-01-01T00:00:00Z"  # Should be normalized
        }
        
        fixed_data = self.task_manager._fix_field_formats(entity_data)
        
        self.assertEqual(fixed_data["description"], "")
        self.assertIn("2025-01-01T00:00:00", fixed_data["created"])


if __name__ == "__main__":
    unittest.main()