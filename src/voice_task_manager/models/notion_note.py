"""
Notion Note Data Model

Represents a note from the Notion Notes database for knowledge management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from .notion_project import Priority, DateRange


class NoteStatus(Enum):
    """Valid note status values from Notion database"""
    DRAFT = "Draft"
    IN_REVIEW = "In Review"
    PUBLISHED = "Published"
    ARCHIVED = "Archived"


class NoteType(Enum):
    """Types of notes"""
    MEETING = "Meeting"
    RESEARCH = "Research"
    IDEA = "Idea"
    REFERENCE = "Reference"
    JOURNAL = "Journal"
    TEMPLATE = "Template"


@dataclass
class NotionNote:
    """
    Notion Note data model
    
    Represents a note from the Notes database (eb339471-752a-4090-b93e-39079a661098)
    for knowledge management and information capture.
    """
    
    # Core identification
    note_id: str
    title: str
    content: str = ""
    summary: str = ""
    
    # Classification
    status: str = NoteStatus.DRAFT.value
    note_type: str = NoteType.IDEA.value
    priority: str = Priority.LOW.value
    
    # Relationships
    project_id: Optional[str] = None
    area_id: Optional[str] = None
    goal_id: Optional[str] = None
    meeting_id: Optional[str] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    source_url: Optional[str] = None
    author: Optional[str] = None
    
    # System properties
    created_time: datetime = field(default_factory=datetime.now)
    last_edited_time: Optional[datetime] = None
    published_date: Optional[datetime] = None
    archive: bool = False
    
    # Computed properties
    word_count: int = 0
    reading_time_minutes: int = 0
    
    @classmethod
    def from_notion_data(cls, notion_data: Dict[str, Any]) -> 'NotionNote':
        """
        Create NotionNote from Notion API response data
        
        Args:
            notion_data: Raw data from Notion API
            
        Returns:
            NotionNote instance
        """
        properties = notion_data.get('properties', {})
        
        # Extract basic fields
        note_id = notion_data.get('id', '')
        title = cls._extract_title(properties.get('Title', {}) or properties.get('Name', {}))
        content = cls._extract_rich_text(properties.get('Content', {}))
        summary = cls._extract_rich_text(properties.get('Summary', {}))
        
        # Extract classification
        status = cls._extract_select(properties.get('Status', {}))
        note_type = cls._extract_select(properties.get('Type', {}))
        priority = cls._extract_select(properties.get('Priority', {}))
        
        # Extract dates
        created_time = cls._extract_created_time(properties.get('Created', {}))
        last_edited_time = cls._extract_last_edited_time(properties.get('Edited', {}))
        published_date = cls._extract_date(properties.get('Published Date', {}))
        
        # Extract relationships
        project_id = cls._extract_relation_id(properties.get('Project', {}))
        area_id = cls._extract_relation_id(properties.get('Area', {}))
        goal_id = cls._extract_relation_id(properties.get('Goal', {}))
        meeting_id = cls._extract_relation_id(properties.get('Meeting', {}))
        
        # Extract metadata
        tags = cls._extract_multi_select(properties.get('Tags', {}))
        source_url = cls._extract_url(properties.get('Source URL', {}))
        author = cls._extract_rich_text(properties.get('Author', {}))
        
        # Extract computed properties
        word_count = cls._extract_number(properties.get('Word Count', {})) or 0
        reading_time_minutes = cls._extract_number(properties.get('Reading Time', {})) or 0
        
        # Extract checkbox
        archive = cls._extract_checkbox(properties.get('Archive', {}))
        
        return cls(
            note_id=note_id,
            title=title,
            content=content,
            summary=summary,
            status=status,
            note_type=note_type,
            priority=priority,
            project_id=project_id,
            area_id=area_id,
            goal_id=goal_id,
            meeting_id=meeting_id,
            tags=tags,
            source_url=source_url,
            author=author,
            created_time=created_time,
            last_edited_time=last_edited_time,
            published_date=published_date,
            archive=archive,
            word_count=int(word_count),
            reading_time_minutes=int(reading_time_minutes)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'note_id': self.note_id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'status': self.status,
            'note_type': self.note_type,
            'priority': self.priority,
            'project_id': self.project_id,
            'area_id': self.area_id,
            'goal_id': self.goal_id,
            'meeting_id': self.meeting_id,
            'tags': self.tags,
            'source_url': self.source_url,
            'author': self.author,
            'created_time': self.created_time.isoformat(),
            'last_edited_time': self.last_edited_time.isoformat() if self.last_edited_time else None,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'archive': self.archive,
            'word_count': self.word_count,
            'reading_time_minutes': self.reading_time_minutes
        }
    
    def is_published(self) -> bool:
        """Check if note is published"""
        return self.status == NoteStatus.PUBLISHED.value
    
    def is_draft(self) -> bool:
        """Check if note is still in draft status"""
        return self.status == NoteStatus.DRAFT.value
    
    def is_archived(self) -> bool:
        """Check if note is archived"""
        return self.status == NoteStatus.ARCHIVED.value or self.archive
    
    def calculate_reading_time(self) -> int:
        """Calculate estimated reading time in minutes based on word count"""
        if not self.word_count:
            # Estimate word count from content if not provided
            word_count = len(self.content.split()) if self.content else 0
        else:
            word_count = self.word_count
        
        # Average reading speed: 200-250 words per minute
        return max(1, word_count // 225)
    
    def add_tag(self, tag: str) -> None:
        """Add a tag if not already present"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.last_edited_time = datetime.now()
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag if present"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.last_edited_time = datetime.now()
    
    def publish(self) -> None:
        """Publish the note"""
        self.status = NoteStatus.PUBLISHED.value
        self.published_date = datetime.now()
        self.last_edited_time = datetime.now()
    
    @staticmethod
    def _extract_title(title_property: Dict[str, Any]) -> str:
        """Extract title from Notion title property"""
        title_list = title_property.get('title', [])
        if title_list:
            return title_list[0].get('plain_text', '')
        return ''
    
    @staticmethod
    def _extract_rich_text(rich_text_property: Dict[str, Any]) -> str:
        """Extract rich text from Notion rich_text property"""
        rich_text_list = rich_text_property.get('rich_text', [])
        if rich_text_list:
            return ''.join([item.get('plain_text', '') for item in rich_text_list])
        return ''
    
    @staticmethod
    def _extract_select(select_property: Dict[str, Any]) -> str:
        """Extract select value from Notion select property"""
        select_data = select_property.get('select', {})
        return select_data.get('name', '') if select_data else ''
    
    @staticmethod
    def _extract_multi_select(multi_select_property: Dict[str, Any]) -> List[str]:
        """Extract multi-select values from Notion multi_select property"""
        multi_select_list = multi_select_property.get('multi_select', [])
        return [item.get('name', '') for item in multi_select_list]
    
    @staticmethod
    def _extract_url(url_property: Dict[str, Any]) -> Optional[str]:
        """Extract URL from Notion url property"""
        return url_property.get('url')
    
    @staticmethod
    def _extract_number(number_property: Dict[str, Any]) -> Optional[float]:
        """Extract number from Notion number property"""
        return number_property.get('number')
    
    @staticmethod
    def _extract_created_time(created_property: Dict[str, Any]) -> datetime:
        """Extract created time from Notion created_time property"""
        created_str = created_property.get('created_time', '')
        if created_str:
            return datetime.fromisoformat(created_str.replace('Z', '+00:00'))
        return datetime.now()
    
    @staticmethod
    def _extract_last_edited_time(edited_property: Dict[str, Any]) -> Optional[datetime]:
        """Extract last edited time from Notion last_edited_time property"""
        edited_str = edited_property.get('last_edited_time', '')
        if edited_str:
            return datetime.fromisoformat(edited_str.replace('Z', '+00:00'))
        return None
    
    @staticmethod
    def _extract_date(date_property: Dict[str, Any]) -> Optional[datetime]:
        """Extract date from Notion date property"""
        date_data = date_property.get('date', {})
        if date_data and date_data.get('start'):
            return datetime.fromisoformat(date_data['start'].replace('Z', '+00:00'))
        return None
    
    @staticmethod
    def _extract_relation_id(relation_property: Dict[str, Any]) -> Optional[str]:
        """Extract first relation ID from Notion relation property"""
        relation_list = relation_property.get('relation', [])
        if relation_list:
            return relation_list[0].get('id')
        return None
    
    @staticmethod
    def _extract_checkbox(checkbox_property: Dict[str, Any]) -> bool:
        """Extract checkbox value from Notion checkbox property"""
        return checkbox_property.get('checkbox', False)