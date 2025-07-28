"""Pytest configuration and shared fixtures for voice task manager tests"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Generator, Dict, Any

@pytest.fixture
def temp_db() -> Generator[sqlite3.Connection, None, None]:
    """Provide a temporary SQLite database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        db_path = temp_file.name
    
    conn = sqlite3.connect(db_path)
    
    # Create test tables
    conn.execute('''
        CREATE TABLE IF NOT EXISTS processed_files (
            file_id TEXT PRIMARY KEY,
            processed_at TIMESTAMP,
            transcript TEXT,
            task_url TEXT
        )
    ''')
    conn.commit()
    
    yield conn
    
    conn.close()
    os.unlink(db_path)

@pytest.fixture
def mock_env_vars() -> Generator[Dict[str, str], None, None]:
    """Provide mock environment variables for testing"""
    test_env = {
        'OPENAI_API_KEY': 'test_openai_key',
        'NOTION_TOKEN': 'test_notion_token',
        'NOTION_TASKS_DB': 'test_database_id',
        'GOOGLE_DRIVE_FOLDER_ID': 'test_folder_id'
    }
    
    # Store original values
    original_values = {}
    for key in test_env:
        original_values[key] = os.environ.get(key)
        os.environ[key] = test_env[key]
    
    yield test_env
    
    # Restore original values
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value

@pytest.fixture
def mock_logger() -> Mock:
    """Provide a mock logger for testing"""
    logger = Mock()
    logger.info = Mock()
    logger.debug = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.success = Mock()
    logger.update_run_stats = Mock()
    logger.log_run_summary = Mock()
    logger.start_run = Mock()
    return logger

@pytest.fixture
def sample_voice_file_data() -> Dict[str, Any]:
    """Provide sample voice file data for testing"""
    return {
        'file_id': 'test_file_123',
        'transcript': 'This is a test voice recording',
        'task_url': 'https://notion.so/test-task-url',
        'duration': 15.5,
        'transcript_length': 30
    }

@pytest.fixture
def mock_requests_response() -> Generator[Mock, None, None]:
    """Provide a mock requests response"""
    response = Mock()
    response.ok = True
    response.status_code = 200
    response.text = '<html>Mock HTML response</html>'
    response.content = b'Mock binary content'
    response.headers = {'content-type': 'audio/m4a', 'content-length': '100000'}
    response.json = Mock(return_value={'text': 'Transcribed text', 'duration': 15.5})
    yield response

@pytest.fixture
def project_root() -> Path:
    """Provide the project root path for testing"""
    return Path(__file__).parent.parent

@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Provide a temporary project directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create basic project structure
        (temp_path / 'data').mkdir()
        (temp_path / 'logs').mkdir()
        (temp_path / 'scripts').mkdir()
        
        yield temp_path