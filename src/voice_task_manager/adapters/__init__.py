"""Task storage adapters for multi-platform support"""

from .base import TaskAdapter, TaskData
from .notion import NotionTaskAdapter
from .graphrag import GraphRAGTaskAdapter

__all__ = ['TaskAdapter', 'TaskData', 'NotionTaskAdapter', 'GraphRAGTaskAdapter']