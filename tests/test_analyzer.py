"""Tests for voice processing analytics and reporting"""

import pytest
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from io import StringIO

from src.voice_task_manager.core.analyzer import VoiceAnalyzer
from src.voice_task_manager.models.voice_file import VoiceFile


class TestVoiceAnalyzer:
    """Test cases for VoiceAnalyzer functionality"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Create required subdirectories
            (temp_path / 'data').mkdir()
            (temp_path / 'logs').mkdir()
            yield temp_path
    
    @pytest.fixture
    def analyzer(self, temp_project_root):
        """Create a VoiceAnalyzer instance"""
        return VoiceAnalyzer(temp_project_root)
    
    @pytest.fixture
    def sample_run_history(self):
        """Create sample run history data"""
        now = datetime.now()
        return [
            {
                "timestamp": (now - timedelta(hours=2)).isoformat(),
                "status": "success",
                "files_found": 5,
                "files_processed": 3,
                "run_duration_seconds": 25.5,
                "errors": 0,
                "warnings": 1,
                "processing_success_rate": 60.0
            },
            {
                "timestamp": (now - timedelta(hours=1)).isoformat(),
                "status": "success", 
                "files_found": 3,
                "files_processed": 3,
                "run_duration_seconds": 18.2,
                "errors": 0,
                "warnings": 0,
                "processing_success_rate": 100.0
            },
            {
                "timestamp": now.isoformat(),
                "status": "partial",
                "files_found": 4,
                "files_processed": 2,
                "run_duration_seconds": 30.1,
                "errors": 1,
                "warnings": 0,
                "processing_success_rate": 50.0
            }
        ]
    
    def test_analyzer_initialization(self, temp_project_root):
        """Test analyzer initialization"""
        analyzer = VoiceAnalyzer(temp_project_root)
        
        assert analyzer.project_root == temp_project_root
        assert analyzer.log_dir == temp_project_root / 'logs'
        assert analyzer.run_history_log == temp_project_root / 'logs' / 'cron-run-history.log'
    
    @patch('src.voice_task_manager.core.analyzer.VoiceDatabase')
    @patch('src.voice_task_manager.core.analyzer.VoiceLogger')
    def test_generate_analysis_no_data(self, mock_logger_class, mock_db_class, analyzer):
        """Test analysis generation with no data"""
        # Mock empty database and no run history
        mock_db = Mock()
        mock_db.get_processing_stats.return_value = {
            'total_files': 0,
            'completed_files': 0,
            'failed_files': 0,
            'pending_files': 0,
            'today_processed': 0,
            'success_rate': 0.0,
            'avg_processing_time_seconds': 0
        }
        mock_db_class.return_value = mock_db
        
        # Mock empty run history
        with patch.object(analyzer, '_load_run_history', return_value=[]):
            result = analyzer.generate_analysis()
            
            assert "No voice processing data found" in result
    
    def test_load_run_history(self, analyzer, sample_run_history):
        """Test loading run history from log file"""
        # Create temporary log file with sample data
        log_content = '\n'.join(json.dumps(run) for run in sample_run_history)
        
        with patch('builtins.open', mock_open(read_data=log_content)):
            runs = analyzer._load_run_history()
            
            assert len(runs) == 3
            assert all('datetime' in run for run in runs)
            assert all(isinstance(run['datetime'], datetime) for run in runs)
            # Should be sorted by datetime descending
            assert runs[0]['datetime'] > runs[1]['datetime']
    
    def test_load_run_history_with_invalid_json(self, analyzer):
        """Test loading run history with invalid JSON lines"""
        log_content = '''{"valid": "json", "timestamp": "2025-01-01T12:00:00"}
invalid json line
{"another": "valid", "timestamp": "2025-01-01T13:00:00"}'''
        
        with patch('builtins.open', mock_open(read_data=log_content)):
            runs = analyzer._load_run_history()
            
            # Should skip invalid line and load valid ones
            assert len(runs) == 2
    
    def test_load_run_history_missing_file(self, analyzer):
        """Test loading run history when file doesn't exist"""
        runs = analyzer._load_run_history()
        assert runs == []
    
    def test_filter_today_runs(self, analyzer, sample_run_history):
        """Test filtering runs to today only"""
        # Add datetime objects to sample data
        now = datetime.now()
        for i, run in enumerate(sample_run_history):
            run['datetime'] = now - timedelta(hours=i)
        
        # Add run from yesterday
        yesterday_run = {
            "datetime": now - timedelta(days=1),
            "status": "success"
        }
        sample_run_history.append(yesterday_run)
        
        today_runs = analyzer._filter_today_runs(sample_run_history)
        
        # Should only include today's runs
        assert len(today_runs) == 3  # Exclude yesterday's run
        assert all(run['datetime'].date() == now.date() for run in today_runs)
    
    @patch('src.voice_task_manager.core.analyzer.VoiceDatabase')
    def test_format_recent_runs(self, mock_db_class, analyzer, sample_run_history):
        """Test formatting recent runs display"""
        # Add datetime objects
        for i, run in enumerate(sample_run_history):
            run['datetime'] = datetime.now() - timedelta(hours=i)
        
        result = analyzer._format_recent_runs(sample_run_history, count=2)
        
        assert "Last 2 runs:" in result
        assert "✅" in result  # Success symbols
        assert "⚠️" in result   # Partial symbol
        assert "Found:" in result
        assert "Processed:" in result
        assert "Duration:" in result
    
    @patch('src.voice_task_manager.core.analyzer.VoiceDatabase')
    def test_format_today_analysis(self, mock_db_class, analyzer, sample_run_history):
        """Test formatting today's activity analysis"""
        # Add datetime objects for today
        now = datetime.now()
        for i, run in enumerate(sample_run_history):
            run['datetime'] = now - timedelta(hours=i)
        
        db_stats = {
            'today_processed': 5,
            'success_rate': 85.0
        }
        
        result = analyzer._format_today_analysis(sample_run_history, db_stats)
        
        assert "Today's Activity" in result
        assert "3 runs" in result
        assert "Files processed: 5" in result
        assert "Success rate: 85.0%" in result
    
    @patch('src.voice_task_manager.core.analyzer.VoiceDatabase')
    def test_format_comprehensive_stats(self, mock_db_class, analyzer, sample_run_history):
        """Test formatting comprehensive statistics"""
        # Add datetime objects
        now = datetime.now()
        for i, run in enumerate(sample_run_history):
            run['datetime'] = now - timedelta(hours=i)
        
        db_stats = {
            'total_files': 10,
            'completed_files': 8,
            'failed_files': 1,
            'pending_files': 1,
            'today_processed': 5,
            'success_rate': 80.0,
            'avg_processing_time_seconds': 22.5
        }
        
        result = analyzer._format_comprehensive_stats(sample_run_history, db_stats)
        
        assert "VOICE PROCESSING STATISTICS" in result
        assert "RUN STATISTICS:" in result
        assert "Total Runs:             3" in result
        assert "FILE STATISTICS:" in result
        assert "DATABASE STATISTICS:" in result
        assert "System Health:" in result
        assert "HEALTHY" in result or "WARNING" in result or "CRITICAL" in result
    
    @patch('src.voice_task_manager.core.analyzer.VoiceDatabase')
    def test_format_error_analysis(self, mock_db_class, analyzer, sample_run_history):
        """Test formatting error and warning analysis"""
        # Add datetime objects and modify to include errors/warnings
        now = datetime.now()
        for i, run in enumerate(sample_run_history):
            run['datetime'] = now - timedelta(hours=i)
        
        # Add more errors/warnings for testing
        sample_run_history[0]['errors'] = 2
        sample_run_history[1]['warnings'] = 3
        
        result = analyzer._format_error_analysis(sample_run_history)
        
        assert "ERROR SUMMARY" in result
        assert "WARNING SUMMARY" in result
        assert "❌" in result  # Error symbol
        assert "⚠️" in result  # Warning symbol
    
    def test_format_run_entry(self, analyzer):
        """Test formatting individual run entry"""
        now = datetime.now()
        run = {
            'datetime': now,
            'status': 'success',
            'files_found': 5,
            'files_processed': 3,
            'run_duration_seconds': 25.5,
            'errors': 0,
            'warnings': 1
        }
        
        result = analyzer._format_run_entry(run)
        
        assert "✅" in result  # Success symbol
        assert "Found:  5" in result
        assert "Processed:  3" in result
        assert "Duration:  25.5s" in result
        assert "Errors:  0" in result
        assert "Warnings:  1" in result
    
    @patch('src.voice_task_manager.core.analyzer.VoiceDatabase')
    def test_export_json(self, mock_db_class, analyzer, sample_run_history):
        """Test JSON export functionality"""
        # Add datetime objects
        for i, run in enumerate(sample_run_history):
            run['datetime'] = datetime.now() - timedelta(hours=i)
        
        db_stats = {'total_files': 10, 'success_rate': 80.0}
        
        result = analyzer._export_json(sample_run_history, db_stats)
        
        # Parse JSON to verify structure
        data = json.loads(result)
        
        assert 'export_timestamp' in data
        assert 'database_stats' in data
        assert 'run_history' in data
        assert 'summary' in data
        
        assert data['database_stats']['total_files'] == 10
        assert len(data['run_history']) == 3
        assert data['summary']['total_runs'] == 3
    
    @patch('src.voice_task_manager.core.analyzer.VoiceDatabase')
    def test_export_csv(self, mock_db_class, analyzer, sample_run_history):
        """Test CSV export functionality"""
        # Add datetime objects
        for i, run in enumerate(sample_run_history):
            run['datetime'] = datetime.now() - timedelta(hours=i)
        
        result = analyzer._export_csv(sample_run_history)
        
        # Check CSV structure
        lines = result.split('\n')
        assert len(lines) >= 4  # Header + 3 data rows + possible empty line
        
        # Check header
        header = lines[0]
        assert 'timestamp' in header
        assert 'status' in header
        assert 'files_found' in header
        assert 'files_processed' in header
        
        # Check data rows
        data_row = lines[1]
        assert 'success' in data_row or 'partial' in data_row
    
    @patch('src.voice_task_manager.core.analyzer.VoiceDatabase')
    def test_export_html(self, mock_db_class, analyzer, sample_run_history):
        """Test HTML export functionality"""
        # Add datetime objects
        for i, run in enumerate(sample_run_history):
            run['datetime'] = datetime.now() - timedelta(hours=i)
        
        db_stats = {
            'total_files': 10,
            'completed_files': 8,
            'failed_files': 1,
            'today_processed': 5,
            'avg_processing_time_seconds': 22.5,
            'success_rate': 80.0
        }
        
        result = analyzer._export_html(sample_run_history, db_stats)
        
        # Check HTML structure
        assert '<!DOCTYPE html>' in result
        assert '<title>Voice Processing Analysis Report</title>' in result
        assert 'Voice Processing Analysis Report' in result
        assert '<table>' in result
        assert 'Total Files: 10' in result
        assert 'success' in result  # Status classes
    
    @patch('src.voice_task_manager.core.analyzer.VoiceDatabase')  
    def test_get_trend_analysis(self, mock_db_class, analyzer):
        """Test trend analysis functionality"""
        # Create sample data spanning multiple days
        now = datetime.now()
        runs = []
        
        for day in range(3):
            for hour in range(2):  # 2 runs per day
                run_time = now - timedelta(days=day, hours=hour)
                runs.append({
                    'datetime': run_time,
                    'files_found': 5 - day,  # Decreasing trend
                    'files_processed': 4 - day,
                    'errors': day,  # Increasing errors
                    'run_duration_seconds': 20.0 + day * 5
                })
        
        with patch.object(analyzer, '_load_run_history', return_value=runs):
            result = analyzer.get_trend_analysis(days_back=7)
            
            assert 'period_days' in result
            assert 'total_runs' in result
            assert 'daily_breakdown' in result
            assert 'summary' in result
            
            assert result['period_days'] == 7
            assert result['total_runs'] == 6  # 3 days * 2 runs
            assert len(result['daily_breakdown']) <= 3  # Up to 3 days
    
    def test_get_trend_analysis_no_data(self, analyzer):
        """Test trend analysis with no data"""
        with patch.object(analyzer, '_load_run_history', return_value=[]):
            result = analyzer.get_trend_analysis()
            
            assert 'error' in result
            assert 'No data available' in result['error']
    
    @patch('src.voice_task_manager.core.analyzer.VoiceDatabase')
    def test_export_data_invalid_format(self, mock_db_class, analyzer):
        """Test export with invalid format"""
        with pytest.raises(ValueError, match="Unsupported export format"):
            analyzer._export_data([], {}, "invalid_format")
    
    @patch('src.voice_task_manager.core.analyzer.VoiceDatabase')
    def test_generate_analysis_with_export(self, mock_db_class, analyzer, sample_run_history):
        """Test generate_analysis with export format"""
        # Mock database
        mock_db = Mock()
        mock_db.get_processing_stats.return_value = {'total_files': 5}
        mock_db_class.return_value = mock_db
        
        # Add datetime objects
        for i, run in enumerate(sample_run_history):
            run['datetime'] = datetime.now() - timedelta(hours=i)
        
        with patch.object(analyzer, '_load_run_history', return_value=sample_run_history):
            result = analyzer.generate_analysis(export_format='json')
            
            # Should return JSON string
            data = json.loads(result)
            assert 'export_timestamp' in data
            assert 'run_history' in data
    
    @patch('src.voice_task_manager.core.analyzer.VoiceDatabase')
    def test_generate_analysis_today_only(self, mock_db_class, analyzer, sample_run_history):
        """Test generate_analysis with today_only flag"""
        # Mock database
        mock_db = Mock()
        mock_db.get_processing_stats.return_value = {
            'total_files': 5,
            'today_processed': 3,
            'success_rate': 85.0
        }
        mock_db_class.return_value = mock_db
        
        # Add datetime objects for today
        now = datetime.now()
        for i, run in enumerate(sample_run_history):
            run['datetime'] = now - timedelta(hours=i)
        
        with patch.object(analyzer, '_load_run_history', return_value=sample_run_history):
            result = analyzer.generate_analysis(today_only=True)
            
            assert "Today's Activity" in result
            assert "Files processed: 3" in result
    
    @patch('src.voice_task_manager.core.analyzer.VoiceDatabase')
    def test_generate_analysis_include_errors(self, mock_db_class, analyzer, sample_run_history):
        """Test generate_analysis with include_errors flag"""
        # Mock database
        mock_db = Mock()
        mock_db.get_processing_stats.return_value = {'total_files': 5}
        mock_db_class.return_value = mock_db
        
        # Add datetime objects and errors
        now = datetime.now()
        for i, run in enumerate(sample_run_history):
            run['datetime'] = now - timedelta(hours=i)
            run['errors'] = i  # Add some errors
        
        with patch.object(analyzer, '_load_run_history', return_value=sample_run_history):
            result = analyzer.generate_analysis(include_errors=True)
            
            assert "ERROR SUMMARY" in result or "No errors or warnings found" in result