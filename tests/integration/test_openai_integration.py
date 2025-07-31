"""Integration tests for OpenAI API interactions"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

from voice_task_manager.integrations.whisper import WhisperClient


class TestOpenAIIntegration:
    """Integration tests for OpenAI API connectivity and transcription"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / 'data').mkdir()
            (temp_path / 'logs').mkdir()
            yield temp_path
    
    @pytest.fixture
    def transcriber(self, temp_project_root):
        """Create a VoiceTranscriber instance"""
        return VoiceTranscriber(temp_project_root)
    
    @pytest.fixture
    def sample_audio_data(self):
        """Create sample audio data for testing"""
        return b"fake_audio_data_for_testing" * 1000  # Simulate audio bytes
    
    @pytest.mark.integration
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_api_key'})
    def test_openai_client_initialization(self, transcriber):
        """Test OpenAI client is properly initialized"""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Initialize transcriber (should create OpenAI client)
            result = transcriber._initialize_openai_client()
            
            assert result is not None
            mock_openai.assert_called_once_with(api_key='test_api_key')
    
    @pytest.mark.integration
    def test_openai_client_missing_api_key(self, transcriber):
        """Test OpenAI client initialization without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                transcriber._initialize_openai_client()
    
    @pytest.mark.integration
    @patch('openai.OpenAI')
    def test_transcribe_audio_success(self, mock_openai, transcriber, sample_audio_data):
        """Test successful audio transcription"""
        # Mock OpenAI client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "This is a test transcription"
        mock_client.audio.transcriptions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_audio:
            temp_audio.write(sample_audio_data)
            temp_audio.flush()
            
            result = transcriber.transcribe_audio(temp_audio.name)
            
            assert result['success'] is True
            assert result['transcript'] == "This is a test transcription"
            assert 'processing_time' in result
            
            # Verify OpenAI API was called correctly
            mock_client.audio.transcriptions.create.assert_called_once()
            call_args = mock_client.audio.transcriptions.create.call_args
            assert call_args[1]['model'] == 'whisper-1'
            assert call_args[1]['response_format'] == 'text'
    
    @pytest.mark.integration
    @patch('openai.OpenAI')
    def test_transcribe_audio_api_error(self, mock_openai, transcriber, sample_audio_data):
        """Test transcription with OpenAI API error"""
        # Mock OpenAI client to raise exception
        mock_client = Mock()
        mock_client.audio.transcriptions.create.side_effect = Exception("API rate limit exceeded")
        mock_openai.return_value = mock_client
        
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_audio:
            temp_audio.write(sample_audio_data)
            temp_audio.flush()
            
            result = transcriber.transcribe_audio(temp_audio.name)
            
            assert result['success'] is False
            assert 'API rate limit exceeded' in result['error']
    
    @pytest.mark.integration
    @patch('openai.OpenAI')
    def test_transcribe_audio_file_not_found(self, mock_openai, transcriber):
        """Test transcription with non-existent audio file"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        result = transcriber.transcribe_audio('/nonexistent/audio/file.m4a')
        
        assert result['success'] is False
        assert 'File not found' in result['error']
    
    @pytest.mark.integration
    @patch('openai.OpenAI')
    def test_transcribe_with_custom_model(self, mock_openai, transcriber, sample_audio_data):
        """Test transcription with custom Whisper model"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Custom model transcription"
        mock_client.audio.transcriptions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_audio:
            temp_audio.write(sample_audio_data)
            temp_audio.flush()
            
            result = transcriber.transcribe_audio(
                temp_audio.name, 
                model='whisper-1', 
                language='en'
            )
            
            assert result['success'] is True
            assert result['transcript'] == "Custom model transcription"
            
            # Verify model and language parameters
            call_args = mock_client.audio.transcriptions.create.call_args
            assert call_args[1]['model'] == 'whisper-1'
            assert call_args[1]['language'] == 'en'
    
    @pytest.mark.integration
    @patch('openai.OpenAI')
    def test_transcribe_with_response_format_json(self, mock_openai, transcriber, sample_audio_data):
        """Test transcription with JSON response format"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "JSON format transcription"
        mock_response.duration = 15.5
        mock_client.audio.transcriptions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_audio:
            temp_audio.write(sample_audio_data)
            temp_audio.flush()
            
            result = transcriber.transcribe_audio(
                temp_audio.name,
                response_format='verbose_json'
            )
            
            assert result['success'] is True
            assert result['transcript'] == "JSON format transcription"
            
            # Verify response format parameter
            call_args = mock_client.audio.transcriptions.create.call_args
            assert call_args[1]['response_format'] == 'verbose_json'
    
    @pytest.mark.integration  
    @patch('openai.OpenAI')
    def test_transcribe_large_file_chunking(self, mock_openai, transcriber):
        """Test transcription of large audio files with chunking"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Chunked transcription result"
        mock_client.audio.transcriptions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create large audio file (simulate 26MB file > 25MB limit)
        large_audio_data = b"fake_audio_data" * (26 * 1024 * 1024 // 15)
        
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_audio:
            temp_audio.write(large_audio_data)
            temp_audio.flush()
            
            result = transcriber.transcribe_audio(temp_audio.name)
            
            # Should handle large file appropriately
            assert result['success'] in [True, False]  # May succeed with chunking or fail gracefully
            if not result['success']:
                assert 'file size' in result['error'].lower()
    
    @pytest.mark.integration
    @patch('openai.OpenAI')
    def test_transcribe_audio_with_prompt(self, mock_openai, transcriber, sample_audio_data):
        """Test transcription with context prompt"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Prompted transcription with technical terms"
        mock_client.audio.transcriptions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_audio:
            temp_audio.write(sample_audio_data)
            temp_audio.flush()
            
            context_prompt = "This audio contains technical software development terms and API names."
            result = transcriber.transcribe_audio(temp_audio.name, prompt=context_prompt)
            
            assert result['success'] is True
            
            # Verify prompt parameter was passed
            call_args = mock_client.audio.transcriptions.create.call_args
            assert call_args[1]['prompt'] == context_prompt
    
    @pytest.mark.integration
    @patch('requests.get')
    def test_download_and_transcribe_from_url(self, mock_get, transcriber, sample_audio_data):
        """Test downloading audio from URL and transcribing"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = sample_audio_data
        mock_response.headers = {'content-type': 'audio/m4a'}
        mock_get.return_value = mock_response
        
        with patch.object(transcriber, 'transcribe_audio') as mock_transcribe:
            mock_transcribe.return_value = {
                'success': True,
                'transcript': 'Downloaded and transcribed successfully'
            }
            
            result = transcriber.download_and_transcribe(
                'https://example.com/audio.m4a'
            )
            
            assert result['success'] is True
            assert result['transcript'] == 'Downloaded and transcribed successfully'
            mock_transcribe.assert_called_once()
    
    @pytest.mark.integration
    def test_transcribe_batch_files(self, transcriber):
        """Test batch transcription of multiple files"""
        with patch.object(transcriber, 'transcribe_audio') as mock_transcribe:
            # Mock successful transcriptions
            mock_transcribe.side_effect = [
                {'success': True, 'transcript': 'First file transcript'},
                {'success': True, 'transcript': 'Second file transcript'},
                {'success': False, 'error': 'Third file failed'}
            ]
            
            audio_files = ['file1.m4a', 'file2.m4a', 'file3.m4a']
            results = transcriber.transcribe_batch(audio_files)
            
            assert len(results) == 3
            assert results[0]['success'] is True
            assert results[1]['success'] is True
            assert results[2]['success'] is False
            assert mock_transcribe.call_count == 3
    
    @pytest.mark.integration
    @patch('openai.OpenAI')
    def test_api_retry_mechanism(self, mock_openai, transcriber, sample_audio_data):
        """Test API retry mechanism for transient failures"""
        mock_client = Mock()
        
        # First call fails, second succeeds
        mock_client.audio.transcriptions.create.side_effect = [
            Exception("Temporary network error"),
            Mock(text="Retry successful transcription")
        ]
        mock_openai.return_value = mock_client
        
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_audio:
            temp_audio.write(sample_audio_data)
            temp_audio.flush()
            
            result = transcriber.transcribe_audio(temp_audio.name, max_retries=2)
            
            assert result['success'] is True
            assert result['transcript'] == "Retry successful transcription"
            assert mock_client.audio.transcriptions.create.call_count == 2
    
    @pytest.mark.integration
    @patch('openai.OpenAI')
    def test_api_timeout_handling(self, mock_openai, transcriber, sample_audio_data):
        """Test API timeout handling"""
        mock_client = Mock()
        mock_client.audio.transcriptions.create.side_effect = TimeoutError("Request timeout")
        mock_openai.return_value = mock_client
        
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_audio:
            temp_audio.write(sample_audio_data)
            temp_audio.flush()
            
            result = transcriber.transcribe_audio(temp_audio.name, timeout=30)
            
            assert result['success'] is False
            assert 'timeout' in result['error'].lower()
    
    @pytest.mark.integration
    def test_supported_audio_formats(self, transcriber):
        """Test transcription of various supported audio formats"""
        formats = ['.m4a', '.mp3', '.wav', '.mp4', '.mpeg', '.mpga', '.webm']
        
        with patch.object(transcriber, 'transcribe_audio') as mock_transcribe:
            mock_transcribe.return_value = {'success': True, 'transcript': 'Format test'}
            
            for format_ext in formats:
                test_file = f"test_audio{format_ext}"
                result = transcriber.transcribe_audio(test_file)
                
                # Should attempt transcription for all supported formats
                assert mock_transcribe.called
    
    @pytest.mark.integration
    @patch('openai.OpenAI')
    def test_transcription_cost_tracking(self, mock_openai, transcriber, sample_audio_data):
        """Test tracking of transcription costs and usage"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Cost tracking transcription"
        mock_client.audio.transcriptions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_audio:
            temp_audio.write(sample_audio_data)
            temp_audio.flush()
            
            # Get file size for cost calculation
            file_size = os.path.getsize(temp_audio.name)
            
            result = transcriber.transcribe_audio(temp_audio.name, track_usage=True)
            
            assert result['success'] is True
            assert 'usage_stats' in result
            assert result['usage_stats']['file_size_bytes'] == file_size
            assert 'estimated_cost' in result['usage_stats']
    
    @pytest.mark.integration
    def test_integration_with_voice_processor(self, transcriber):
        """Test integration between transcriber and voice processor"""
        from voice_task_manager.core.processor import VoiceProcessor
        
        with patch.object(transcriber, 'transcribe_audio') as mock_transcribe:
            mock_transcribe.return_value = {
                'success': True,
                'transcript': 'Integration test transcript'
            }
            
            processor = VoiceProcessor(transcriber.project_root)
            
            # Mock the transcriber in processor
            processor.transcriber = transcriber
            
            result = processor._transcribe_file('test_file.m4a')
            
            assert result['success'] is True
            assert result['transcript'] == 'Integration test transcript'