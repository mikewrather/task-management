"""
Base entity manager with common validation and error handling functionality.
"""

import json
import re
from typing import Dict, Any, Optional, Tuple, List
from abc import ABC, abstractmethod


class BaseEntityManager(ABC):
    """Base class for entity managers with common validation and error handling."""
    
    # Subclasses must define these
    ENTITY_TYPE: str = ""
    REQUIRED_FIELDS: List[str] = []
    OPTIONAL_FIELDS: List[str] = []
    
    def __init__(self, adapter):
        """Initialize with reference to the GraphRAG adapter."""
        self.adapter = adapter
        self.logger = adapter.logger
    
    def validate_entity(self, entity_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate entity data against schema requirements.
        
        Returns:
            (is_valid: bool, error_message: str)
        """
        if not self.ENTITY_TYPE:
            return False, "Entity type not defined"
        
        # Check required fields
        missing_fields = []
        for field in self.REQUIRED_FIELDS:
            if field not in entity_data or entity_data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Check for unexpected fields (warn only)
        all_allowed = set(self.REQUIRED_FIELDS + self.OPTIONAL_FIELDS)
        unexpected = set(entity_data.keys()) - all_allowed
        if unexpected:
            self.logger.warning(f"Unexpected fields for {self.ENTITY_TYPE}: {unexpected}")
        
        return True, "Valid"
    
    def create_entity(self, entity_data: Dict[str, Any]) -> Optional[str]:
        """
        Create entity with validation and error handling.
        
        Returns:
            entity_id if successful, None if failed
        """
        # Validate before sending to MCP
        is_valid, error_msg = self.validate_entity(entity_data)
        if not is_valid:
            self.logger.error(f"Validation failed for {self.ENTITY_TYPE}: {error_msg}")
            return None
        
        # Prepare MCP parameters - CRITICAL: entities must be object format (not array!)
        mcp_params = {
            "entity_type": self.ENTITY_TYPE,
            "entities": entity_data,  # Object format, not array
            "check_duplicates": True
        }
        
        # Execute with retry logic
        return self.create_with_retry(mcp_params, max_retries=2)
    
    def create_with_retry(self, mcp_params: Dict[str, Any], max_retries: int = 2) -> Optional[str]:
        """Create entity with retry logic for common fixes."""
        
        for attempt in range(max_retries + 1):
            self.logger.debug(f"Entity creation attempt {attempt + 1}/{max_retries + 1}")
            
            # Execute MCP command
            response = self.adapter._execute_mcp_command("create_entities", mcp_params)
            
            # Parse response
            success, entity_id, error = self.parse_mcp_response(response)
            
            if success:
                self.logger.success(f"✅ Created {self.ENTITY_TYPE}: {entity_id}")
                return entity_id
            
            # Try common fixes on validation errors
            if attempt < max_retries:
                if "required field" in error.lower():
                    mcp_params["entities"] = self._add_default_required_fields(mcp_params["entities"])
                    self.logger.info(f"Retry {attempt + 1}: Adding default required fields")
                    continue
                elif "format" in error.lower() or "validation" in error.lower():
                    mcp_params["entities"] = self._fix_field_formats(mcp_params["entities"])
                    self.logger.info(f"Retry {attempt + 1}: Fixing field formats")
                    continue
            
            self.logger.error(f"Entity creation failed after {attempt + 1} attempts: {error}")
            break
        
        return None
    
    def parse_mcp_response(self, response: Dict[str, Any]) -> Tuple[bool, Optional[str], str]:
        """
        Parse MCP response with detailed error analysis.
        
        Returns:
            (success: bool, entity_id: Optional[str], error_message: str)
        """
        if not response.get("success", False):
            error_msg = response.get("error", "Unknown MCP error")
            
            # Check if it's a validation error
            if "validation" in error_msg.lower():
                validation_details = self._extract_validation_details(error_msg)
                return False, None, f"Schema validation failed: {validation_details}"
            
            return False, None, f"MCP call failed: {error_msg}"
        
        # Check for Claude's interpreted response (when Claude processes the result)
        result_text = response.get("result", "")
        if isinstance(result_text, str) and ("validation errors" in result_text.lower() or "error" in result_text.lower()):
            validation_details = self._extract_validation_details(result_text)
            return False, None, f"Schema validation failed: {validation_details}"
        
        # Extract entity ID from various response formats
        entity_id = self._extract_entity_id(response)
        if not entity_id:
            return False, None, f"Could not extract entity ID from response: {json.dumps(response, indent=2)[:300]}..."
        
        return True, entity_id, "Success"
    
    def _extract_entity_id(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract entity ID from MCP response in various formats."""
        
        # Format 1: Direct results array with entity info
        results = response.get("results", [])
        if results and isinstance(results, list) and len(results) > 0:
            result = results[0]
            
            # Check for entity_id field
            if "entity_id" in result:
                return result["entity_id"]
            
            # Check for entity objects with id field
            for key in ['t', 'task', 'p', 'project', 'a', 'area', 'entity']:
                if key in result:
                    entity = result[key]
                    if isinstance(entity, dict) and 'id' in entity:
                        return entity['id']
        
        # Format 2: entities array (mock response format)
        entities = response.get("entities", [])
        if entities and isinstance(entities, list) and len(entities) > 0:
            entity = entities[0]
            if isinstance(entity, dict) and 'id' in entity:
                return entity['id']
        
        # Format 3: Direct entity_id in response
        if "entity_id" in response:
            return response["entity_id"]
        
        return None
    
    def _extract_validation_details(self, error_text: str) -> str:
        """Extract specific validation errors from error messages."""
        
        # Look for common validation error patterns
        patterns = [
            r"required field[s]?\\s*(?:is|are)?\\s*missing:\\s*([^.]+)",
            r"invalid format for field[s]?\\s*([^.]+)", 
            r"field[s]?\\s*([^.]+)\\s*(?:is|are)\\s*required",
            r"schema mismatch.*field[s]?\\s*([^.]+)",
            r"not valid under any of the given schemas"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_text, re.IGNORECASE)
            if match:
                if match.groups():
                    return f"Field validation error: {match.group(1)}"
                else:
                    return "Schema validation error"
        
        # Return first 100 chars if no specific pattern found
        return f"Unknown validation error: {error_text[:100]}..."
    
    def _add_default_required_fields(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add default values for missing required fields."""
        updated_data = entity_data.copy()
        
        for field in self.REQUIRED_FIELDS:
            if field not in updated_data or updated_data[field] is None:
                # Add reasonable defaults based on field name
                if field == "id":
                    import uuid
                    updated_data[field] = f"{self.ENTITY_TYPE.lower().split(':')[-1]}_{uuid.uuid4().hex[:8]}"
                elif field == "name":
                    updated_data[field] = updated_data.get("description", "Unnamed Entity")[:50]
                elif field == "description":
                    updated_data[field] = updated_data.get("name", "No description provided")
                else:
                    updated_data[field] = ""
        
        return updated_data
    
    def _fix_field_formats(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix common field format issues."""
        updated_data = entity_data.copy()
        
        # Convert None values to empty strings
        for key, value in updated_data.items():
            if value is None:
                updated_data[key] = ""
        
        # Fix date formats if present
        if "created" in updated_data and updated_data["created"]:
            # Ensure ISO format
            from datetime import datetime
            try:
                if isinstance(updated_data["created"], str):
                    dt = datetime.fromisoformat(updated_data["created"].replace('Z', '+00:00'))
                    updated_data["created"] = dt.isoformat()
            except ValueError:
                updated_data["created"] = datetime.now().isoformat()
        
        return updated_data
    
    @abstractmethod
    def create(self, *args, **kwargs) -> Optional[str]:
        """Create entity with entity-specific logic. Must be implemented by subclasses."""
        pass