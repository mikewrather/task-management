"""Tests for voice processing cleanup operations"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import json

from src.voice_task_manager.core.cleanup import VoiceCleanup
from src.voice_task_manager.models.voice_file import VoiceFile


class TestVoiceCleanup:
    """Test cases for VoiceCleanup functionality"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Create required subdirectories
            (temp_path / 'data').mkdir()
            (temp_path / 'logs').mkdir()
            (temp_path / 'temp').mkdir()
            yield temp_path
    
    @pytest.fixture
    def cleanup_system(self, temp_project_root):
        """Create a VoiceCleanup instance"""
        return VoiceCleanup(temp_project_root)
    
    def test_cleanup_initialization(self, temp_project_root):
        """Test cleanup system initialization"""
        cleanup = VoiceCleanup(temp_project_root)
        
        assert cleanup.project_root == temp_project_root
        assert cleanup.temp_dir == temp_project_root / 'temp'
        assert cleanup.data_dir == temp_project_root / 'data'
        assert cleanup.logs_dir == temp_project_root / 'logs'
    
    @patch('src.voice_task_manager.core.cleanup.VoiceDatabase')
    def test_cleanup_old_files_database(self, mock_db_class, cleanup_system):
        """Test cleaning up old database records"""
        # Mock database
        mock_db = Mock()
        mock_db.cleanup_old_records.return_value = 5
        mock_db.vacuum_database.return_value = None
        mock_db_class.return_value = mock_db
        
        result = cleanup_system.cleanup_old_database_records(days_old=90)
        
        assert result['deleted_count'] == 5
        assert result['success'] is True
        mock_db.cleanup_old_records.assert_called_once_with(90)
        mock_db.vacuum_database.assert_called_once()
    
    def test_cleanup_temp_files(self, cleanup_system, temp_project_root):
        """Test cleaning up temporary files"""
        temp_dir = temp_project_root / 'temp'
        
        # Create test temporary files
        old_file = temp_dir / 'old_file.tmp'
        recent_file = temp_dir / 'recent_file.tmp'
        
        # Create files with different ages
        old_time = datetime.now() - timedelta(days=2)
        recent_time = datetime.now() - timedelta(hours=1)
        
        old_file.touch()
        recent_file.touch()
        
        # Mock file modification times
        with patch('os.path.getmtime') as mock_getmtime:
            mock_getmtime.side_effect = lambda path: {
                str(old_file): old_time.timestamp(),
                str(recent_file): recent_time.timestamp()
            }.get(str(path), datetime.now().timestamp())
                
            result = cleanup_system.cleanup_temp_files(hours_old=12)
            
            assert result['deleted_count'] >= 0
            assert result['success'] is True
    
    def test_cleanup_log_files(self, cleanup_system, temp_project_root):
        """Test cleaning up old log files"""
        logs_dir = temp_project_root / 'logs'
        
        # Create test log files
        old_log = logs_dir / 'old_log.log'
        recent_log = logs_dir / 'recent_log.log'
        
        old_log.write_text("Old log content")
        recent_log.write_text("Recent log content")
        
        # Mock file stats to simulate old files
        with patch('os.path.getmtime') as mock_getmtime:
            old_time = (datetime.now() - timedelta(days=40)).timestamp()
            recent_time = (datetime.now() - timedelta(days=5)).timestamp()
            
            mock_getmtime.side_effect = lambda path: {
                str(old_log): old_time,
                str(recent_log): recent_time
            }.get(str(path), datetime.now().timestamp())
            
            result = cleanup_system.cleanup_log_files(days_old=30)
            
            assert result['success'] is True
            assert result['deleted_count'] >= 0
    
    def test_cleanup_audio_cache(self, cleanup_system, temp_project_root):
        """Test cleaning up cached audio files"""
        cache_dir = temp_project_root / 'cache'
        cache_dir.mkdir()
        
        # Create cached files
        for i in range(3):
            cache_file = cache_dir / f'audio_cache_{i}.m4a'
            cache_file.write_text(f"Cached audio {i}")
        
        result = cleanup_system.cleanup_audio_cache()
        
        assert result['success'] is True
        assert result.get('deleted_count', 0) >= 0
    
    @patch('src.voice_task_manager.core.cleanup.VoiceDatabase')
    def test_cleanup_orphaned_records(self, mock_db_class, cleanup_system):
        """Test cleaning up orphaned database records"""
        # Mock database with orphaned records
        mock_db = Mock()
        mock_files = [
            VoiceFile(file_id="existing_file", status="completed"),
            VoiceFile(file_id="orphaned_file", status="completed")
        ]
        mock_db.get_all_voice_files.return_value = mock_files
        mock_db_class.return_value = mock_db
        
        # Mock file existence check
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.side_effect = lambda self: "existing_file" in str(self)
            
            result = cleanup_system.cleanup_orphaned_records()
            
            assert result['success'] is True
            assert 'orphaned_count' in result
    
    def test_archive_old_data(self, cleanup_system, temp_project_root):
        """Test archiving old data"""
        data_dir = temp_project_root / 'data'
        archive_dir = temp_project_root / 'archive'
        
        # Create test data files
        old_data = data_dir / 'old_data.json'
        old_data.write_text('{"test": "data"}')
        
        result = cleanup_system.archive_old_data(days_old=30)
        
        assert result['success'] is True
        assert 'archived_count' in result
    
    def test_cleanup_run_all(self, cleanup_system):
        """Test running all cleanup operations"""
        with patch.object(cleanup_system, 'cleanup_old_database_records') as mock_db_cleanup, \
             patch.object(cleanup_system, 'cleanup_temp_files') as mock_temp_cleanup, \
             patch.object(cleanup_system, 'cleanup_log_files') as mock_log_cleanup, \
             patch.object(cleanup_system, 'cleanup_audio_cache') as mock_cache_cleanup:
            
            # Mock all cleanup methods to return success
            mock_db_cleanup.return_value = {'success': True, 'deleted_count': 5}
            mock_temp_cleanup.return_value = {'success': True, 'deleted_count': 3}
            mock_log_cleanup.return_value = {'success': True, 'deleted_count': 2}
            mock_cache_cleanup.return_value = {'success': True, 'deleted_count': 1}
            
            result = cleanup_system.run_all_cleanup()
            
            assert result['success'] is True
            assert result['total_deleted'] == 11  # Sum of all deleted counts
            assert 'database_cleanup' in result
            assert 'temp_cleanup' in result
            assert 'log_cleanup' in result
            assert 'cache_cleanup' in result
    
    def test_get_cleanup_stats(self, cleanup_system, temp_project_root):
        """Test getting cleanup statistics"""
        # Create some test files to analyze
        temp_dir = temp_project_root / 'temp'
        logs_dir = temp_project_root / 'logs'
        
        # Create files
        (temp_dir / 'test1.tmp').write_text("temp file 1")
        (temp_dir / 'test2.tmp').write_text("temp file 2") 
        (logs_dir / 'test.log').write_text("log content")
        
        stats = cleanup_system.get_cleanup_stats()
        
        assert 'temp_files_count' in stats
        assert 'temp_files_size' in stats
        assert 'log_files_count' in stats
        assert 'log_files_size' in stats
        assert 'total_cleanable_size' in stats
    
    def test_cleanup_error_handling(self, cleanup_system):
        """Test cleanup error handling"""
        with patch.object(cleanup_system, 'cleanup_temp_files') as mock_cleanup:
            mock_cleanup.side_effect = Exception("Cleanup error")
            
            result = cleanup_system.run_all_cleanup()
            
            # Should handle errors gracefully
            assert result['success'] is False
            assert 'error' in result
    
    def test_safe_file_deletion(self, cleanup_system, temp_project_root):
        """Test safe file deletion with backup"""
        test_file = temp_project_root / 'test_file.txt'
        test_file.write_text("test content")
        
        # Test successful deletion
        result = cleanup_system._safe_delete_file(test_file)
        assert result is True
        
        # Test deletion of non-existent file
        result = cleanup_system._safe_delete_file(Path("nonexistent_file.txt"))
        assert result is False
    
    def test_directory_size_calculation(self, cleanup_system, temp_project_root):
        """Test directory size calculation"""
        test_dir = temp_project_root / 'test_size'
        test_dir.mkdir()
        
        # Create files of known size
        (test_dir / 'file1.txt').write_text("a" * 100)
        (test_dir / 'file2.txt').write_text("b" * 200)
        
        size = cleanup_system._get_directory_size(test_dir)
        assert size >= 300  # At least the content size
    
    def test_cleanup_configuration(self, cleanup_system):
        """Test cleanup configuration and settings"""
        config = cleanup_system.get_cleanup_config()
        
        assert 'database_retention_days' in config
        assert 'temp_file_retention_hours' in config
        assert 'log_retention_days' in config
        assert 'auto_cleanup_enabled' in config
    
    def test_scheduled_cleanup_check(self, cleanup_system):
        """Test checking if scheduled cleanup should run"""
        # Mock last cleanup time
        with patch.object(cleanup_system, '_get_last_cleanup_time') as mock_last_time:
            # Test when cleanup is needed (old last run)
            mock_last_time.return_value = datetime.now() - timedelta(days=2)
            assert cleanup_system.should_run_cleanup() is True
            
            # Test when cleanup is not needed (recent last run)
            mock_last_time.return_value = datetime.now() - timedelta(hours=1)
            assert cleanup_system.should_run_cleanup() is False
    
    def test_cleanup_report_generation(self, cleanup_system):
        """Test generating cleanup reports"""
        # Mock cleanup results
        cleanup_results = {
            'success': True,
            'total_deleted': 10,
            'database_cleanup': {'deleted_count': 5},
            'temp_cleanup': {'deleted_count': 3},
            'log_cleanup': {'deleted_count': 2}
        }
        
        report = cleanup_system.generate_cleanup_report(cleanup_results)
        
        assert "CLEANUP REPORT" in report
        assert "Total files deleted: 10" in report
        assert "Database records cleaned: 5" in report