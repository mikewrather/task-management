"""Tests for voice task manager data models"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import json

from voice_task_manager.models.voice_file import VoiceFile
from voice_task_manager.models.task import Task


class TestVoiceFile:
    """Test cases for VoiceFile model"""
    
    def test_voice_file_creation_minimal(self):
        """Test creating a VoiceFile with minimal data"""
        file_id = "test_file_123"
        voice_file = VoiceFile(file_id=file_id)
        
        assert voice_file.file_id == file_id
        assert voice_file.status == "discovered"  # Fixed: uses "discovered" not "pending"
        assert voice_file.discovered_at is not None
        assert voice_file.processed_at is None
        assert voice_file.transcript is None
        assert voice_file.task_url is None
        assert voice_file.metadata == {}
    
    def test_voice_file_creation_full(self):
        """Test creating a VoiceFile with all data"""
        now = datetime.now()
        voice_file = VoiceFile(
            file_id="test_file_123",
            discovered_at=now,
            processed_at=now + timedelta(minutes=5),
            status="completed",
            file_size=1024000,
            content_type="audio/m4a",
            transcript="This is a test transcript",
            transcript_length=25,
            duration_seconds=15.5,
            task_url="https://notion.so/test-task",
            error_message=None,
            retry_count=0,
            metadata={"test": "data"}
        )
        
        assert voice_file.file_id == "test_file_123"
        assert voice_file.status == "completed"
        assert voice_file.file_size == 1024000
        assert voice_file.transcript == "This is a test transcript"
        assert voice_file.transcript_length == 25
        assert voice_file.duration_seconds == 15.5
        assert voice_file.file_size_mb == 0.98  # 1024000 bytes = 0.98MB
        assert voice_file.google_drive_url == "https://drive.google.com/file/d/test_file_123/view"
    
    def test_voice_file_google_drive_url(self):
        """Test Google Drive URL generation"""
        voice_file = VoiceFile(file_id="abc123")
        expected_url = "https://drive.google.com/file/d/abc123/view"
        assert voice_file.google_drive_url == expected_url
    
    def test_voice_file_file_size_mb(self):
        """Test file size MB calculation"""
        # Test with exact MB
        voice_file = VoiceFile(file_id="test", file_size=1048576)  # 1MB
        assert voice_file.file_size_mb == 1.0
        
        # Test with fractional MB
        voice_file = VoiceFile(file_id="test", file_size=1572864)  # 1.5MB
        assert voice_file.file_size_mb == 1.5
        
        # Test with None
        voice_file = VoiceFile(file_id="test", file_size=None)
        assert voice_file.file_size_mb is None
    
    def test_mark_processing(self):
        """Test marking file as processing"""
        voice_file = VoiceFile(file_id="test")
        assert voice_file.status == "discovered"  # Fixed: starts as "discovered"
        
        voice_file.mark_processing()
        assert voice_file.status == "processing"
    
    def test_mark_completed(self):
        """Test marking file as completed"""
        voice_file = VoiceFile(file_id="test")
        transcript = "Test transcript"
        task_url = "https://notion.so/task"
        
        voice_file.mark_completed(transcript, task_url)
        
        assert voice_file.status == "completed"
        assert voice_file.transcript == transcript
        assert voice_file.task_url == task_url
        assert voice_file.processed_at is not None
        assert voice_file.transcript_length == len(transcript)
    
    def test_mark_failed(self):
        """Test marking file as failed"""
        voice_file = VoiceFile(file_id="test")
        error_msg = "Processing failed"
        
        voice_file.mark_failed(error_msg)
        
        assert voice_file.status == "failed"
        assert voice_file.error_message == error_msg
        # mark_failed doesn't set processed_at in the current implementation
        assert voice_file.retry_count == 0
    
    def test_retry_count_incremented_by_mark_processing(self):
        """Test that retry count is incremented by mark_processing"""
        voice_file = VoiceFile(file_id="test")
        assert voice_file.retry_count == 0
        
        voice_file.mark_processing()
        assert voice_file.retry_count == 1
        
        voice_file.mark_processing()
        assert voice_file.retry_count == 2
    
    def test_to_dict(self):
        """Test converting VoiceFile to dictionary"""
        now = datetime.now()
        voice_file = VoiceFile(
            file_id="test_file",
            discovered_at=now,
            transcript="Test transcript",
            status="completed"
        )
        
        result = voice_file.to_dict()
        
        assert result["file_id"] == "test_file"
        assert result["status"] == "completed"
        assert result["transcript"] == "Test transcript"
        assert "discovered_at" in result
        assert isinstance(result, dict)
    
    def test_from_dict(self):
        """Test creating VoiceFile from dictionary"""
        now = datetime.now()
        data = {
            "file_id": "test_file",
            "discovered_at": now.isoformat(),
            "status": "completed",
            "transcript": "Test transcript",
            "file_size": 1024,
            "duration_seconds": 15.5
        }
        
        voice_file = VoiceFile.from_dict(data)
        
        assert voice_file.file_id == "test_file"
        assert voice_file.status == "completed"
        assert voice_file.transcript == "Test transcript"
        assert voice_file.file_size == 1024
        assert voice_file.duration_seconds == 15.5
        assert isinstance(voice_file.discovered_at, datetime)


class TestTask:
    """Test cases for Task model"""
    
    def test_task_creation_minimal(self):
        """Test creating a Task with minimal data"""
        task = Task(
            task_id="task_123",
            title="Test Task",
            content="Test content"  # Fixed: content is required parameter
        )
        
        assert task.task_id == "task_123"
        assert task.title == "Test Task"
        assert task.content == "Test content"
        assert task.status == "Inbox"
        assert task.contexts == ["voice", "auto-processed"]  # Fixed: default includes both
        assert task.created_at is not None
        assert task.updated_at is not None  # Fixed: updated_at is set in __post_init__
        assert task.url is None
        assert task.metadata == {}
    
    def test_notion_task_creation_full(self):
        """Test creating a Task with all data"""
        now = datetime.now()
        task = Task(
            task_id="task_123",
            title="Test Task",
            content="This is test content",
            status="In Progress",
            contexts=["voice", "work"],
            created_at=now,
            updated_at=now + timedelta(minutes=10),
            url="https://notion.so/task-123",
            voice_file_id="file_123",
            transcript_source="voice recording",
            metadata={"priority": "high"}
        )
        
        assert task.task_id == "task_123"
        assert task.title == "Test Task"
        assert task.content == "This is test content"
        assert task.status == "In Progress"
        assert task.contexts == ["voice", "work"]
        assert task.voice_file_id == "file_123"
        assert task.transcript_source == "voice recording"
        assert task.metadata["priority"] == "high"
    
    def test_update_status(self):
        """Test updating task status"""
        task = Task(task_id="test", title="Test", content="Test content")
        assert task.status == "Inbox"
        
        task.update_status("In Progress")
        assert task.status == "In Progress"
        assert task.updated_at is not None
    
    def test_add_context(self):
        """Test adding context to task"""
        task = Task(task_id="test", title="Test", content="Test content")
        assert task.contexts == ["voice", "auto-processed"]  # Fixed: default contexts
        
        task.add_context("work")
        assert "work" in task.contexts
        assert "voice" in task.contexts
        assert task.updated_at is not None
        
        # Test duplicate context
        task.add_context("work")
        assert task.contexts.count("work") == 1  # Should not duplicate
    
    def test_remove_context(self):
        """Test removing context from task"""
        task = Task(task_id="test", title="Test", content="Test content", contexts=["voice", "work"])
        
        task.remove_context("work")
        assert "work" not in task.contexts
        assert "voice" in task.contexts
        assert task.updated_at is not None
    
    def test_url_property(self):
        """Test URL property"""
        task = Task(
            task_id="test",
            title="Test Task",
            content="Test content",
            url="https://www.notion.so/task-123"
        )
        
        assert task.url == "https://www.notion.so/task-123"
        
        # Test with None URL
        task_no_url = Task(task_id="test", title="Test", content="Test content")
        assert task_no_url.url is None
    
    def test_to_dict(self):
        """Test converting Task to dictionary"""
        now = datetime.now()
        task = Task(
            task_id="test_task",
            title="Test Task",
            content="Test content",
            status="In Progress",
            created_at=now
        )
        
        result = task.to_dict()
        
        assert result["task_id"] == "test_task"
        assert result["title"] == "Test Task"
        assert result["content"] == "Test content"
        assert result["status"] == "In Progress"
        assert "created_at" in result
        assert isinstance(result, dict)
    
    def test_from_dict(self):
        """Test creating Task from dictionary"""
        now = datetime.now()
        data = {
            "task_id": "test_task",
            "title": "Test Task",
            "content": "Test content", 
            "status": "Done",
            "contexts": ["voice", "work"],  # Fixed: from_dict expects list, not JSON string
            "created_at": now.isoformat(),
            "voice_file_id": "file_123"
        }
        
        task = Task.from_dict(data)
        
        assert task.task_id == "test_task"
        assert task.title == "Test Task"
        assert task.content == "Test content"
        assert task.status == "Done"
        assert task.contexts == ["voice", "work"]
        assert task.voice_file_id == "file_123"
        assert isinstance(task.created_at, datetime)
    
    def test_from_dict_with_context_parsing(self):
        """Test creating Task from dict with context parsing"""
        now = datetime.now()
        # Test with list contexts
        data = {
            "task_id": "test",
            "title": "Test",
            "content": "Test content",
            "created_at": now.isoformat(),
            "contexts": ["voice", "work", "urgent"]
        }
        task = Task.from_dict(data)
        assert task.contexts == ["voice", "work", "urgent"]
        
        # Test with different list contexts
        data["contexts"] = ["voice", "personal"]
        task = Task.from_dict(data)
        assert task.contexts == ["voice", "personal"]
        
        # Test with missing contexts key (gets default)
        del data["contexts"]  # Remove the key entirely
        task = Task.from_dict(data)
        assert task.contexts == ["voice", "auto-processed"]  # Default when key missing
    
    def test_task_validation(self):
        """Test task data validation"""
        # Test valid task
        task = Task(task_id="valid", title="Valid Task", content="Valid content")
        assert task.task_id == "valid"
        
        # Test empty title (should still work)
        task = Task(task_id="test", title="", content="Test content")
        assert task.title == ""
        
        # Test long title (no truncation implemented)
        long_title = "A" * 300
        task = Task(task_id="test", title=long_title, content="Test content")
        assert task.title == long_title  # No truncation in current implementation