"""
Tests for archive functionality
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from voice_task_manager.utils.database import VoiceDatabase
from voice_task_manager.models.voice_file import VoiceFile


class TestArchiveFunctionality:
    """Test archive functionality"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create temporary project directory for testing"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def database(self, temp_project_root):
        """Create test database"""
        return VoiceDatabase(temp_project_root)
    
    @pytest.fixture
    def sample_voice_file(self):
        """Create sample voice file for testing"""
        return VoiceFile(
            file_id="test_file_123",
            status='completed',
            transcript="Test transcript",
            task_url="https://notion.so/test",  
            processed_at=datetime.now() - timedelta(days=1)
        )
    
    def test_archive_database_schema(self, database):
        """Test that archive columns are properly added"""
        # The schema should be initialized with archive columns
        with database.get_connection() as conn:
            # Check if archive columns exist
            cursor = conn.execute("PRAGMA table_info(processed_files)")
            columns = [row[1] for row in cursor.fetchall()]
            
            assert 'archive_status' in columns
            assert 'archived_at' in columns
    
    def test_voice_file_archive_properties(self, sample_voice_file):
        """Test VoiceFile archive-related properties"""
        # Initially should be active (not archived)
        assert sample_voice_file.archive_status == 'active'
        assert not sample_voice_file.is_archived
        assert not sample_voice_file.is_pending_archive
        assert sample_voice_file.can_be_archived
        
        # Mark for archive
        success = sample_voice_file.mark_for_archive()
        assert success
        assert sample_voice_file.archive_status == 'pending_archive'
        assert sample_voice_file.is_pending_archive
        assert not sample_voice_file.can_be_archived
        
        # Mark as archived
        sample_voice_file.mark_archived()
        assert sample_voice_file.archive_status == 'archived'
        assert sample_voice_file.is_archived
        assert not sample_voice_file.is_pending_archive
    
    def test_voice_file_archive_eligibility(self):
        """Test archive eligibility rules"""
        # File must be completed to be archived
        incomplete_file = VoiceFile(file_id="incomplete", status="processing")
        assert not incomplete_file.can_be_archived
        
        # Completed file can be archived
        completed_file = VoiceFile(file_id="completed", status="completed")
        assert completed_file.can_be_archived
        
        # Already archived file cannot be archived again
        archived_file = VoiceFile(
            file_id="archived", 
            status="completed", 
            archive_status="archived"
        )
        assert not archived_file.can_be_archived
    
    def test_database_mark_file_for_archive(self, database, sample_voice_file):
        """Test database archive marking functionality"""
        # First save the file to database
        with database.get_connection() as conn:
            conn.execute('''
                INSERT INTO processed_files 
                (file_id, status, transcript, task_url, processed_at, archive_status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                sample_voice_file.file_id,
                sample_voice_file.status,
                sample_voice_file.transcript,
                sample_voice_file.task_url,
                sample_voice_file.processed_at,
                'active'
            ))
            conn.commit()
        
        # Mark for archive
        success = database.mark_file_for_archive(sample_voice_file.file_id)
        assert success
        
        # Verify it's marked
        pending_files = database.get_files_pending_archive()
        assert len(pending_files) == 1
        assert pending_files[0].file_id == sample_voice_file.file_id
        assert pending_files[0].archive_status == 'pending_archive'
        
        # Test marking non-existent file
        success = database.mark_file_for_archive("non_existent")
        assert not success
    
    def test_database_mark_file_archived(self, database, sample_voice_file):
        """Test marking file as successfully archived"""
        # Setup file in pending archive state
        with database.get_connection() as conn:
            conn.execute('''
                INSERT INTO processed_files 
                (file_id, status, archive_status, archived_at)
                VALUES (?, ?, ?, ?)
            ''', (
                sample_voice_file.file_id,
                'completed',
                'pending_archive',
                datetime.now()
            ))
            conn.commit()
        
        # Mark as archived
        success = database.mark_file_archived(sample_voice_file.file_id)
        assert success
        
        # Verify it's archived
        archived_files = database.get_archived_files()
        assert len(archived_files) == 1
        assert archived_files[0].file_id == sample_voice_file.file_id
        assert archived_files[0].archive_status == 'archived'
    
    def test_get_archive_statistics(self, database):
        """Test archive statistics functionality"""
        # Add some test files
        test_files = [
            ("active1", "completed", "active", None),
            ("active2", "completed", "active", None),
            ("pending1", "completed", "pending_archive", datetime.now()),
            ("archived1", "completed", "archived", datetime.now()),
            ("archived2", "completed", "archived", datetime.now() - timedelta(days=10))
        ]
        
        with database.get_connection() as conn:
            for file_id, status, archive_status, archived_at in test_files:
                conn.execute('''
                    INSERT INTO processed_files (file_id, status, archive_status, archived_at)
                    VALUES (?, ?, ?, ?)
                ''', (file_id, status, archive_status, archived_at))
            conn.commit()
        
        # Get statistics
        stats = database.get_archive_statistics()
        
        assert stats['active_files'] == 2
        assert stats['pending_archive'] == 1
        assert stats['archived_count'] == 2
        assert stats['recent_archived'] == 1  # Only one from last 7 days
        assert stats['total_files'] == 5
    
    def test_archive_file_serialization(self, sample_voice_file):
        """Test that archive fields are properly serialized"""
        # Mark for archive
        sample_voice_file.mark_for_archive()
        
        # Convert to dict
        data = sample_voice_file.to_dict()
        assert 'archive_status' in data
        assert 'archived_at' in data
        assert data['archive_status'] == 'pending_archive'
        assert data['archived_at'] is not None
        
        # Convert back from dict
        restored_file = VoiceFile.from_dict(data)
        assert restored_file.archive_status == 'pending_archive'
        assert restored_file.archived_at is not None
        assert restored_file.is_pending_archive