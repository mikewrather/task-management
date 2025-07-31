"""
Google Drive Integration
Enhanced Google Drive file detection and management for voice recordings.
"""

import requests
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from ..models.voice_file import VoiceFile
from ..utils.logging import VoiceLogger

class GoogleDriveClient:
    """Enhanced Google Drive integration for voice file management"""
    
    def __init__(self, folder_id: Optional[str] = None, logger: Optional[VoiceLogger] = None):
        """
        Initialize Google Drive client
        
        Args:
            folder_id: Google Drive folder ID (from environment if None)
            logger: Logger instance for consistent logging
        """
        import os
        self.folder_id = folder_id or os.getenv('GOOGLE_DRIVE_FOLDER_ID', '1vUNQV617t5mXHtyYrGro6Q3K-6JCmuUj')
        self.logger = logger or VoiceLogger()
        self.folder_url = f"https://drive.google.com/drive/folders/{self.folder_id}"
        self.session = requests.Session()
        self.session.timeout = 30
    
    def scan_folder(self) -> List[VoiceFile]:
        """
        Scan Google Drive folder for audio files
        
        Returns:
            List of VoiceFile objects for discovered audio files
        """
        self.logger.info("🔍 Scanning Google Drive folder", folder_id=self.folder_id)
        
        try:
            response = self.session.get(self.folder_url)
            if not response.ok:
                self.logger.warning(
                    "Failed to access Google Drive folder", 
                    status_code=response.status_code, 
                    folder_id=self.folder_id
                )
                return []
            
            html = response.text
            
            # Extract potential file IDs from the folder HTML
            potential_ids = self._extract_file_ids(html)
            self.logger.debug(f"Found {len(potential_ids)} potential file IDs to validate")
            
            # Validate which IDs are actually audio files
            voice_files = []
            for file_id in potential_ids:
                voice_file = self._validate_audio_file(file_id)
                if voice_file:
                    voice_files.append(voice_file)
            
            self.logger.info(f"📁 Discovered {len(voice_files)} audio files", count=len(voice_files))
            return voice_files
            
        except Exception as e:
            self.logger.error("Error scanning Google Drive folder", exception=e, folder_id=self.folder_id)
            return []
    
    def _extract_file_ids(self, html: str) -> List[str]:
        """Extract potential Google Drive file IDs from folder HTML"""
        # Enhanced pattern to find file IDs in Google Drive HTML
        all_ids = re.findall(r'\"([a-zA-Z0-9_-]{28,33})\"', html)
        
        # Filter out the folder ID and other non-file IDs
        potential_ids = [id for id in set(all_ids) if id != self.folder_id]
        
        return potential_ids
    
    def _validate_audio_file(self, file_id: str) -> Optional[VoiceFile]:
        """
        Validate if a file ID represents an audio file
        
        Args:
            file_id: Google Drive file ID to validate
            
        Returns:
            VoiceFile object if valid audio file, None otherwise
        """
        try:
            # Quick HEAD request to check if it's an audio file
            test_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            test_response = self.session.head(test_url, timeout=5, allow_redirects=True)
            
            if test_response.ok:
                content_type = test_response.headers.get('content-type', '')
                content_length = int(test_response.headers.get('content-length', '0'))
                
                # Check if it's an audio file or large enough to be audio
                if self._is_audio_file(content_type, content_length):
                    voice_file = VoiceFile(
                        file_id=file_id,
                        file_size=content_length,
                        content_type=content_type,
                        status='discovered'
                    )
                    
                    self.logger.debug(
                        f"Validated audio file: {file_id}",
                        content_type=content_type,
                        size_bytes=content_length
                    )
                    
                    return voice_file
                
        except Exception as e:
            self.logger.debug(f"Failed to validate file {file_id}: {e}")
        
        return None
    
    def _is_audio_file(self, content_type: str, content_length: int) -> bool:
        """
        Determine if file is likely an audio file
        
        Args:
            content_type: HTTP Content-Type header
            content_length: File size in bytes
            
        Returns:
            True if likely an audio file
        """
        # Check MIME type
        if 'audio' in content_type.lower():
            return True
        
        # Check for common audio file extensions in content type
        audio_types = ['m4a', 'mp3', 'wav', 'aac', 'ogg', 'flac']
        if any(audio_type in content_type.lower() for audio_type in audio_types):
            return True
        
        # If no clear content type, assume files > 50KB might be audio
        # (this is a heuristic for Apple Watch voice recordings)
        if content_length > 50000:
            return True
        
        return False
    
    def download_file(self, voice_file: VoiceFile) -> Optional[bytes]:
        """
        Download audio file content
        
        Args:
            voice_file: VoiceFile object to download
            
        Returns:
            File content as bytes, or None if download failed
        """
        self.logger.info("📥 Downloading audio file", file_id=voice_file.file_id)
        
        try:
            download_url = voice_file.download_url
            response = self.session.get(download_url, timeout=60)
            
            if not response.ok:
                self.logger.error(
                    "Failed to download audio file from Google Drive",
                    file_id=voice_file.file_id,
                    status_code=response.status_code
                )
                return None
            
            # Update file metadata with actual download info
            content_type = response.headers.get('content-type', '')
            content_size = len(response.content)
            
            # Validate audio content
            if not self._is_audio_file(content_type, content_size):
                self.logger.warning(
                    "Downloaded file doesn't appear to be valid audio content",
                    file_id=voice_file.file_id,
                    content_type=content_type,
                    size_bytes=content_size
                )
                return None
            
            # Update voice file metadata
            voice_file.content_type = content_type
            voice_file.file_size = content_size
            
            self.logger.success(
                "Audio file downloaded successfully",
                file_id=voice_file.file_id,
                size_bytes=content_size
            )
            
            return response.content
            
        except Exception as e:
            self.logger.error(
                "Unexpected error during audio file download",
                exception=e,
                file_id=voice_file.file_id
            )
            return None
    
    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """
        Get file metadata without downloading the full file
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            Dictionary with file metadata
        """
        try:
            test_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            response = self.session.head(test_url, timeout=10, allow_redirects=True)
            
            if response.ok:
                return {
                    'file_id': file_id,
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': int(response.headers.get('content-length', '0')),
                    'last_modified': response.headers.get('last-modified'),
                    'url': test_url,
                    'accessible': True
                }
            else:
                return {
                    'file_id': file_id,
                    'accessible': False,
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                'file_id': file_id,
                'accessible': False,
                'error': str(e)
            }
    
    def cleanup_processed_file(self, voice_file: VoiceFile, cleanup_method: str = 'track') -> bool:
        """
        Handle cleanup of processed voice files
        
        This method currently tracks cleanup intent for manual management.
        Future versions will integrate with Google Drive API for automated cleanup.
        
        Args:
            voice_file: VoiceFile that has been processed
            cleanup_method: Method to use ('track', 'rename', 'move', 'delete')
            
        Returns:
            True if cleanup tracking was successful
        """
        import os
        
        # Check if cleanup functionality is enabled
        cleanup_enabled = os.getenv('CLEANUP_PROCESSED_FILES', 'false').lower() in ('true', '1', 'yes')
        
        if not cleanup_enabled:
            self.logger.debug(
                "File cleanup disabled - set CLEANUP_PROCESSED_FILES=true to enable",
                file_id=voice_file.file_id
            )
            return False
        
        try:
            # Log cleanup intent for tracking and manual management
            self.logger.info(
                "🧹 Tracking file for cleanup",
                file_id=voice_file.file_id,
                cleanup_method=cleanup_method,
                management_tool="vtm cleanup command"
            )
            
            # Current implementation: Move local downloaded files
            cleanup_timestamp = voice_file.processed_at or voice_file.discovered_at
            
            # Check if we have a local recordings directory
            import pathlib
            recordings_dir = pathlib.Path.home() / "recordings"
            processed_dir = recordings_dir / "processed"
            
            if recordings_dir.exists() and cleanup_method == 'move':
                # Create processed directory if it doesn't exist
                processed_dir.mkdir(exist_ok=True)
                
                # Look for the audio file in recordings directory
                # Try to find file by partial match (file_id might be in the filename)
                potential_files = []
                for file in recordings_dir.glob("*.m4a"):
                    if voice_file.file_id in str(file):
                        potential_files.append(file)
                
                # Also check for files by timestamp if available
                if voice_file.discovered_at:
                    timestamp_str = voice_file.discovered_at.strftime("%Y-%m-%d")
                    for file in recordings_dir.glob(f"*{timestamp_str}*.m4a"):
                        if file not in potential_files:
                            potential_files.append(file)
                
                # Move the files
                moved_files = []
                for file in potential_files:
                    try:
                        new_path = processed_dir / file.name
                        # Add timestamp prefix if not already present
                        if not new_path.name.startswith("PROCESSED_"):
                            timestamp_prefix = cleanup_timestamp.strftime("%Y%m%d_%H%M%S")
                            new_path = processed_dir / f"PROCESSED_{timestamp_prefix}_{file.name}"
                        
                        # Move the file
                        import shutil
                        shutil.move(str(file), str(new_path))
                        moved_files.append(new_path.name)
                        
                        self.logger.info(
                            f"✅ Moved file to processed folder",
                            original_file=file.name,
                            new_location=new_path.name
                        )
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to move file {file.name}",
                            exception=e
                        )
                
                if moved_files:
                    self.logger.success(
                        f"🧹 Cleanup completed - moved {len(moved_files)} file(s)",
                        file_id=voice_file.file_id,
                        files=moved_files
                    )
                else:
                    self.logger.debug(
                        "No local files found to move",
                        file_id=voice_file.file_id,
                        recordings_dir=str(recordings_dir)
                    )
            
            # Always track in logs for reference
            self.logger.debug(
                "File marked for cleanup tracking",
                file_id=voice_file.file_id,
                cleanup_timestamp=cleanup_timestamp.isoformat(),
                google_drive_url=voice_file.google_drive_url
            )
            
            return True
            
        except Exception as e:
            self.logger.warning(
                "Failed to track file for cleanup",
                exception=e,
                file_id=voice_file.file_id
            )
            return False