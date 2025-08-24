"""
Note entity manager for GraphRAG adapter.
"""

import json
import uuid
from typing import Optional, List, Dict, Any

from .base_manager import BaseEntityManager


class NoteManager(BaseEntityManager):
    """Manager for NOTE entities with validation and relationship handling."""
    
    ENTITY_TYPE = "TASK_MANAGEMENT:NOTE"
    REQUIRED_FIELDS = ["title", "content"]
    OPTIONAL_FIELDS = ["context", "tags", "created", "source"]
    
    def create(self, title: str, content: str, context: str = None, 
              tags: List[str] = None) -> Optional[str]:
        """
        Create note with optional context and tags.
        
        Args:
            title: Note title (required)
            content: Note content (required) 
            context: Optional context information
            tags: Optional list of tags
            
        Returns:
            Note ID if successful, None if failed
        """
        # Generate unique note ID
        note_id = f"note_{uuid.uuid4().hex[:8]}"
        
        # Build entity data
        entity_data = {
            "id": note_id,
            "title": title,  # Required
            "content": content,  # Required
        }
        
        # Add optional fields
        if context:
            entity_data["context"] = context
        if tags:
            entity_data["tags"] = tags
        
        # Add timestamp
        from datetime import datetime
        entity_data["created"] = datetime.now().isoformat()
        
        # Create the entity
        created_note_id = self.create_entity(entity_data)
        
        return created_note_id
    
    def find_by_title(self, title: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find notes by title using semantic search."""
        
        query_params = {
            "query": f"Find notes with title: {title}",
            "max_results": limit
        }
        
        response = self.adapter._execute_mcp_command("query_natural_language", query_params)
        
        if response.get("success") and response.get("results"):
            return response["results"]
        
        return []
    
    def find_by_content(self, content_query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find notes by content using semantic search."""
        
        query_params = {
            "query": f"Find notes containing: {content_query}",
            "max_results": limit
        }
        
        response = self.adapter._execute_mcp_command("query_natural_language", query_params)
        
        if response.get("success") and response.get("results"):
            return response["results"]
        
        return []
    
    def add_tag(self, note_id: str, tag: str) -> bool:
        """Add a tag to an existing note."""
        
        # First get current tags
        query = f"""
        MATCH (n:TASK_MANAGEMENT:NOTE {{id: '{note_id}'}})
        RETURN n.tags as current_tags
        """
        
        response = self.adapter._execute_mcp_command("execute_cypher", {"query": query})
        
        if not response.get("success") or not response.get("results"):
            self.logger.error(f"Could not retrieve note {note_id} for tag addition")
            return False
        
        current_tags = response["results"][0].get("current_tags", [])
        if not isinstance(current_tags, list):
            current_tags = []
        
        # Add new tag if not already present
        if tag not in current_tags:
            current_tags.append(tag)
            
            # Update note with new tags
            return self.update(note_id, {"tags": current_tags})
        
        return True  # Tag already exists
    
    def update(self, note_id: str, updates: Dict[str, Any]) -> bool:
        """Update note properties."""
        
        # Validate update fields
        invalid_fields = set(updates.keys()) - set(self.REQUIRED_FIELDS + self.OPTIONAL_FIELDS)
        if invalid_fields:
            self.logger.error(f"Invalid update fields for {self.ENTITY_TYPE}: {invalid_fields}")
            return False
        
        # Build Cypher update query
        set_clauses = []
        for key, value in updates.items():
            if isinstance(value, str):
                escaped_value = value.replace("'", "\\'")
                set_clauses.append(f"n.{key} = '{escaped_value}'")
            elif isinstance(value, list):
                # Handle arrays (like tags)
                json_value = json.dumps(value).replace("'", "\\\\'")
                set_clauses.append(f"n.{key} = {json_value}")
            elif isinstance(value, (int, float, bool)):
                set_clauses.append(f"n.{key} = {value}")
            elif value is None:
                set_clauses.append(f"n.{key} = null")
        
        if not set_clauses:
            self.logger.warning("No valid update clauses generated")
            return False
        
        update_query = f"""
        MATCH (n:TASK_MANAGEMENT:NOTE {{id: '{note_id}'}})
        SET {', '.join(set_clauses)}
        RETURN n.id as updated_id
        """
        
        response = self.adapter._execute_mcp_command("execute_cypher", {
            "query": update_query.strip()
        })
        
        if response.get("success") and response.get("results"):
            self.logger.success(f"✅ Updated note: {note_id}")
            return True
        else:
            self.logger.error(f"Failed to update note {note_id}: {response.get('error')}")
            return False