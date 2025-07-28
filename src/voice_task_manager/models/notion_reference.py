"""
Notion Reference Data Model

Represents a reference/resource from the Notion References database for knowledge linking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from .notion_project import Priority


class ReferenceType(Enum):
    """Types of references"""
    ARTICLE = "Article"
    BOOK = "Book"
    VIDEO = "Video"
    PODCAST = "Podcast"
    DOCUMENT = "Document"
    WEBSITE = "Website"
    RESEARCH = "Research"
    TOOL = "Tool"
    PERSON = "Person"
    COMPANY = "Company"


class ReferenceStatus(Enum):
    """Status of references"""
    TO_READ = "To Read"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    REFERENCED = "Referenced"
    ARCHIVED = "Archived"


@dataclass
class NotionReference:
    """
    Notion Reference data model
    
    Represents a reference/resource for knowledge management and linking to projects/areas.
    """
    
    # Core identification
    reference_id: str
    title: str
    description: str = ""
    
    # Classification
    reference_type: str = ReferenceType.ARTICLE.value
    status: str = ReferenceStatus.TO_READ.value
    priority: str = Priority.LOW.value
    
    # Content details
    url: Optional[str] = None
    author: Optional[str] = None
    source: Optional[str] = None
    publication_date: Optional[datetime] = None
    
    # Relationships
    project_ids: List[str] = field(default_factory=list)
    area_ids: List[str] = field(default_factory=list)
    goal_ids: List[str] = field(default_factory=list)
    note_ids: List[str] = field(default_factory=list)
    
    # Organization
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    
    # Content
    summary: str = ""
    key_quotes: List[str] = field(default_factory=list)
    key_insights: List[str] = field(default_factory=list)
    
    # Ratings and metrics
    rating: Optional[int] = None  # 1-5 scale
    usefulness: Optional[int] = None  # 1-5 scale
    reading_time_minutes: Optional[int] = None
    
    # System properties
    created_time: datetime = field(default_factory=datetime.now)
    last_edited_time: Optional[datetime] = None
    accessed_date: Optional[datetime] = None
    archive: bool = False
    
    @classmethod
    def from_notion_data(cls, notion_data: Dict[str, Any]) -> 'NotionReference':
        """
        Create NotionReference from Notion API response data
        
        Args:
            notion_data: Raw data from Notion API
            
        Returns:
            NotionReference instance
        """
        properties = notion_data.get('properties', {})
        
        # Extract basic fields
        reference_id = notion_data.get('id', '')
        title = cls._extract_title(properties.get('Title', {}) or properties.get('Name', {}))
        description = cls._extract_rich_text(properties.get('Description', {}))
        
        # Extract classification
        reference_type = cls._extract_select(properties.get('Type', {}))
        status = cls._extract_select(properties.get('Status', {}))
        priority = cls._extract_select(properties.get('Priority', {}))
        
        # Extract content details
        url = cls._extract_url(properties.get('URL', {}))
        author = cls._extract_rich_text(properties.get('Author', {}))
        source = cls._extract_rich_text(properties.get('Source', {}))
        publication_date = cls._extract_date(properties.get('Publication Date', {}))
        
        # Extract dates
        created_time = cls._extract_created_time(properties.get('Created', {}))
        last_edited_time = cls._extract_last_edited_time(properties.get('Edited', {}))
        accessed_date = cls._extract_date(properties.get('Last Accessed', {}))
        
        # Extract relationships
        project_ids = cls._extract_relation_ids(properties.get('Projects', {}))
        area_ids = cls._extract_relation_ids(properties.get('Areas', {}))
        goal_ids = cls._extract_relation_ids(properties.get('Goals', {}))
        note_ids = cls._extract_relation_ids(properties.get('Notes', {}))
        
        # Extract organization
        tags = cls._extract_multi_select(properties.get('Tags', {}))
        categories = cls._extract_multi_select(properties.get('Categories', {}))
        
        # Extract content
        summary = cls._extract_rich_text(properties.get('Summary', {}))
        key_quotes = cls._extract_multi_select(properties.get('Key Quotes', {}))
        key_insights = cls._extract_multi_select(properties.get('Key Insights', {}))
        
        # Extract ratings
        rating = cls._extract_number(properties.get('Rating', {}))
        usefulness = cls._extract_number(properties.get('Usefulness', {}))
        reading_time_minutes = cls._extract_number(properties.get('Reading Time', {}))
        
        # Extract checkbox
        archive = cls._extract_checkbox(properties.get('Archive', {}))
        
        return cls(
            reference_id=reference_id,
            title=title,
            description=description,
            reference_type=reference_type,
            status=status,
            priority=priority,
            url=url,
            author=author,
            source=source,
            publication_date=publication_date,
            project_ids=project_ids,
            area_ids=area_ids,
            goal_ids=goal_ids,
            note_ids=note_ids,
            tags=tags,
            categories=categories,
            summary=summary,
            key_quotes=key_quotes,
            key_insights=key_insights,
            rating=int(rating) if rating else None,
            usefulness=int(usefulness) if usefulness else None,
            reading_time_minutes=int(reading_time_minutes) if reading_time_minutes else None,
            created_time=created_time,
            last_edited_time=last_edited_time,
            accessed_date=accessed_date,
            archive=archive
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'reference_id': self.reference_id,
            'title': self.title,
            'description': self.description,
            'reference_type': self.reference_type,
            'status': self.status,
            'priority': self.priority,
            'url': self.url,
            'author': self.author,
            'source': self.source,
            'publication_date': self.publication_date.isoformat() if self.publication_date else None,
            'project_ids': self.project_ids,
            'area_ids': self.area_ids,
            'goal_ids': self.goal_ids,
            'note_ids': self.note_ids,
            'tags': self.tags,
            'categories': self.categories,
            'summary': self.summary,
            'key_quotes': self.key_quotes,
            'key_insights': self.key_insights,
            'rating': self.rating,
            'usefulness': self.usefulness,
            'reading_time_minutes': self.reading_time_minutes,
            'created_time': self.created_time.isoformat(),
            'last_edited_time': self.last_edited_time.isoformat() if self.last_edited_time else None,
            'accessed_date': self.accessed_date.isoformat() if self.accessed_date else None,
            'archive': self.archive
        }
    
    def is_completed(self) -> bool:
        """Check if reference has been fully processed"""
        return self.status == ReferenceStatus.COMPLETED.value
    
    def is_in_progress(self) -> bool:
        """Check if reference is currently being processed"""
        return self.status == ReferenceStatus.IN_PROGRESS.value
    
    def is_archived(self) -> bool:
        """Check if reference is archived"""
        return self.status == ReferenceStatus.ARCHIVED.value or self.archive
    
    def mark_accessed(self) -> None:
        """Mark reference as accessed today"""
        self.accessed_date = datetime.now()
        self.last_edited_time = datetime.now()
    
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
    
    def add_category(self, category: str) -> None:
        """Add a category if not already present"""
        if category not in self.categories:
            self.categories.append(category)
            self.last_edited_time = datetime.now()
    
    def add_key_insight(self, insight: str) -> None:
        """Add a key insight"""
        if insight not in self.key_insights:
            self.key_insights.append(insight)
            self.last_edited_time = datetime.now()
    
    def add_key_quote(self, quote: str) -> None:
        """Add a key quote"""
        if quote not in self.key_quotes:
            self.key_quotes.append(quote)
            self.last_edited_time = datetime.now()
    
    def link_to_project(self, project_id: str) -> None:
        """Link reference to a project"""
        if project_id not in self.project_ids:
            self.project_ids.append(project_id)
            self.last_edited_time = datetime.now()
    
    def link_to_area(self, area_id: str) -> None:
        """Link reference to an area"""
        if area_id not in self.area_ids:
            self.area_ids.append(area_id)
            self.last_edited_time = datetime.now()
    
    def link_to_goal(self, goal_id: str) -> None:
        """Link reference to a goal"""
        if goal_id not in self.goal_ids:
            self.goal_ids.append(goal_id)
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
    def _extract_relation_ids(relation_property: Dict[str, Any]) -> List[str]:
        """Extract all relation IDs from Notion relation property"""
        relation_list = relation_property.get('relation', [])
        return [item.get('id', '') for item in relation_list if item.get('id')]
    
    @staticmethod
    def _extract_checkbox(checkbox_property: Dict[str, Any]) -> bool:
        """Extract checkbox value from Notion checkbox property"""
        return checkbox_property.get('checkbox', False)