"""
Voice File Data Model
Represents a voice recording file with metadata and processing state.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

@dataclass
class VoiceFile:
    """
    Data model for voice recording files
    
    Attributes:
        file_id: Google Drive file ID
        discovered_at: When the file was first discovered
        processed_at: When the file was successfully processed (None if not processed)
        status: Processing status ('discovered', 'processing', 'completed', 'failed')
        file_size: Size of the audio file in bytes
        content_type: MIME type of the file
        transcript: Transcribed text (None until processed)
        transcript_length: Length of transcript in characters
        duration_seconds: Audio duration in seconds
        task_url: URL of the created Notion task (None until processed)
        error_message: Error details if processing failed
        retry_count: Number of processing attempts
        metadata: Additional file metadata
        archive_status: Archive status ('active', 'pending_archive', 'archived')
        archived_at: When the file was archived (None if not archived)
    """
    
    file_id: str
    discovered_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    status: str = 'discovered'  # discovered, processing, completed, failed
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    transcript: Optional[str] = None
    transcript_length: Optional[int] = None
    duration_seconds: Optional[float] = None
    task_url: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    archive_status: str = 'active'  # active, pending_archive, archived
    archived_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate and normalize data after initialization"""
        if self.transcript and self.transcript_length is None:
            self.transcript_length = len(self.transcript)
    
    @property
    def is_processed(self) -> bool:
        """Check if the file has been successfully processed"""
        return self.status == 'completed' and self.processed_at is not None
    
    @property
    def is_failed(self) -> bool:
        """Check if the file processing has failed"""
        return self.status == 'failed'
    
    @property
    def is_archived(self) -> bool:
        """Check if the file has been archived"""
        return self.archive_status == 'archived'
    
    @property
    def is_pending_archive(self) -> bool:
        """Check if the file is pending archival"""
        return self.archive_status == 'pending_archive'
    
    @property
    def can_be_archived(self) -> bool:
        """Check if the file can be archived (must be completed)"""
        return self.status == 'completed' and self.archive_status == 'active'
    
    @property
    def processing_duration(self) -> Optional[float]:
        """Calculate processing duration in seconds"""
        if self.processed_at:
            return (self.processed_at - self.discovered_at).total_seconds()
        return None
    
    @property
    def file_size_mb(self) -> Optional[float]:
        """Get file size in megabytes"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return None
    
    @property
    def google_drive_url(self) -> str:
        """Generate Google Drive URL for the file"""
        return f"https://drive.google.com/file/d/{self.file_id}/view"
    
    @property
    def download_url(self) -> str:
        """Generate Google Drive download URL"""
        return f"https://drive.google.com/uc?export=download&id={self.file_id}"
    
    def mark_processing(self) -> None:
        """Mark file as currently being processed"""
        self.status = 'processing'
        self.retry_count += 1
    
    def mark_completed(self, transcript: str, task_url: str, 
                      duration_seconds: Optional[float] = None) -> None:
        """Mark file as successfully processed"""
        self.status = 'completed'
        self.processed_at = datetime.now()
        self.transcript = transcript
        self.transcript_length = len(transcript)
        self.task_url = task_url
        if duration_seconds:
            self.duration_seconds = duration_seconds
        self.error_message = None  # Clear any previous errors
    
    def mark_failed(self, error_message: str) -> None:
        """Mark file processing as failed"""
        self.status = 'failed'
        self.error_message = error_message
    
    def can_retry(self, max_retries: int = 3) -> bool:
        """Check if file can be retried for processing"""
        return self.retry_count < max_retries and self.status != 'completed'
    
    def mark_for_archive(self) -> bool:
        """
        Mark file for archival
        
        Returns:
            True if successfully marked, False if not eligible
        """
        if not self.can_be_archived:
            return False
        
        self.archive_status = 'pending_archive'
        self.archived_at = datetime.now()
        return True
    
    def mark_archived(self) -> None:
        """Mark file as successfully archived"""
        self.archive_status = 'archived'
        self.archived_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'file_id': self.file_id,
            'discovered_at': self.discovered_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'status': self.status,
            'file_size': self.file_size,
            'content_type': self.content_type,
            'transcript': self.transcript,
            'transcript_length': self.transcript_length,
            'duration_seconds': self.duration_seconds,
            'task_url': self.task_url,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'metadata': self.metadata,
            'archive_status': self.archive_status,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoiceFile':
        """Create instance from dictionary"""
        # Handle datetime parsing
        discovered_at = datetime.fromisoformat(data['discovered_at'])
        processed_at = datetime.fromisoformat(data['processed_at']) if data.get('processed_at') else None
        archived_at = datetime.fromisoformat(data['archived_at']) if data.get('archived_at') else None
        
        return cls(
            file_id=data['file_id'],
            discovered_at=discovered_at,
            processed_at=processed_at,
            status=data.get('status', 'discovered'),
            file_size=data.get('file_size'),
            content_type=data.get('content_type'),
            transcript=data.get('transcript'),
            transcript_length=data.get('transcript_length'),
            duration_seconds=data.get('duration_seconds'),
            task_url=data.get('task_url'),
            error_message=data.get('error_message'),
            retry_count=data.get('retry_count', 0),
            metadata=data.get('metadata', {}),
            archive_status=data.get('archive_status', 'active'),
            archived_at=archived_at
        )
    
    def __str__(self) -> str:
        """String representation"""
        status_emoji = {
            'discovered': '🔍',
            'processing': '⚙️',
            'completed': '✅',
            'failed': '❌'
        }
        emoji = status_emoji.get(self.status, '❓')
        
        return f"{emoji} VoiceFile({self.file_id[:8]}..., {self.status})"
    
    def __repr__(self) -> str:
        """Detailed representation"""
        return (f"VoiceFile(file_id='{self.file_id}', status='{self.status}', "
                f"discovered_at='{self.discovered_at}', processed_at='{self.processed_at}')")