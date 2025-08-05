"""
Task Data Model
Represents a task created from voice recordings in GraphRAG.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class Task:
    """
    Data model for tasks created from voice recordings
    
    Attributes:
        task_id: GraphRAG node ID  
        title: Task title
        content: Full task content
        status: Task status (e.g., 'Inbox', 'In Progress', 'Done')
        contexts: List of context tags
        created_at: When the task was created
        updated_at: When the task was last updated
        voice_file_id: ID of the source voice file
        transcript_source: Original transcript text
        metadata: Additional task metadata
    """
    
    task_id: str
    title: str
    content: str
    status: str = 'Inbox'
    contexts: List[str] = field(default_factory=lambda: ['voice', 'auto-processed'])
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    url: Optional[str] = None  # URL to task (for backward compatibility with NotionTask)
    voice_file_id: Optional[str] = None
    transcript_source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize data after initialization"""
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    @property
    def is_completed(self) -> bool:
        """Check if the task is marked as completed"""
        return self.status.lower() in ['done', 'completed', 'finished']
    
    @property
    def is_in_progress(self) -> bool:
        """Check if the task is currently in progress"""
        return self.status.lower() in ['in progress', 'doing', 'active']
    
    @property
    def is_inbox(self) -> bool:
        """Check if the task is in the inbox (not yet processed)"""
        return self.status.lower() in ['inbox', 'new', 'unprocessed']
    
    @property
    def has_voice_context(self) -> bool:
        """Check if task has voice-related context tags"""
        return 'voice' in [c.lower() for c in self.contexts]
    
    @property
    def is_auto_processed(self) -> bool:
        """Check if task was automatically created from voice recording"""
        return 'auto-processed' in [c.lower() for c in self.contexts]
    
    @property
    def age_hours(self) -> float:
        """Get task age in hours"""
        return (datetime.now() - self.created_at).total_seconds() / 3600
    
    @property
    def age_days(self) -> float:
        """Get task age in days"""
        return self.age_hours / 24
    
    def update_status(self, new_status: str) -> None:
        """Update task status and timestamp"""
        self.status = new_status
        self.updated_at = datetime.now()
    
    def add_context(self, context: str) -> None:
        """Add a context tag if not already present"""
        if context not in self.contexts:
            self.contexts.append(context)
            self.updated_at = datetime.now()
    
    def remove_context(self, context: str) -> None:
        """Remove a context tag if present"""
        if context in self.contexts:
            self.contexts.remove(context)
            self.updated_at = datetime.now()
    
    def update_content(self, new_content: str) -> None:
        """Update task content and timestamp"""
        self.content = new_content
        self.updated_at = datetime.now()
    
    @classmethod
    def create_from_voice(cls, voice_file_id: str, transcript: str, 
                         task_id: str) -> 'Task':
        """
        Create a Task from a voice recording
        
        Args:
            voice_file_id: ID of the source voice file
            transcript: Transcribed text
            task_id: GraphRAG node ID
            
        Returns:
            Task instance
        """
        # Create concise title from transcript
        title_text = transcript[:60] + "..." if len(transcript) > 60 else transcript
        title = f"Voice Note: {title_text}"
        
        # Use full transcript as content
        content = f"Full transcript: {transcript}"
        
        return cls(
            task_id=task_id,  
            title=title,
            content=content,
            voice_file_id=voice_file_id,
            transcript_source=transcript,
            contexts=['voice', 'auto-processed']
        )
    
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'task_id': self.task_id,
            'title': self.title,
            'content': self.content,
            'status': self.status,
            'contexts': self.contexts,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'url': self.url,
            'voice_file_id': self.voice_file_id,
            'transcript_source': self.transcript_source,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create instance from dictionary"""
        # Handle datetime parsing
        created_at = datetime.fromisoformat(data['created_at'])
        updated_at = datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        
        return cls(
            task_id=data['task_id'],
            title=data['title'],
            content=data['content'],
            status=data.get('status', 'Inbox'),
            contexts=data.get('contexts', ['voice', 'auto-processed']),
            created_at=created_at,
            updated_at=updated_at,
            url=data.get('url'),
            voice_file_id=data.get('voice_file_id'),
            transcript_source=data.get('transcript_source'),
            metadata=data.get('metadata', {})
        )
    
    
    def __str__(self) -> str:
        """String representation"""
        status_emoji = {
            'inbox': '📥',
            'in progress': '⚙️',
            'done': '✅'
        }
        emoji = status_emoji.get(self.status.lower(), '📋')
        
        return f"{emoji} Task({self.title[:30]}..., {self.status})"
    
    def __repr__(self) -> str:
        """Detailed representation"""
        return (f"Task(task_id='{self.task_id}', title='{self.title[:30]}...', "
                f"status='{self.status}', contexts={self.contexts})")