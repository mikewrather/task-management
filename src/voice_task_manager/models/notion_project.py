"""
Notion Project Data Model

Represents a project from the Notion Projects database with full PARA methodology support.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ProjectStatus(Enum):
    """Valid project status values from Notion database"""
    INBOX = "Inbox"
    NOT_STARTED = "Not Started" 
    IN_PROGRESS = "In Progress"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"


class Priority(Enum):
    """Priority levels for projects"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


@dataclass
class DateRange:
    """Represents a date range for project timelines"""
    start: Optional[datetime] = None
    end: Optional[datetime] = None


@dataclass
class NotionProject:
    """
    Notion Project data model
    
    Represents a project from the Projects database (9abc79db-e5c2-4046-b812-585804df2e41)
    with full PARA methodology support and rich relationship tracking.
    """
    
    # Core identification
    project_id: str
    name: str
    
    # Status and priority
    status: str = ProjectStatus.INBOX.value
    priority: str = Priority.MEDIUM.value
    
    # Relationships
    area_id: Optional[str] = None
    goal_id: Optional[str] = None
    parent_project_id: Optional[str] = None
    
    # Timeline information
    timeline: Optional[DateRange] = None
    start_date: Optional[datetime] = None
    
    # Computed properties
    progress: Optional[float] = None  # From rollup of task completion
    goal_area: Optional[str] = None  # From goal relation rollup
    
    # System properties
    created_time: datetime = field(default_factory=datetime.now)
    last_edited_time: Optional[datetime] = None
    archive: bool = False
    
    # Related entity counts (computed)
    task_count: int = 0
    completed_task_count: int = 0
    note_count: int = 0
    meeting_count: int = 0
    
    @classmethod
    def from_notion_data(cls, notion_data: Dict[str, Any]) -> 'NotionProject':
        """
        Create NotionProject from Notion API response data
        
        Args:
            notion_data: Raw data from Notion API
            
        Returns:
            NotionProject instance
        """
        properties = notion_data.get('properties', {})
        
        # Extract basic fields
        project_id = notion_data.get('id', '')
        name = cls._extract_title(properties.get('Name', {}))
        
        # Extract status and priority
        status = cls._extract_select(properties.get('Status', {}))
        priority = cls._extract_select(properties.get('Priority', {}))
        
        # Extract dates
        created_time = cls._extract_created_time(properties.get('Created', {}))
        last_edited_time = cls._extract_last_edited_time(properties.get('Edited', {}))
        start_date = cls._extract_date(properties.get('Start Date', {}))
        
        # Extract timeline
        timeline_data = properties.get('Timeline', {})
        timeline = cls._extract_date_range(timeline_data) if timeline_data else None
        
        # Extract relationships
        area_id = cls._extract_relation_id(properties.get('Area', {}))
        goal_id = cls._extract_relation_id(properties.get('Goal', {}))
        parent_project_id = cls._extract_relation_id(properties.get('Parent Project', {}))
        
        # Extract computed properties
        progress = cls._extract_rollup_number(properties.get('Progress', {}))
        goal_area = cls._extract_rollup_text(properties.get('Goal Area', {}))
        
        # Extract checkbox
        archive = cls._extract_checkbox(properties.get('Archive', {}))
        
        return cls(
            project_id=project_id,
            name=name,
            status=status,
            priority=priority,
            area_id=area_id,
            goal_id=goal_id,
            parent_project_id=parent_project_id,
            timeline=timeline,
            start_date=start_date,
            progress=progress,
            goal_area=goal_area,
            created_time=created_time,
            last_edited_time=last_edited_time,
            archive=archive
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'project_id': self.project_id,
            'name': self.name,
            'status': self.status,
            'priority': self.priority,
            'area_id': self.area_id,
            'goal_id': self.goal_id,
            'parent_project_id': self.parent_project_id,
            'timeline': {
                'start': self.timeline.start.isoformat() if self.timeline and self.timeline.start else None,
                'end': self.timeline.end.isoformat() if self.timeline and self.timeline.end else None
            } if self.timeline else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'progress': self.progress,
            'goal_area': self.goal_area,
            'created_time': self.created_time.isoformat(),
            'last_edited_time': self.last_edited_time.isoformat() if self.last_edited_time else None,
            'archive': self.archive,
            'task_count': self.task_count,
            'completed_task_count': self.completed_task_count,
            'note_count': self.note_count,
            'meeting_count': self.meeting_count
        }
    
    def is_active(self) -> bool:
        """Check if project is actively being worked on"""
        return self.status == ProjectStatus.IN_PROGRESS.value and not self.archive
    
    def is_completed(self) -> bool:
        """Check if project is completed"""
        return self.status == ProjectStatus.COMPLETED.value
    
    def completion_percentage(self) -> float:
        """Get completion percentage (0.0 to 1.0)"""
        return self.progress if self.progress is not None else 0.0
    
    @staticmethod
    def _extract_title(title_property: Dict[str, Any]) -> str:
        """Extract title from Notion title property"""
        title_list = title_property.get('title', [])
        if title_list:
            return title_list[0].get('plain_text', '')
        return ''
    
    @staticmethod
    def _extract_select(select_property: Dict[str, Any]) -> str:
        """Extract select value from Notion select property"""
        select_data = select_property.get('select', {})
        return select_data.get('name', '') if select_data else ''
    
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
    def _extract_date_range(date_property: Dict[str, Any]) -> Optional[DateRange]:
        """Extract date range from Notion date property"""
        date_data = date_property.get('date', {})
        if not date_data:
            return None
        
        start = None
        end = None
        
        if date_data.get('start'):
            start = datetime.fromisoformat(date_data['start'].replace('Z', '+00:00'))
        
        if date_data.get('end'):
            end = datetime.fromisoformat(date_data['end'].replace('Z', '+00:00'))
        
        return DateRange(start=start, end=end) if start or end else None
    
    @staticmethod
    def _extract_relation_id(relation_property: Dict[str, Any]) -> Optional[str]:
        """Extract first relation ID from Notion relation property"""
        relation_list = relation_property.get('relation', [])
        if relation_list:
            return relation_list[0].get('id')
        return None
    
    @staticmethod
    def _extract_rollup_number(rollup_property: Dict[str, Any]) -> Optional[float]:
        """Extract number from Notion rollup property"""
        rollup_data = rollup_property.get('rollup', {})
        if rollup_data and rollup_data.get('type') == 'number':
            return rollup_data.get('number')
        return None
    
    @staticmethod
    def _extract_rollup_text(rollup_property: Dict[str, Any]) -> Optional[str]:
        """Extract text from Notion rollup property"""
        rollup_data = rollup_property.get('rollup', {})
        if rollup_data:
            # Handle different rollup result types
            if rollup_data.get('type') == 'array':
                array_results = rollup_data.get('array', [])
                if array_results:
                    return array_results[0].get('title', [{}])[0].get('plain_text', '')
        return None
    
    @staticmethod
    def _extract_checkbox(checkbox_property: Dict[str, Any]) -> bool:
        """Extract checkbox value from Notion checkbox property"""
        return checkbox_property.get('checkbox', False)