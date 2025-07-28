"""
Notion Goal Data Model

Represents a goal from the Notion Goals database with PARA methodology support.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from .notion_project import Priority, DateRange


class GoalStatus(Enum):
    """Valid goal status values from Notion database"""
    INBOX = "Inbox"
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"


class GoalType(Enum):
    """Types of goals"""
    PERSONAL = "Personal"
    PROFESSIONAL = "Professional"
    HEALTH = "Health"
    FINANCIAL = "Financial"
    LEARNING = "Learning"
    RELATIONSHIP = "Relationship"


@dataclass
class NotionGoal:
    """
    Notion Goal data model
    
    Represents a goal from the Goals database (07654b24-ee44-473b-a43c-6ac78e49f717)
    with full PARA methodology support and relationship tracking.
    """
    
    # Core identification
    goal_id: str
    name: str
    description: str = ""
    
    # Status and priority
    status: str = GoalStatus.INBOX.value
    priority: str = Priority.MEDIUM.value
    goal_type: str = GoalType.PERSONAL.value
    
    # Timeline information
    timeline: Optional[DateRange] = None
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    
    # Computed properties
    progress: Optional[float] = None  # From rollup of project/task completion
    completion_rate: Optional[float] = None  # Calculated completion percentage
    
    # System properties
    created_time: datetime = field(default_factory=datetime.now)
    last_edited_time: Optional[datetime] = None
    archive: bool = False
    
    # Related entity counts (computed)
    project_count: int = 0
    area_count: int = 0
    task_count: int = 0
    completed_task_count: int = 0
    note_count: int = 0
    meeting_count: int = 0
    
    @classmethod
    def from_notion_data(cls, notion_data: Dict[str, Any]) -> 'NotionGoal':
        """
        Create NotionGoal from Notion API response data
        
        Args:
            notion_data: Raw data from Notion API
            
        Returns:
            NotionGoal instance
        """
        properties = notion_data.get('properties', {})
        
        # Extract basic fields
        goal_id = notion_data.get('id', '')
        name = cls._extract_title(properties.get('Name', {}))
        description = cls._extract_rich_text(properties.get('Description', {}))
        
        # Extract status and priority
        status = cls._extract_select(properties.get('Status', {}))
        priority = cls._extract_select(properties.get('Priority', {}))
        goal_type = cls._extract_select(properties.get('Type', {}))
        
        # Extract dates
        created_time = cls._extract_created_time(properties.get('Created', {}))
        last_edited_time = cls._extract_last_edited_time(properties.get('Edited', {}))
        start_date = cls._extract_date(properties.get('Start Date', {}))
        target_date = cls._extract_date(properties.get('Target Date', {}))
        
        # Extract timeline
        timeline_data = properties.get('Timeline', {})
        timeline = cls._extract_date_range(timeline_data) if timeline_data else None
        
        # Extract computed properties
        progress = cls._extract_rollup_number(properties.get('Progress', {}))
        completion_rate = cls._extract_number(properties.get('Completion Rate', {}))
        
        # Extract checkbox
        archive = cls._extract_checkbox(properties.get('Archive', {}))
        
        return cls(
            goal_id=goal_id,
            name=name,
            description=description,
            status=status,
            priority=priority,
            goal_type=goal_type,
            timeline=timeline,
            start_date=start_date,
            target_date=target_date,
            progress=progress,
            completion_rate=completion_rate,
            created_time=created_time,
            last_edited_time=last_edited_time,
            archive=archive
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'goal_id': self.goal_id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'goal_type': self.goal_type,
            'timeline': {
                'start': self.timeline.start.isoformat() if self.timeline and self.timeline.start else None,
                'end': self.timeline.end.isoformat() if self.timeline and self.timeline.end else None
            } if self.timeline else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'progress': self.progress,
            'completion_rate': self.completion_rate,
            'created_time': self.created_time.isoformat(),
            'last_edited_time': self.last_edited_time.isoformat() if self.last_edited_time else None,
            'archive': self.archive,
            'project_count': self.project_count,
            'area_count': self.area_count,
            'task_count': self.task_count,
            'completed_task_count': self.completed_task_count,
            'note_count': self.note_count,
            'meeting_count': self.meeting_count
        }
    
    def is_active(self) -> bool:
        """Check if goal is actively being worked on"""
        return self.status == GoalStatus.IN_PROGRESS.value and not self.archive
    
    def is_completed(self) -> bool:
        """Check if goal is completed"""
        return self.status == GoalStatus.COMPLETED.value
    
    def completion_percentage(self) -> float:
        """Get completion percentage (0.0 to 1.0)"""
        if self.completion_rate is not None:
            return self.completion_rate
        return self.progress if self.progress is not None else 0.0
    
    def days_until_target(self) -> Optional[int]:
        """Get number of days until target date"""
        if not self.target_date:
            return None
        delta = self.target_date - datetime.now()
        return delta.days
    
    def is_overdue(self) -> bool:
        """Check if goal is past its target date"""
        if not self.target_date:
            return False
        return datetime.now() > self.target_date and not self.is_completed()
    
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
            return rich_text_list[0].get('plain_text', '')
        return ''
    
    @staticmethod
    def _extract_select(select_property: Dict[str, Any]) -> str:
        """Extract select value from Notion select property"""
        select_data = select_property.get('select', {})
        return select_data.get('name', '') if select_data else ''
    
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
    def _extract_rollup_number(rollup_property: Dict[str, Any]) -> Optional[float]:
        """Extract number from Notion rollup property"""
        rollup_data = rollup_property.get('rollup', {})
        if rollup_data and rollup_data.get('type') == 'number':
            return rollup_data.get('number')
        return None
    
    @staticmethod
    def _extract_checkbox(checkbox_property: Dict[str, Any]) -> bool:
        """Extract checkbox value from Notion checkbox property"""
        return checkbox_property.get('checkbox', False)