"""
Notion Event/Meeting Data Model

Represents an event or meeting from the Notion Events database for calendar and meeting management.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

from .notion_project import Priority, DateRange


class EventStatus(Enum):
    """Valid event status values from Notion database"""
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    RESCHEDULED = "Rescheduled"


class EventType(Enum):
    """Types of events"""
    MEETING = "Meeting"
    CALL = "Call"
    PRESENTATION = "Presentation"
    WORKSHOP = "Workshop"
    INTERVIEW = "Interview"
    PERSONAL = "Personal"
    TRAVEL = "Travel"


class EventPriority(Enum):
    """Event-specific priority levels"""
    OPTIONAL = "Optional"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class NotionEvent:
    """
    Notion Event data model
    
    Represents an event/meeting from the Events database (0e341d66-cecf-4521-a875-7af1585dda42)
    for calendar and meeting management.
    """
    
    # Core identification
    event_id: str
    title: str
    description: str = ""
    
    # Event details
    status: str = EventStatus.SCHEDULED.value
    event_type: str = EventType.MEETING.value
    priority: str = EventPriority.MEDIUM.value
    
    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    timezone: str = "UTC"
    
    # Location and access
    location: str = ""
    meeting_url: Optional[str] = None
    meeting_id: Optional[str] = None
    passcode: Optional[str] = None
    
    # Relationships
    project_id: Optional[str] = None
    area_id: Optional[str] = None
    goal_id: Optional[str] = None
    
    # Participants
    organizer: Optional[str] = None
    attendees: List[str] = field(default_factory=list)
    required_attendees: List[str] = field(default_factory=list)
    optional_attendees: List[str] = field(default_factory=list)
    
    # Content
    agenda: str = ""
    notes: str = ""
    action_items: List[str] = field(default_factory=list)
    
    # System properties
    created_time: datetime = field(default_factory=datetime.now)
    last_edited_time: Optional[datetime] = None
    archive: bool = False
    
    # Computed properties
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    
    @classmethod
    def from_notion_data(cls, notion_data: Dict[str, Any]) -> 'NotionEvent':
        """
        Create NotionEvent from Notion API response data
        
        Args:
            notion_data: Raw data from Notion API
            
        Returns:
            NotionEvent instance
        """
        properties = notion_data.get('properties', {})
        
        # Extract basic fields
        event_id = notion_data.get('id', '')
        title = cls._extract_title(properties.get('Title', {}) or properties.get('Name', {}))
        description = cls._extract_rich_text(properties.get('Description', {}))
        
        # Extract classification
        status = cls._extract_select(properties.get('Status', {}))
        event_type = cls._extract_select(properties.get('Type', {}))
        priority = cls._extract_select(properties.get('Priority', {}))
        
        # Extract timing
        start_time = cls._extract_date(properties.get('Start Time', {}))
        end_time = cls._extract_date(properties.get('End Time', {}))
        duration_minutes = cls._extract_number(properties.get('Duration', {}))
        timezone = cls._extract_select(properties.get('Timezone', {})) or "UTC"
        
        # Extract location and access
        location = cls._extract_rich_text(properties.get('Location', {}))
        meeting_url = cls._extract_url(properties.get('Meeting URL', {}))
        meeting_id = cls._extract_rich_text(properties.get('Meeting ID', {}))
        passcode = cls._extract_rich_text(properties.get('Passcode', {}))
        
        # Extract dates
        created_time = cls._extract_created_time(properties.get('Created', {}))
        last_edited_time = cls._extract_last_edited_time(properties.get('Edited', {}))
        
        # Extract relationships
        project_id = cls._extract_relation_id(properties.get('Project', {}))
        area_id = cls._extract_relation_id(properties.get('Area', {}))
        goal_id = cls._extract_relation_id(properties.get('Goal', {}))
        
        # Extract participants
        organizer = cls._extract_rich_text(properties.get('Organizer', {}))
        attendees = cls._extract_multi_select(properties.get('Attendees', {}))
        required_attendees = cls._extract_multi_select(properties.get('Required Attendees', {}))
        optional_attendees = cls._extract_multi_select(properties.get('Optional Attendees', {}))
        
        # Extract content
        agenda = cls._extract_rich_text(properties.get('Agenda', {}))
        notes = cls._extract_rich_text(properties.get('Notes', {}))
        action_items = cls._extract_multi_select(properties.get('Action Items', {}))
        
        # Extract recurrence
        is_recurring = cls._extract_checkbox(properties.get('Recurring', {}))
        recurrence_pattern = cls._extract_rich_text(properties.get('Recurrence Pattern', {}))
        
        # Extract checkbox
        archive = cls._extract_checkbox(properties.get('Archive', {}))
        
        return cls(
            event_id=event_id,
            title=title,
            description=description,
            status=status,
            event_type=event_type,
            priority=priority,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=int(duration_minutes) if duration_minutes else None,
            timezone=timezone,
            location=location,
            meeting_url=meeting_url,
            meeting_id=meeting_id,
            passcode=passcode,
            project_id=project_id,
            area_id=area_id,
            goal_id=goal_id,
            organizer=organizer,
            attendees=attendees,
            required_attendees=required_attendees,
            optional_attendees=optional_attendees,
            agenda=agenda,
            notes=notes,
            action_items=action_items,
            created_time=created_time,
            last_edited_time=last_edited_time,
            archive=archive,
            is_recurring=is_recurring,
            recurrence_pattern=recurrence_pattern
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'event_id': self.event_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'event_type': self.event_type,
            'priority': self.priority,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_minutes': self.duration_minutes,
            'timezone': self.timezone,
            'location': self.location,
            'meeting_url': self.meeting_url,
            'meeting_id': self.meeting_id,
            'passcode': self.passcode,
            'project_id': self.project_id,
            'area_id': self.area_id,
            'goal_id': self.goal_id,
            'organizer': self.organizer,
            'attendees': self.attendees,
            'required_attendees': self.required_attendees,
            'optional_attendees': self.optional_attendees,
            'agenda': self.agenda,
            'notes': self.notes,
            'action_items': self.action_items,
            'created_time': self.created_time.isoformat(),
            'last_edited_time': self.last_edited_time.isoformat() if self.last_edited_time else None,
            'archive': self.archive,
            'is_recurring': self.is_recurring,
            'recurrence_pattern': self.recurrence_pattern
        }
    
    def is_completed(self) -> bool:
        """Check if event is completed"""
        return self.status == EventStatus.COMPLETED.value
    
    def is_cancelled(self) -> bool:
        """Check if event is cancelled"""
        return self.status == EventStatus.CANCELLED.value
    
    def is_upcoming(self) -> bool:
        """Check if event is upcoming (scheduled and in the future)"""
        if not self.start_time:
            return False
        return (self.status == EventStatus.SCHEDULED.value and 
                self.start_time > datetime.now())
    
    def is_today(self) -> bool:
        """Check if event is scheduled for today"""
        if not self.start_time:
            return False
        today = datetime.now().date()
        return self.start_time.date() == today
    
    def time_until_start(self) -> Optional[timedelta]:
        """Get time until event starts"""
        if not self.start_time:
            return None
        now = datetime.now()
        if self.start_time > now:
            return self.start_time - now
        return None
    
    def calculate_duration(self) -> Optional[int]:
        """Calculate duration in minutes from start/end times"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return self.duration_minutes
    
    def add_attendee(self, attendee: str, required: bool = True) -> None:
        """Add an attendee to the event"""
        if attendee not in self.attendees:
            self.attendees.append(attendee)
            if required and attendee not in self.required_attendees:
                self.required_attendees.append(attendee)
            elif not required and attendee not in self.optional_attendees:
                self.optional_attendees.append(attendee)
            self.last_edited_time = datetime.now()
    
    def remove_attendee(self, attendee: str) -> None:
        """Remove an attendee from the event"""
        for attendee_list in [self.attendees, self.required_attendees, self.optional_attendees]:
            if attendee in attendee_list:
                attendee_list.remove(attendee)
        self.last_edited_time = datetime.now()
    
    def add_action_item(self, action_item: str) -> None:
        """Add an action item to the event"""
        if action_item not in self.action_items:
            self.action_items.append(action_item)
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