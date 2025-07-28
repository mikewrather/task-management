"""
OpenAI Whisper Integration
Enhanced audio transcription using OpenAI's Whisper API.
"""

import requests
import os
from typing import Optional, Dict, Any, Tuple
from ..models.voice_file import VoiceFile
from ..utils.logging import VoiceLogger

class WhisperClient:
    """Enhanced OpenAI Whisper API client for audio transcription"""
    
    def __init__(self, api_key: Optional[str] = None, logger: Optional[VoiceLogger] = None):
        """
        Initialize Whisper client
        
        Args:
            api_key: OpenAI API key (from environment if None)
            logger: Logger instance for consistent logging
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.logger = logger or VoiceLogger()
        self.base_url = 'https://api.openai.com/v1/audio/transcriptions'
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}'
        })
    
    def transcribe(self, voice_file: VoiceFile, audio_content: bytes) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio content using OpenAI Whisper
        
        Args:
            voice_file: VoiceFile object containing metadata
            audio_content: Raw audio file bytes
            
        Returns:
            Dictionary with transcription results, or None if failed
        """
        self.logger.info("🎙️ Starting transcription with OpenAI Whisper", file_id=voice_file.file_id)
        
        try:
            # Prepare the request
            files = {
                'file': ('audio.m4a', audio_content, voice_file.content_type or 'audio/m4a')
            }
            
            data = {
                'model': 'whisper-1',
                'response_format': 'verbose_json',
                'language': 'en'  # Can be made configurable
            }
            
            # Make the API request
            response = self.session.post(
                self.base_url,
                files=files,
                data=data,
                timeout=120  # Whisper can take time for longer audio
            )
            
            if not response.ok:
                error_details = self._parse_error_response(response)
                self.logger.error(
                    "OpenAI Whisper transcription failed",
                    file_id=voice_file.file_id,
                    status_code=response.status_code,
                    error_details=error_details
                )
                return None
            
            # Parse the response
            transcription_data = response.json()
            transcript_text = transcription_data.get('text', '').strip()
            duration = transcription_data.get('duration', 0)
            
            if not transcript_text:
                self.logger.warning(
                    "Transcription resulted in empty text",
                    file_id=voice_file.file_id,
                    duration=duration
                )
                return None
            
            # Prepare result
            result = {
                'text': transcript_text,
                'duration': duration,
                'language': transcription_data.get('language'),
                'segments': transcription_data.get('segments', []),
                'confidence': self._calculate_confidence(transcription_data),
                'word_count': len(transcript_text.split()),
                'character_count': len(transcript_text)
            }
            
            self.logger.success(
                "Transcription completed successfully",
                file_id=voice_file.file_id,
                transcript_length=len(transcript_text),
                duration_seconds=duration,
                word_count=result['word_count'],
                preview=transcript_text[:100] + "..." if len(transcript_text) > 100 else transcript_text
            )
            
            return result
            
        except requests.RequestException as e:
            self.logger.error(
                "Network error during Whisper API request",
                exception=e,
                file_id=voice_file.file_id
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error during transcription",
                exception=e,
                file_id=voice_file.file_id
            )
            return None
    
    def transcribe_with_retry(self, voice_file: VoiceFile, audio_content: bytes, 
                             max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Transcribe with automatic retry on transient failures
        
        Args:
            voice_file: VoiceFile object containing metadata
            audio_content: Raw audio file bytes
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with transcription results, or None if all attempts failed
        """
        for attempt in range(max_retries + 1):
            if attempt > 0:
                self.logger.info(
                    f"Retrying transcription (attempt {attempt + 1}/{max_retries + 1})",
                    file_id=voice_file.file_id
                )
            
            result = self.transcribe(voice_file, audio_content)
            
            if result:
                return result
            
            # Don't retry on the last attempt
            if attempt < max_retries:
                import time
                # Exponential backoff: 2^attempt seconds
                delay = 2 ** attempt
                self.logger.debug(f"Waiting {delay} seconds before retry", file_id=voice_file.file_id)
                time.sleep(delay)
        
        self.logger.error(
            f"Transcription failed after {max_retries + 1} attempts",
            file_id=voice_file.file_id
        )
        return None
    
    def _parse_error_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse error response from OpenAI API"""
        try:
            error_data = response.json()
            error_info = error_data.get('error', {})
            
            return {
                'type': error_info.get('type'),
                'code': error_info.get('code'),
                'message': error_info.get('message'),
                'param': error_info.get('param')
            }
        except:
            return {
                'type': 'unknown',
                'message': response.text,
                'status_code': response.status_code
            }
    
    def _calculate_confidence(self, transcription_data: Dict[str, Any]) -> Optional[float]:
        """
        Calculate overall confidence score from segment data
        
        Args:
            transcription_data: Full transcription response from Whisper
            
        Returns:
            Average confidence score, or None if not available
        """
        segments = transcription_data.get('segments', [])
        if not segments:
            return None
        
        # Whisper doesn't always provide confidence scores
        # This is a placeholder for when they do
        confidences = []
        for segment in segments:
            if 'confidence' in segment:
                confidences.append(segment['confidence'])
        
        if confidences:
            return sum(confidences) / len(confidences)
        
        return None
    
    def validate_audio_format(self, voice_file: VoiceFile) -> Tuple[bool, str]:
        """
        Validate if audio format is supported by Whisper
        
        Args:
            voice_file: VoiceFile to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        # Whisper supports various formats
        supported_types = [
            'audio/mpeg', 'audio/mp3',
            'audio/mp4', 'audio/m4a', 'audio/aac',
            'audio/wav', 'audio/wave',
            'audio/ogg', 'audio/webm',
            'audio/flac'
        ]
        
        content_type = voice_file.content_type or ''
        
        # Check MIME type
        if any(supported in content_type.lower() for supported in supported_types):
            return True, "Audio format is supported"
        
        # Check file size (Whisper has a 25MB limit)
        if voice_file.file_size and voice_file.file_size > 25 * 1024 * 1024:
            return False, f"File too large: {voice_file.file_size_mb}MB (limit: 25MB)"
        
        # If content type is unclear but file size is reasonable, assume it's okay
        if not content_type and voice_file.file_size and voice_file.file_size > 1000:
            return True, "Unknown format but size suggests audio file"
        
        return False, f"Unsupported audio format: {content_type}"
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """Get information about supported audio formats"""
        return {
            'formats': [
                'mp3', 'm4a', 'wav', 'webm', 'mp4', 'mpeg', 'mpga', 'ogg', 'flac'
            ],
            'max_file_size_mb': 25,
            'max_duration_minutes': None,  # No official limit mentioned
            'supported_languages': 'auto-detect or specify ISO 639-1 code'
        }
    
    def estimate_cost(self, duration_seconds: float) -> Dict[str, Any]:
        """
        Estimate transcription cost
        
        Args:
            duration_seconds: Audio duration in seconds
            
        Returns:
            Dictionary with cost information
        """
        # As of 2024, Whisper API costs $0.006 per minute
        cost_per_minute = 0.006
        duration_minutes = duration_seconds / 60
        estimated_cost = duration_minutes * cost_per_minute
        
        return {
            'duration_seconds': duration_seconds,
            'duration_minutes': round(duration_minutes, 2),
            'cost_per_minute': cost_per_minute,
            'estimated_cost_usd': round(estimated_cost, 4),
            'currency': 'USD'
        }