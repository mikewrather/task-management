"""
Entity management system for GraphRAG adapter.

Provides dedicated managers for each entity type with validation,
error handling, and relationship management.
"""

from .base_manager import BaseEntityManager
from .task_manager import TaskManager
from .project_manager import ProjectManager
from .area_manager import AreaManager
from .goal_manager import GoalManager
from .note_manager import NoteManager

__all__ = [
    "BaseEntityManager",
    "TaskManager", 
    "ProjectManager",
    "AreaManager",
    "GoalManager",
    "NoteManager"
]