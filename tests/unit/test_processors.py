"""Unit tests for processors"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from voice_task_manager.processors.claude_processor import ClaudeVoiceProcessor
from voice_task_manager.adapters.base import TaskData


class TestClaudeVoiceProcessor:
    """Test Claude voice processor"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Mock GraphRAG adapter"""
        adapter = Mock()
        adapter.get_categorization_context.return_value = {
            "recent_tasks": [],
            "project_patterns": {
                "proj123": {
                    "name": "Test Project",
                    "area_name": "Work",
                    "keywords": ["test", "project"]
                }
            },
            "area_descriptions": {
                "area456": {
                    "name": "Work",
                    "keywords": ["work", "professional"]
                }
            }
        }
        return adapter
    
    @pytest.fixture
    def processor(self, mock_adapter):
        """Create processor with mocked adapter"""
        return ClaudeVoiceProcessor(adapter=mock_adapter)
    
    def test_build_categorization_prompt(self, processor):
        """Test prompt building"""
        # Execute
        prompt = processor._build_categorization_prompt(
            "Create a task for the meeting tomorrow",
            processor.adapter.get_categorization_context()
        )
        
        # Verify
        assert "Create a task for the meeting tomorrow" in prompt
        assert "Test Project" in prompt
        assert "Work" in prompt
        assert "mcp__agent-db__query_natural_language" in prompt
    
    @patch('subprocess.run')
    def test_execute_claude_with_mcp_success(self, mock_run, processor):
        """Test successful Claude execution"""
        # Setup
        mock_response = {
            "success": True,
            "task_data": {
                "name": "Meeting task",
                "description": "Task for tomorrow's meeting",
                "priority": "High",
                "contexts": ["@work"],
                "project_id": "proj123",
                "project_name": "Test Project"
            }
        }
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_response)
        )
        
        # Execute
        result = processor._execute_claude_with_mcp("Test prompt")
        
        # Verify
        assert result["success"] is True
        assert result["task_data"]["name"] == "Meeting task"
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_process_transcript_success(self, mock_run, processor):
        """Test successful transcript processing"""
        # Setup - match the expected format with "tasks" array
        mock_response = {
            "success": True,
            "tasks": [{
                "name": "Process invoices",
                "description": "Review and process Q4 invoices",
                "priority": "Medium",
                "contexts": ["@computer"],
                "project_id": "proj123",
                "project_name": "Finance",
                "confidence": 0.9,
                "reasoning": "Found matching project"
            }],
            "overall_reasoning": "Found matching project for invoice processing"
        }
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_response)
        )
        
        # Execute
        result = processor.process_transcript(
            "I need to process the invoices for Q4",
            "voice123"
        )
        
        # Verify - process_transcript now returns List[TaskData]
        assert isinstance(result, list)
        assert len(result) == 1
        task = result[0]
        assert isinstance(task, TaskData)
        assert task.name == "Process invoices"
        assert task.project_name == "Finance"
        assert task.metadata["voice_file_id"] == "voice123"
        assert task.metadata["claude_confidence"] == 0.9
    
    def test_process_transcript_with_multiple_tasks(self, processor):
        """Test handling transcript mentioning multiple tasks"""
        # Setup
        with patch.object(processor, '_execute_claude_with_mcp') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "tasks": [{
                    "name": "Set up Android emulator",
                    "description": "Configure emulator for testing",
                    "priority": "High",
                    "contexts": ["@computer"]
                }],
                "overall_reasoning": "Main task extracted from transcript",
                "additional_tasks": [
                    "Forward events from Adapty to RevenueCat"
                ]
            }
            
            # Execute
            result = processor.process_transcript(
                "Set up emulator and also forward events",
                "voice456"
            )
            
            # Verify - process_transcript now returns List[TaskData]
            assert isinstance(result, list)
            assert len(result) >= 1
            primary_task = result[0]
            assert primary_task.name == "Set up Android emulator"
            # Check if additional tasks were captured in overall reasoning
            assert "overall_reasoning" in primary_task.metadata
    
    def test_process_transcript_failure(self, processor):
        """Test handling of processing failure"""
        # Setup
        with patch.object(processor, '_execute_claude_with_mcp') as mock_execute:
            mock_execute.return_value = {
                "success": False,
                "error": "Claude execution failed"
            }
            
            # Execute
            result = processor.process_transcript("Test", "voice789")
            
            # Verify - process_transcript now returns empty list on failure
            assert isinstance(result, list)
            assert len(result) == 0
    
    def test_batch_process_transcripts(self, processor):
        """Test batch processing of multiple transcripts"""
        # Setup
        transcripts = [
            {"transcript": "Task 1", "file_id": "f1"},
            {"transcript": "Task 2", "file_id": "f2"},
            {"transcript": "Task 3", "file_id": "f3"}
        ]
        
        with patch.object(processor, 'process_transcript') as mock_process:
            mock_process.side_effect = [
                [TaskData(name="Task 1")],  # Returns list now
                [],  # Failed - empty list  
                [TaskData(name="Task 3")]   # Returns list now
            ]
            
            # Execute
            results = processor.batch_process_transcripts(transcripts)
            
            # Verify
            assert len(results) == 2
            assert results[0].name == "Task 1"
            assert results[1].name == "Task 3"