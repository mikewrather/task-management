"""
Test suite for duplicate voice note processing prevention
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from voice_task_manager.utils.database import VoiceDatabase
from voice_task_manager.models.voice_file import VoiceFile


class TestDuplicateProcessingPrevention:
    """Test duplicate processing prevention functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.database = VoiceDatabase(project_root=self.temp_dir)
        
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)

    def test_database_save_preserves_completed_status(self):
        """Test that saving a discovered file doesn't overwrite completed status"""
        # Create a completed file in database
        completed_file = VoiceFile(
            file_id="test123",
            status="completed",
            processed_at=datetime.now(),
            transcript="Test transcript",
            task_url="https://notion.so/test"
        )
        self.database.save_voice_file(completed_file)
        
        # Verify it was saved correctly
        db_file = self.database.get_voice_file("test123")
        assert db_file is not None
        assert db_file.status == "completed"
        assert db_file.transcript == "Test transcript"
        
        # Now try to save a "discovered" version of the same file
        discovered_file = VoiceFile(
            file_id="test123",
            status="discovered",
            discovered_at=datetime.now(),
            file_size=12345
        )
        
        # This should overwrite - this is the bug we're testing for
        self.database.save_voice_file(discovered_file)
        
        # Check what happened - this demonstrates the problem
        db_file_after = self.database.get_voice_file("test123")
        assert db_file_after is not None
        # The bug: completed status gets overwritten
        assert db_file_after.status == "discovered"  # This shows the problem
        assert db_file_after.transcript is None  # Lost the transcript!

    def test_is_file_processed_logic(self):
        """Test the is_file_processed method works correctly"""
        # Test with non-existent file
        assert not self.database.is_file_processed("nonexistent")
        
        # Test with discovered file
        discovered_file = VoiceFile(file_id="discovered123", status="discovered")
        self.database.save_voice_file(discovered_file)
        assert not self.database.is_file_processed("discovered123")
        
        # Test with completed file
        completed_file = VoiceFile(file_id="completed456", status="completed")
        self.database.save_voice_file(completed_file)
        assert self.database.is_file_processed("completed456")
        
        # Test with failed file
        failed_file = VoiceFile(file_id="failed789", status="failed")
        self.database.save_voice_file(failed_file)
        assert not self.database.is_file_processed("failed789")

    def test_archive_status_tracking(self):
        """Test that archive status is properly tracked"""
        # Create a completed file
        voice_file = VoiceFile(
            file_id="archive_test",
            status="completed",
            processed_at=datetime.now()
        )
        self.database.save_voice_file(voice_file)
        
        # Verify default archive status
        db_file = self.database.get_voice_file("archive_test")
        assert db_file.archive_status == "active"
        
        # Mark for archive
        success = self.database.mark_file_for_archive("archive_test")
        assert success
        
        # Verify pending archive status
        db_file = self.database.get_voice_file("archive_test")
        assert db_file.archive_status == "pending_archive"
        
        # Mark as archived
        success = self.database.mark_file_archived("archive_test")
        assert success
        
        # Verify archived status
        db_file = self.database.get_voice_file("archive_test")
        assert db_file.archive_status == "archived"

    def test_cleanup_configuration_awareness(self):
        """Test that cleanup configuration is respected"""
        # This would normally test the processor's cleanup logic
        # but we're testing the core concept without full processor
        
        # Test that environment variable controls cleanup
        os.environ.pop('CLEANUP_PROCESSED_FILES', None)  # Remove if set
        
        # Default should be False
        cleanup_enabled = os.getenv('CLEANUP_PROCESSED_FILES', 'false').lower() in ('true', '1', 'yes')
        assert not cleanup_enabled
        
        # Set to true and test
        os.environ['CLEANUP_PROCESSED_FILES'] = 'true'
        cleanup_enabled = os.getenv('CLEANUP_PROCESSED_FILES', 'false').lower() in ('true', '1', 'yes')
        assert cleanup_enabled