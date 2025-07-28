"""
Task Data Model
Represents a Notion task created from voice recordings.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class NotionTask:
    """
    Data model for Notion tasks created from voice recordings
    
    Attributes:
        task_id: Notion page ID
        title: Task title
        content: Full task content
        status: Task status in Notion (e.g., 'Inbox', 'In Progress', 'Done')
        contexts: List of context tags
        created_at: When the task was created
        updated_at: When the task was last updated
        url: URL to the Notion page
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
    url: Optional[str] = None
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
                         task_id: str, url: str) -> 'NotionTask':
        """
        Create a NotionTask from a voice recording
        
        Args:
            voice_file_id: ID of the source voice file
            transcript: Transcribed text
            task_id: Notion page ID
            url: URL to the Notion page
            
        Returns:
            NotionTask instance
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
            url=url,
            contexts=['voice', 'auto-processed']
        )
    
    def to_notion_data(self) -> Dict[str, Any]:
        """
        Convert to Notion API format for creating/updating pages
        
        Returns:
            Dictionary formatted for Notion API
        """
        return {
            "properties": {
                "Name": {
                    "title": [{"text": {"content": self.title}}]
                },
                "Status": {
                    "status": {"name": self.status}
                },
                "Contexts": {
                    "multi_select": [{"name": context} for context in self.contexts]
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": self.content}}]
                    }
                }
            ] if len(self.content) > 100 else []
        }
    
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
    def from_dict(cls, data: Dict[str, Any]) -> 'NotionTask':
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
    
    @classmethod
    def from_notion_response(cls, response_data: Dict[str, Any], 
                           voice_file_id: Optional[str] = None) -> 'NotionTask':
        """
        Create instance from Notion API response
        
        Args:
            response_data: Raw response from Notion API
            voice_file_id: Associated voice file ID (if known)
            
        Returns:
            NotionTask instance
        """
        properties = response_data.get('properties', {})
        
        # Extract title
        title_prop = properties.get('Name', {}).get('title', [])
        title = title_prop[0]['text']['content'] if title_prop else 'Untitled'
        
        # Extract status
        status_prop = properties.get('Status', {}).get('status')
        status = status_prop['name'] if status_prop else 'Inbox'
        
        # Extract contexts
        contexts_prop = properties.get('Contexts', {}).get('multi_select', [])
        contexts = [ctx['name'] for ctx in contexts_prop]
        
        # Extract timestamps
        created_time = response_data.get('created_time')
        last_edited_time = response_data.get('last_edited_time')
        
        created_at = datetime.fromisoformat(created_time.replace('Z', '+00:00')) if created_time else datetime.now()
        updated_at = datetime.fromisoformat(last_edited_time.replace('Z', '+00:00')) if last_edited_time else None
        
        return cls(
            task_id=response_data['id'],
            title=title,
            content='',  # Content would need separate API call to get blocks
            status=status,
            contexts=contexts,
            created_at=created_at,
            updated_at=updated_at,
            url=response_data.get('url'),
            voice_file_id=voice_file_id
        )
    
    def __str__(self) -> str:
        """String representation"""
        status_emoji = {
            'inbox': '📥',
            'in progress': '⚙️',
            'done': '✅'
        }
        emoji = status_emoji.get(self.status.lower(), '📋')
        
        return f"{emoji} NotionTask({self.title[:30]}..., {self.status})"
    
    def __repr__(self) -> str:
        """Detailed representation"""
        return (f"NotionTask(task_id='{self.task_id}', title='{self.title[:30]}...', "
                f"status='{self.status}', contexts={self.contexts})")