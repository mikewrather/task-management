"""Tests for voice task manager configuration system"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import json

from src.voice_task_manager.utils.config import SystemStatus, SystemSetup


class TestSystemStatus:
    """Test cases for SystemStatus functionality"""
    
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
    def status_checker(self, temp_project_root):
        """Create a SystemStatus instance"""
        return SystemStatus(temp_project_root)
    
    def test_status_initialization(self, temp_project_root):
        """Test SystemStatus initialization"""
        status = SystemStatus(temp_project_root)
        
        assert status.project_root == temp_project_root
        assert status.data_dir == temp_project_root / 'data'
        assert status.logs_dir == temp_project_root / 'logs'
    
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_key',
        'NOTION_TOKEN': 'test_token',
        'NOTION_TASKS_DB': 'test_db_id'
    })
    def test_check_environment_variables_complete(self, status_checker):
        """Test environment variables check with all required vars"""
        result = status_checker._check_environment_variables()
        
        assert result['status'] == 'HEALTHY'
        assert result['missing_vars'] == []
        assert len(result['found_vars']) >= 3
    
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_key'
        # Missing other required vars
    }, clear=True)
    def test_check_environment_variables_missing(self, status_checker):
        """Test environment variables check with missing vars"""
        result = status_checker._check_environment_variables()
        
        assert result['status'] == 'WARNING'
        assert 'NOTION_TOKEN' in result['missing_vars']
        assert 'NOTION_TASKS_DB' in result['missing_vars']
    
    def test_check_database_connectivity(self, status_checker):
        """Test database connectivity check"""
        with patch('src.voice_task_manager.utils.config.VoiceDatabase') as mock_db_class:
            mock_db = Mock()
            mock_db.get_processing_stats.return_value = {'total_files': 5}
            mock_db_class.return_value = mock_db
            
            result = status_checker._check_database_connectivity()
            
            assert result['status'] == 'HEALTHY'
            assert result['stats']['total_files'] == 5
    
    def test_check_database_connectivity_error(self, status_checker):
        """Test database connectivity check with error"""
        with patch('src.voice_task_manager.utils.config.VoiceDatabase') as mock_db_class:
            mock_db_class.side_effect = Exception("Database connection failed")
            
            result = status_checker._check_database_connectivity()
            
            assert result['status'] == 'CRITICAL'
            assert 'error' in result
    
    def test_check_directory_structure(self, status_checker, temp_project_root):
        """Test directory structure validation"""
        result = status_checker._check_directory_structure()
        
        assert result['status'] == 'HEALTHY'
        assert result['directories']['data']['exists'] is True
        assert result['directories']['logs']['exists'] is True
    
    def test_check_directory_structure_missing(self, temp_project_root):
        """Test directory structure with missing directories"""
        # Remove a required directory
        import shutil
        shutil.rmtree(temp_project_root / 'data')
        
        status_checker = SystemStatus(temp_project_root)
        result = status_checker._check_directory_structure()
        
        assert result['status'] == 'WARNING'
        assert result['directories']['data']['exists'] is False
    
    def test_check_file_permissions(self, status_checker, temp_project_root):
        """Test file permissions check"""
        result = status_checker._check_file_permissions()
        
        assert result['status'] in ['HEALTHY', 'WARNING']
        assert 'data_dir_writable' in result
        assert 'logs_dir_writable' in result
    
    def test_check_api_connectivity_openai(self, status_checker):
        """Test OpenAI API connectivity check"""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.models.list.return_value = Mock(data=[{'id': 'gpt-3.5-turbo'}])
            mock_openai.return_value = mock_client
            
            result = status_checker._check_api_connectivity()
            
            assert 'openai' in result
            assert result['openai']['status'] in ['HEALTHY', 'WARNING', 'CRITICAL']
    
    def test_check_api_connectivity_notion(self, status_checker):
        """Test Notion API connectivity check"""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.json.return_value = {'object': 'database'}
            mock_get.return_value = mock_response
            
            result = status_checker._check_api_connectivity()
            
            assert 'notion' in result
            assert result['notion']['status'] in ['HEALTHY', 'WARNING', 'CRITICAL']
    
    def test_check_disk_space(self, status_checker):
        """Test disk space monitoring"""
        with patch('shutil.disk_usage') as mock_disk_usage:
            # Mock 100GB total, 20GB free (80% used)
            mock_disk_usage.return_value = (100 * 1024**3, 20 * 1024**3, 80 * 1024**3)
            
            result = status_checker._check_disk_space()
            
            assert result['status'] == 'WARNING'  # > 75% used
            assert result['usage_percent'] == 80.0
    
    def test_check_recent_activity(self, status_checker):
        """Test recent activity monitoring"""
        with patch('src.voice_task_manager.utils.config.VoiceDatabase') as mock_db_class:
            mock_db = Mock()
            mock_db.get_processing_stats.return_value = {
                'today_processed': 5,
                'success_rate': 90.0
            }
            mock_db_class.return_value = mock_db
            
            result = status_checker._check_recent_activity()
            
            assert result['status'] == 'HEALTHY'
            assert result['today_processed'] == 5
            assert result['success_rate'] == 90.0
    
    @patch('src.voice_task_manager.utils.config.VoiceDatabase')
    def test_get_system_status_text_format(self, mock_db_class, status_checker):
        """Test system status in text format"""
        # Mock database
        mock_db = Mock()
        mock_db.get_processing_stats.return_value = {'total_files': 10}
        mock_db_class.return_value = mock_db
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test'}):
            result = status_checker.get_system_status(detailed=False, json_format=False)
            
            assert "VOICE TASK MANAGER - SYSTEM STATUS" in result
            assert "Environment:" in result
            assert "Database:" in result
            assert "Overall System Health:" in result
    
    @patch('src.voice_task_manager.utils.config.VoiceDatabase')
    def test_get_system_status_json_format(self, mock_db_class, status_checker):
        """Test system status in JSON format"""
        # Mock database
        mock_db = Mock()
        mock_db.get_processing_stats.return_value = {'total_files': 10}
        mock_db_class.return_value = mock_db
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test'}):
            result = status_checker.get_system_status(detailed=False, json_format=True)
            
            # Should be valid JSON
            data = json.loads(result)
            assert 'timestamp' in data
            assert 'overall_status' in data
            assert 'components' in data
    
    def test_get_status_color_and_symbol(self, status_checker):
        """Test status color and symbol assignment"""
        # Test all status levels
        healthy_color, healthy_symbol = status_checker._get_status_color('HEALTHY')
        assert healthy_symbol == '✅'
        
        warning_color, warning_symbol = status_checker._get_status_color('WARNING')
        assert warning_symbol == '⚠️'
        
        critical_color, critical_symbol = status_checker._get_status_color('CRITICAL')
        assert critical_symbol == '❌'
    
    def test_calculate_overall_status(self, status_checker):
        """Test overall status calculation"""
        # All healthy components
        components = {
            'env': {'status': 'HEALTHY'},
            'database': {'status': 'HEALTHY'},
            'disk': {'status': 'HEALTHY'}
        }
        overall = status_checker._calculate_overall_status(components)
        assert overall == 'HEALTHY'
        
        # One warning component
        components['disk']['status'] = 'WARNING'
        overall = status_checker._calculate_overall_status(components)
        assert overall == 'WARNING'
        
        # One critical component
        components['database']['status'] = 'CRITICAL'
        overall = status_checker._calculate_overall_status(components)
        assert overall == 'CRITICAL'


class TestSystemSetup:
    """Test cases for SystemSetup functionality"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            yield temp_path
    
    @pytest.fixture
    def setup_system(self, temp_project_root):
        """Create a SystemSetup instance"""
        return SystemSetup(temp_project_root)
    
    def test_setup_initialization(self, temp_project_root):
        """Test SystemSetup initialization"""
        setup = SystemSetup(temp_project_root)
        
        assert setup.project_root == temp_project_root
    
    def test_create_directories(self, setup_system, temp_project_root):
        """Test directory creation"""
        result = setup_system.create_directories()
        
        assert result['success'] is True
        assert (temp_project_root / 'data').exists()
        assert (temp_project_root / 'logs').exists()
        assert (temp_project_root / 'temp').exists()
    
    def test_initialize_database(self, setup_system):
        """Test database initialization"""
        with patch('src.voice_task_manager.utils.config.VoiceDatabase') as mock_db_class:
            mock_db = Mock()
            mock_db_class.return_value = mock_db
            
            result = setup_system.initialize_database()
            
            assert result['success'] is True
            mock_db_class.assert_called_once()
    
    def test_initialize_database_error(self, setup_system):
        """Test database initialization with error"""
        with patch('src.voice_task_manager.utils.config.VoiceDatabase') as mock_db_class:
            mock_db_class.side_effect = Exception("Database initialization failed")
            
            result = setup_system.initialize_database()
            
            assert result['success'] is False
            assert 'error' in result
    
    def test_validate_environment_complete(self, setup_system):
        """Test environment validation with complete setup"""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_key',
            'NOTION_TOKEN': 'test_token',
            'NOTION_TASKS_DB': 'test_db_id'
        }):
            result = setup_system.validate_environment()
            
            assert result['success'] is True
            assert result['missing_vars'] == []
    
    def test_validate_environment_incomplete(self, setup_system):
        """Test environment validation with missing variables"""
        with patch.dict(os.environ, {}, clear=True):
            result = setup_system.validate_environment()
            
            assert result['success'] is False
            assert len(result['missing_vars']) > 0
    
    def test_create_config_files(self, setup_system, temp_project_root):
        """Test configuration file creation"""
        result = setup_system.create_config_files()
        
        assert result['success'] is True
        assert 'files_created' in result
    
    def test_setup_logging(self, setup_system):
        """Test logging setup"""
        with patch('src.voice_task_manager.utils.config.VoiceLogger') as mock_logger_class:
            mock_logger = Mock()
            mock_logger_class.return_value = mock_logger
            
            result = setup_system.setup_logging()
            
            assert result['success'] is True
            mock_logger_class.assert_called_once()
    
    def test_test_api_connections(self, setup_system):
        """Test API connection testing"""
        with patch('openai.OpenAI') as mock_openai, \
             patch('requests.get') as mock_requests:
            
            # Mock successful OpenAI connection
            mock_client = Mock()  
            mock_client.models.list.return_value = Mock(data=[])
            mock_openai.return_value = mock_client
            
            # Mock successful Notion connection
            mock_response = Mock()
            mock_response.ok = True
            mock_response.json.return_value = {'object': 'database'}
            mock_requests.return_value = mock_response
            
            result = setup_system.test_api_connections()
            
            assert result['success'] is True
            assert 'openai' in result['connections']
            assert 'notion' in result['connections']
    
    def test_run_full_setup(self, setup_system):
        """Test complete setup process"""
        with patch.object(setup_system, 'create_directories') as mock_dirs, \
             patch.object(setup_system, 'initialize_database') as mock_db, \
             patch.object(setup_system, 'validate_environment') as mock_env, \
             patch.object(setup_system, 'create_config_files') as mock_config, \
             patch.object(setup_system, 'setup_logging') as mock_logging:
            
            # Mock all setup steps to succeed
            mock_dirs.return_value = {'success': True}
            mock_db.return_value = {'success': True}
            mock_env.return_value = {'success': True, 'missing_vars': []}
            mock_config.return_value = {'success': True}
            mock_logging.return_value = {'success': True}
            
            result = setup_system.run_full_setup()
            
            assert result['success'] is True
            assert result['steps_completed'] == 5
            assert 'setup_summary' in result
    
    def test_run_full_setup_with_failures(self, setup_system):
        """Test setup process with some failures"""
        with patch.object(setup_system, 'create_directories') as mock_dirs, \
             patch.object(setup_system, 'initialize_database') as mock_db, \
             patch.object(setup_system, 'validate_environment') as mock_env:
            
            # Mock some steps to fail
            mock_dirs.return_value = {'success': True}
            mock_db.return_value = {'success': False, 'error': 'DB failed'}
            mock_env.return_value = {'success': False, 'missing_vars': ['API_KEY']}
            
            result = setup_system.run_full_setup()
            
            assert result['success'] is False
            assert len(result['failed_steps']) > 0
    
    def test_get_setup_status(self, setup_system):
        """Test getting setup status"""
        status = setup_system.get_setup_status()
        
        assert 'directories_exist' in status
        assert 'database_exists' in status
        assert 'environment_complete' in status
        assert 'overall_ready' in status
    
    def test_generate_setup_report(self, setup_system):
        """Test setup report generation"""
        setup_results = {
            'success': True,
            'steps_completed': 5,
            'failed_steps': [],
            'setup_summary': {
                'directories': {'success': True},
                'database': {'success': True},
                'environment': {'success': True}
            }
        }
        
        report = setup_system.generate_setup_report(setup_results)
        
        assert "SYSTEM SETUP REPORT" in report
        assert "Setup completed successfully!" in report
        assert "Steps completed: 5" in report
    
    def test_cleanup_failed_setup(self, setup_system, temp_project_root):
        """Test cleanup of failed setup"""
        # Create some directories and files
        (temp_project_root / 'data').mkdir()
        (temp_project_root / 'temp_setup_file.txt').write_text("test")
        
        result = setup_system.cleanup_failed_setup()
        
        assert result['success'] is True
        assert 'cleaned_items' in result