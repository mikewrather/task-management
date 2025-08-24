"""Task storage adapters for GraphRAG support"""

from .base import TaskAdapter, TaskData
from .graphrag import GraphRAGTaskAdapter

__all__ = ['TaskAdapter', 'TaskData', 'GraphRAGTaskAdapter']