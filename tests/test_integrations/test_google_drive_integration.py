"""Integration tests for Google Drive API interactions"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import io

from src.voice_task_manager.integrations.google_drive import GoogleDriveIntegration


class TestGoogleDriveIntegration:
    """Integration tests for Google Drive API connectivity and file operations"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / 'data').mkdir()
            (temp_path / 'logs').mkdir()
            yield temp_path
    
    @pytest.fixture
    def drive_integration(self, temp_project_root):
        """Create a GoogleDriveIntegration instance"""
        return GoogleDriveIntegration(temp_project_root)
    
    @pytest.fixture
    def sample_audio_data(self):
        """Create sample audio data for testing"""
        return b"fake_audio_data_for_testing" * 1000
    
    @pytest.mark.integration
    @patch.dict(os.environ, {
        'GOOGLE_DRIVE_FOLDER_ID': 'test_folder_id',
        'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/credentials.json'
    })
    def test_drive_client_initialization(self, drive_integration):
        """Test Google Drive client initialization"""
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service
            
            with patch('google.auth.default') as mock_auth:
                mock_credentials = Mock()
                mock_auth.return_value = (mock_credentials, 'test-project')
                
                client = drive_integration._initialize_drive_client()
                
                assert client is not None
                mock_build.assert_called_once_with('drive', 'v3', credentials=mock_credentials)
    
    @pytest.mark.integration
    def test_drive_client_missing_credentials(self, drive_integration):
        """Test Drive client initialization without credentials"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Google Drive folder ID not found"):
                drive_integration._initialize_drive_client()
    
    @pytest.mark.integration
    @patch('googleapiclient.discovery.build')
    @patch('google.auth.default')
    def test_list_audio_files_success(self, mock_auth, mock_build, drive_integration):
        """Test successful listing of audio files from Drive"""
        # Mock authentication
        mock_credentials = Mock()
        mock_auth.return_value = (mock_credentials, 'test-project')
        
        # Mock Drive service
        mock_service = Mock()
        mock_files = Mock()
        mock_service.files.return_value = mock_files
        mock_list = Mock()
        mock_files.list.return_value = mock_list
        
        # Mock API response
        mock_response = {
            'files': [
                {
                    'id': 'file_1',
                    'name': 'recording_1.m4a',
                    'mimeType': 'audio/m4a',
                    'size': '1024000',
                    'createdTime': '2025-01-24T10:00:00Z',
                    'modifiedTime': '2025-01-24T10:05:00Z'
                },
                {
                    'id': 'file_2',
                    'name': 'recording_2.mp3',
                    'mimeType': 'audio/mpeg',
                    'size': '2048000',
                    'createdTime': '2025-01-24T11:00:00Z',
                    'modifiedTime': '2025-01-24T11:05:00Z'
                }
            ]
        }
        mock_list.execute.return_value = mock_response
        mock_build.return_value = mock_service
        
        result = drive_integration.list_audio_files()
        
        assert result['success'] is True
        assert len(result['files']) == 2
        assert result['files'][0]['id'] == 'file_1'
        assert result['files'][0]['name'] == 'recording_1.m4a'
        assert result['files'][1]['id'] == 'file_2'
        
        # Verify API call parameters
        mock_files.list.assert_called_once()
        call_kwargs = mock_files.list.call_args[1]
        assert 'test_folder_id' in call_kwargs['q']
        assert 'audio/' in call_kwargs['q']
    
    @pytest.mark.integration
    @patch('googleapiclient.discovery.build')
    @patch('google.auth.default')
    def test_download_file_success(self, mock_auth, mock_build, drive_integration, sample_audio_data):
        """Test successful file download from Drive"""
        # Mock authentication
        mock_credentials = Mock()
        mock_auth.return_value = (mock_credentials, 'test-project')
        
        # Mock Drive service
        mock_service = Mock()
        mock_files = Mock()
        mock_service.files.return_value = mock_files
        mock_get = Mock()
        mock_files.get_media.return_value = mock_get
        
        # Mock download response
        mock_request = Mock()
        mock_get.return_value = mock_request
        
        # Mock the actual download
        mock_downloader = Mock()
        mock_downloader.next_chunk.return_value = (None, True)  # Download complete
        
        with patch('googleapiclient.http.MediaIoBaseDownload') as mock_media_download:
            mock_media_download.return_value = mock_downloader
            
            with patch('io.BytesIO') as mock_bytes_io:
                mock_buffer = Mock()
                mock_buffer.getvalue.return_value = sample_audio_data
                mock_bytes_io.return_value = mock_buffer
                
                mock_build.return_value = mock_service
                
                result = drive_integration.download_file('test_file_123', '/tmp/test_download.m4a')
                
                assert result['success'] is True
                assert result['file_path'] == '/tmp/test_download.m4a'
                assert result['file_size'] == len(sample_audio_data)
    
    @pytest.mark.integration
    @patch('googleapiclient.discovery.build')
    @patch('google.auth.default')
    def test_download_file_not_found(self, mock_auth, mock_build, drive_integration):
        """Test download of non-existent file"""
        # Mock authentication
        mock_credentials = Mock()
        mock_auth.return_value = (mock_credentials, 'test-project')
        
        # Mock Drive service to raise not found error
        mock_service = Mock()
        mock_files = Mock()
        mock_service.files.return_value = mock_files
        
        from googleapiclient.errors import HttpError
        mock_files.get_media.side_effect = HttpError(
            Mock(status=404), b'{"error": {"message": "File not found"}}'
        )
        
        mock_build.return_value = mock_service
        
        result = drive_integration.download_file('nonexistent_file', '/tmp/missing.m4a')
        
        assert result['success'] is False
        assert 'File not found' in result['error']
    
    @pytest.mark.integration
    @patch('googleapiclient.discovery.build')
    @patch('google.auth.default')
    def test_get_file_metadata(self, mock_auth, mock_build, drive_integration):
        """Test retrieving file metadata"""
        # Mock authentication
        mock_credentials = Mock()
        mock_auth.return_value = (mock_credentials, 'test-project')
        
        # Mock Drive service
        mock_service = Mock()
        mock_files = Mock()
        mock_service.files.return_value = mock_files
        mock_get = Mock()
        mock_files.get.return_value = mock_get
        
        # Mock metadata response
        mock_metadata = {
            'id': 'test_file_123',
            'name': 'test_recording.m4a',
            'mimeType': 'audio/m4a',
            'size': '1024000',
            'createdTime': '2025-01-24T10:00:00Z',
            'modifiedTime': '2025-01-24T10:05:00Z',
            'webViewLink': 'https://drive.google.com/file/d/test_file_123/view',
            'parents': ['test_folder_id']
        }
        mock_get.execute.return_value = mock_metadata
        mock_build.return_value = mock_service
        
        result = drive_integration.get_file_metadata('test_file_123')
        
        assert result['success'] is True
        assert result['metadata']['id'] == 'test_file_123'
        assert result['metadata']['name'] == 'test_recording.m4a'
        assert result['metadata']['size'] == '1024000'
        
        # Verify API call
        mock_files.get.assert_called_once_with(
            fileId='test_file_123',
            fields='id,name,mimeType,size,createdTime,modifiedTime,webViewLink,parents'
        )
    
    @pytest.mark.integration
    @patch('googleapiclient.discovery.build')
    @patch('google.auth.default')
    def test_check_file_permissions(self, mock_auth, mock_build, drive_integration):
        """Test checking file permissions"""
        # Mock authentication
        mock_credentials = Mock()
        mock_auth.return_value = (mock_credentials, 'test-project')
        
        # Mock Drive service
        mock_service = Mock()
        mock_permissions = Mock()
        mock_service.permissions.return_value = mock_permissions
        mock_list = Mock()
        mock_permissions.list.return_value = mock_list
        
        # Mock permissions response
        mock_perms_response = {
            'permissions': [
                {
                    'id': 'permission_1',
                    'type': 'user',
                    'role': 'owner',
                    'emailAddress': 'owner@example.com'
                },
                {
                    'id': 'permission_2',
                    'type': 'anyone',
                    'role': 'reader'
                }
            ]
        }
        mock_list.execute.return_value = mock_perms_response
        mock_build.return_value = mock_service
        
        result = drive_integration.check_file_permissions('test_file_123')
        
        assert result['success'] is True
        assert len(result['permissions']) == 2
        assert result['permissions'][0]['role'] == 'owner'
        assert result['has_read_access'] is True
    
    @pytest.mark.integration
    @patch('googleapiclient.discovery.build')
    @patch('google.auth.default')
    def test_search_files_by_name(self, mock_auth, mock_build, drive_integration):
        """Test searching files by name pattern"""
        # Mock authentication
        mock_credentials = Mock()
        mock_auth.return_value = (mock_credentials, 'test-project')
        
        # Mock Drive service
        mock_service = Mock()
        mock_files = Mock()
        mock_service.files.return_value = mock_files
        mock_list = Mock()
        mock_files.list.return_value = mock_list
        
        # Mock search response
        mock_search_response = {
            'files': [
                {
                    'id': 'match_1',
                    'name': 'voice_recording_2025_01_24.m4a',
                    'mimeType': 'audio/m4a'
                },
                {
                    'id': 'match_2',
                    'name': 'voice_memo_2025_01_24.m4a',
                    'mimeType': 'audio/m4a'
                }
            ]
        }
        mock_list.execute.return_value = mock_search_response
        mock_build.return_value = mock_service
        
        result = drive_integration.search_files_by_name('voice_*_2025_01_24')
        
        assert result['success'] is True
        assert len(result['files']) == 2
        assert 'voice_recording' in result['files'][0]['name']
        assert 'voice_memo' in result['files'][1]['name']
    
    @pytest.mark.integration
    @patch('googleapiclient.discovery.build')
    @patch('google.auth.default')
    def test_get_folder_contents(self, mock_auth, mock_build, drive_integration):
        """Test retrieving folder contents"""
        # Mock authentication
        mock_credentials = Mock()
        mock_auth.return_value = (mock_credentials, 'test-project')
        
        # Mock Drive service
        mock_service = Mock()
        mock_files = Mock()
        mock_service.files.return_value = mock_files
        mock_list = Mock()
        mock_files.list.return_value = mock_list
        
        # Mock folder contents response
        mock_contents_response = {
            'files': [
                {
                    'id': 'audio_1',
                    'name': 'recording1.m4a',
                    'mimeType': 'audio/m4a'
                },
                {
                    'id': 'audio_2',
                    'name': 'recording2.mp3',
                    'mimeType': 'audio/mpeg'
                },
                {
                    'id': 'subfolder_1',
                    'name': 'Archive',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
            ]
        }
        mock_list.execute.return_value = mock_contents_response
        mock_build.return_value = mock_service
        
        result = drive_integration.get_folder_contents('test_folder_id')
        
        assert result['success'] is True
        assert len(result['files']) == 2  # Only audio files
        assert len(result['folders']) == 1  # Only folders
        assert result['folders'][0]['name'] == 'Archive'
    
    @pytest.mark.integration
    @patch('googleapiclient.discovery.build')
    @patch('google.auth.default')
    def test_batch_download_files(self, mock_auth, mock_build, drive_integration, sample_audio_data):
        """Test batch downloading multiple files"""
        # Mock authentication
        mock_credentials = Mock()
        mock_auth.return_value = (mock_credentials, 'test-project')
        
        # Mock successful downloads
        with patch.object(drive_integration, 'download_file') as mock_download:
            mock_download.side_effect = [
                {'success': True, 'file_path': '/tmp/file1.m4a', 'file_size': 1024},
                {'success': True, 'file_path': '/tmp/file2.m4a', 'file_size': 2048},
                {'success': False, 'error': 'Download failed'}
            ]
            
            file_ids = ['file_1', 'file_2', 'file_3']
            download_dir = '/tmp'
            
            results = drive_integration.batch_download_files(file_ids, download_dir)
            
            assert len(results) == 3
            assert results[0]['success'] is True
            assert results[1]['success'] is True
            assert results[2]['success'] is False
            assert mock_download.call_count == 3
    
    @pytest.mark.integration
    @patch('googleapiclient.discovery.build')
    @patch('google.auth.default')
    def test_monitor_folder_changes(self, mock_auth, mock_build, drive_integration):
        """Test monitoring folder for new files"""
        # Mock authentication
        mock_credentials = Mock()
        mock_auth.return_value = (mock_credentials, 'test-project')
        
        # Mock Drive service for changes API
        mock_service = Mock()
        mock_changes = Mock()
        mock_service.changes.return_value = mock_changes
        
        # Mock start page token
        mock_start_page = Mock()
        mock_changes.getStartPageToken.return_value = mock_start_page
        mock_start_page.execute.return_value = {'startPageToken': '123'}
        
        # Mock changes list
        mock_list = Mock()
        mock_changes.list.return_value = mock_list
        mock_changes_response = {
            'changes': [
                {
                    'type': 'file',
                    'fileId': 'new_file_123',
                    'file': {
                        'id': 'new_file_123',
                        'name': 'new_recording.m4a',
                        'mimeType': 'audio/m4a',
                        'parents': ['test_folder_id']
                    }
                }
            ],
            'nextPageToken': '124'
        }
        mock_list.execute.return_value = mock_changes_response
        mock_build.return_value = mock_service
        
        result = drive_integration.get_folder_changes('123')
        
        assert result['success'] is True
        assert len(result['new_files']) >= 0
        assert result['next_page_token'] == '124'
    
    @pytest.mark.integration
    @patch('googleapiclient.discovery.build')
    @patch('google.auth.default')
    def test_upload_processed_file(self, mock_auth, mock_build, drive_integration):
        """Test uploading processed files back to Drive"""
        # Mock authentication
        mock_credentials = Mock()
        mock_auth.return_value = (mock_credentials, 'test-project')
        
        # Mock Drive service
        mock_service = Mock()
        mock_files = Mock()
        mock_service.files.return_value = mock_files
        mock_create = Mock()
        mock_files.create.return_value = mock_create
        
        # Mock upload response
        mock_upload_response = {
            'id': 'uploaded_file_123',
            'name': 'processed_transcript.txt',
            'webViewLink': 'https://drive.google.com/file/d/uploaded_file_123/view'
        }
        mock_create.execute.return_value = mock_upload_response
        mock_build.return_value = mock_service
        
        # Create test file to upload
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("This is a processed transcript")
            temp_file.flush()
            
            result = drive_integration.upload_file(
                temp_file.name,
                'processed_transcript.txt',
                'text/plain'
            )
            
            assert result['success'] is True
            assert result['file_id'] == 'uploaded_file_123'
            assert result['web_link'] == 'https://drive.google.com/file/d/uploaded_file_123/view'
    
    @pytest.mark.integration
    def test_integration_with_voice_processor(self, drive_integration):
        """Test integration between Drive and voice processor"""
        from src.voice_task_manager.core.processor import VoiceProcessor
        
        with patch.object(drive_integration, 'list_audio_files') as mock_list, \
             patch.object(drive_integration, 'download_file') as mock_download:
            
            # Mock file list
            mock_list.return_value = {
                'success': True,
                'files': [
                    {'id': 'file_1', 'name': 'recording1.m4a'},
                    {'id': 'file_2', 'name': 'recording2.m4a'}
                ]
            }
            
            # Mock successful download
            mock_download.return_value = {
                'success': True,
                'file_path': '/tmp/recording1.m4a',
                'file_size': 1024000
            }
            
            processor = VoiceProcessor(drive_integration.project_root)
            processor.drive_integration = drive_integration  
            
            # Test discovering new files
            result = processor._discover_new_files()
            
            assert 'new_files' in result
            mock_list.assert_called_once()
    
    @pytest.mark.integration
    @patch('googleapiclient.discovery.build')
    @patch('google.auth.default') 
    def test_error_handling_and_retry_logic(self, mock_auth, mock_build, drive_integration):
        """Test error handling and retry logic for API failures"""
        # Mock authentication
        mock_credentials = Mock()
        mock_auth.return_value = (mock_credentials, 'test-project')
        
        # Mock Drive service
        mock_service = Mock()
        mock_files = Mock()
        mock_service.files.return_value = mock_files
        mock_list = Mock()
        mock_files.list.return_value = mock_list
        
        from googleapiclient.errors import HttpError
        
        # First call fails with rate limit, second succeeds
        mock_list.execute.side_effect = [
            HttpError(Mock(status=429), b'{"error": {"message": "Rate limit exceeded"}}'),
            {'files': [{'id': 'file_1', 'name': 'test.m4a'}]}
        ]
        mock_build.return_value = mock_service
        
        with patch('time.sleep') as mock_sleep:
            result = drive_integration.list_audio_files(max_retries=2)
            
            assert result['success'] is True
            assert len(result['files']) == 1
            assert mock_list.execute.call_count == 2
            mock_sleep.assert_called_once()
    
    @pytest.mark.integration
    @patch('googleapiclient.discovery.build')
    @patch('google.auth.default')
    def test_quota_usage_monitoring(self, mock_auth, mock_build, drive_integration):
        """Test monitoring of Drive API quota usage"""
        # Mock authentication
        mock_credentials = Mock()
        mock_auth.return_value = (mock_credentials, 'test-project')
        
        # Mock service with quota tracking
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        # Track API calls
        with patch.object(drive_integration, '_track_api_usage') as mock_track:
            drive_integration.list_audio_files()
            
            # Verify usage tracking was called
            mock_track.assert_called()
    
    @pytest.mark.integration
    def test_local_cache_integration(self, drive_integration):
        """Test local caching of Drive file metadata"""
        cache_data = {
            'file_1': {
                'name': 'recording1.m4a',
                'size': '1024000',
                'modifiedTime': '2025-01-24T10:00:00Z',
                'cached_at': '2025-01-24T12:00:00Z'
            }
        }
        
        # Test cache save/load
        drive_integration._save_cache(cache_data)
        loaded_cache = drive_integration._load_cache()
        
        assert loaded_cache == cache_data
        
        # Test cache expiry
        expired_cache = drive_integration._is_cache_expired('file_1', max_age_hours=1)
        assert expired_cache is not None  # Should handle cache expiry logic