# GraphRAG Entity Management Refactor

## Executive Summary

The current GraphRAG adapter has significant architectural limitations that prevent proper entity creation and management. This document outlines the problems and provides a comprehensive implementation plan to fix them.

## Current Problems

### 1. Limited Entity Type Support

**Current State:**
- Only `create_task()` and `create_project()` methods exist
- **Missing:** `create_area()`, `create_goal()`, `create_note()`
- All entity management is crammed into `GraphRAGTaskAdapter`

**Impact:**
- Cannot create complete entity hierarchies (Area → Project → Task)
- Voice processing fails when Claude identifies areas/goals that don't exist
- No support for notes or other entity types

### 2. Vague MCP Validation Errors

**Current Error Messages:**
```
❌ ERROR: Could not extract task ID from response: {'success': True, 'result': "The entity creation is failing due to validation errors. The entity data structure appears to not match the expected schema. Without being able to see the exact schema requirements, I cannot provide the raw JSON result from the tool as it's not executing successfully."}
```

**Problems:**
- No details about which fields are missing or incorrect
- Cannot determine if it's a schema mismatch or data format issue
- Makes debugging nearly impossible

### 3. Entity Type Schema Confusion

**Current Usage:**
```python
"entity_type": "TASK_MANAGEMENT:TASK"  # Fails validation
```

**Questions:**
- Should we use `TASK` or `TASK_MANAGEMENT:TASK`?
- What are the exact required vs optional fields?
- Are there format requirements (e.g., date formats, field types)?

### 4. Poor Error Handling and Recovery

**Current Behavior:**
- Entity creation fails but task is marked as "created" using fallback ID
- No retry logic with corrected data
- No validation before sending to MCP
- Continues processing even when core functionality fails

## Proposed Architecture

### 1. Separate Entity Managers

Create dedicated managers for each entity type:

```
src/voice_task_manager/entities/
├── __init__.py
├── base_manager.py          # Base class with common functionality
├── task_manager.py          # Task-specific operations
├── project_manager.py       # Project-specific operations
├── area_manager.py          # Area-specific operations
├── goal_manager.py          # Goal-specific operations
└── note_manager.py          # Note-specific operations
```

### 2. Entity Manager Responsibilities

Each manager will:
- **Know its schema:** Exact required/optional fields
- **Validate locally:** Check data before MCP calls
- **Handle errors:** Parse MCP responses and provide clear messages
- **Manage relationships:** Create proper entity links
- **Support embeddings:** Ensure semantic search works

### 3. Updated GraphRAG Adapter

The adapter becomes an orchestrator:
```python
class GraphRAGTaskAdapter:
    def __init__(self):
        self.task_manager = TaskManager(self)
        self.project_manager = ProjectManager(self)
        self.area_manager = AreaManager(self)
        self.goal_manager = GoalManager(self)
        self.note_manager = NoteManager(self)
    
    def create_task(self, task_data: TaskData) -> Optional[str]:
        # Ensure prerequisite entities exist
        area_id = self._ensure_area_exists(task_data.area_name)
        project_id = self._ensure_project_exists(task_data.project_name, area_id)
        
        # Create task with proper relationships
        return self.task_manager.create(task_data, project_id, area_id)
```

## Implementation Plan

### Phase 1: Schema Discovery and Documentation (2-3 hours)

#### 1.1 Query Registered Schemas
```python
# Create script: scripts/debug/analyze_entity_schemas.py
# Query all registered entity schemas
# Document exact requirements for each type
```

#### 1.2 Test Entity Creation
```python
# Create script: scripts/debug/test_entity_creation.py
# Test minimal entity creation for each type
# Document what works vs what fails
```

#### 1.3 Document Schema Requirements
Create `docs/ENTITY_SCHEMAS.md` with:
- Required fields for each entity type
- Optional fields and their formats
- Relationship requirements
- Embedding configuration

### Phase 2: Base Infrastructure (3-4 hours)

#### 2.1 Create Base Manager
```python
# src/voice_task_manager/entities/base_manager.py
class BaseEntityManager:
    def __init__(self, adapter):
        self.adapter = adapter
        self.logger = adapter.logger
        
    def validate_entity(self, entity_data: Dict) -> Tuple[bool, str]:
        """Validate entity data against schema"""
        
    def create_entity(self, entity_type: str, entity_data: Dict) -> Optional[str]:
        """Create entity with validation and error handling"""
        
    def parse_mcp_response(self, response: Dict) -> Tuple[bool, Optional[str], str]:
        """Parse MCP response and extract entity ID"""
```

#### 2.2 Improve MCP Response Parsing
```python
def parse_mcp_response(self, response: Dict) -> Tuple[bool, Optional[str], str]:
    """
    Parse MCP response with detailed error analysis
    
    Returns:
        (success: bool, entity_id: Optional[str], error_message: str)
    """
    if not response.get("success", False):
        return False, None, f"MCP call failed: {response.get('error', 'Unknown error')}"
    
    # Check for Claude's interpreted response
    result_text = response.get("result", "")
    if "validation errors" in result_text.lower():
        # Try to extract specific validation errors
        validation_details = self._extract_validation_details(result_text)
        return False, None, f"Schema validation failed: {validation_details}"
    
    # Extract entity ID from various response formats
    entity_id = self._extract_entity_id(response)
    if not entity_id:
        return False, None, f"Could not extract entity ID from response: {response}"
    
    return True, entity_id, "Success"
```

### Phase 3: Implement Entity Managers (4-5 hours)

#### 3.1 Task Manager
```python
# src/voice_task_manager/entities/task_manager.py
class TaskManager(BaseEntityManager):
    ENTITY_TYPE = "TASK_MANAGEMENT:TASK"  # or "TASK" based on testing
    
    REQUIRED_FIELDS = ["id", "description"]
    OPTIONAL_FIELDS = ["name", "status", "priority", "contexts", "created", "source"]
    
    def create(self, task_data: TaskData, project_id: Optional[str] = None, 
               area_id: Optional[str] = None) -> Optional[str]:
        """Create task with validation and relationship management"""
        
    def validate_task_data(self, task_data: TaskData) -> Tuple[bool, str]:
        """Validate task data against schema"""
```

#### 3.2 Project Manager
```python
# src/voice_task_manager/entities/project_manager.py
class ProjectManager(BaseEntityManager):
    ENTITY_TYPE = "TASK_MANAGEMENT:PROJECT"
    
    def create(self, name: str, description: str, area_id: Optional[str] = None) -> Optional[str]:
        """Create project with area relationship"""
        
    def find_or_create(self, name: str, area_name: str = None) -> Optional[str]:
        """Find existing project or create new one"""
```

#### 3.3 Area Manager
```python
# src/voice_task_manager/entities/area_manager.py
class AreaManager(BaseEntityManager):
    ENTITY_TYPE = "TASK_MANAGEMENT:AREA"
    
    def create(self, name: str, description: str = "") -> Optional[str]:
        """Create new area"""
        
    def find_or_create(self, name: str) -> Optional[str]:
        """Find existing area or create new one"""
```

#### 3.4 Goal and Note Managers
Similar implementations for `GoalManager` and `NoteManager`.

### Phase 4: Update GraphRAG Adapter (2-3 hours)

#### 4.1 Refactor create_task Method
```python
def create_task(self, task_data: TaskData) -> Optional[str]:
    """Create task with prerequisite entity management"""
    
    # Ensure area exists if specified
    area_id = None
    if task_data.area_name:
        area_id = self.area_manager.find_or_create(task_data.area_name)
        if not area_id:
            self.logger.error(f"Failed to create/find area: {task_data.area_name}")
            # Continue anyway - area is optional
    
    # Ensure project exists if specified
    project_id = None
    if task_data.project_name:
        project_id = self.project_manager.find_or_create(
            task_data.project_name, 
            task_data.area_name
        )
        if not project_id:
            self.logger.error(f"Failed to create/find project: {task_data.project_name}")
            # Continue anyway - project is optional
    
    # Create task with relationships
    task_id = self.task_manager.create(task_data, project_id, area_id)
    
    if task_id:
        self.logger.success(f"Task created successfully: {task_id}")
        return task_id
    else:
        self.logger.error("Task creation failed")
        return None
```

#### 4.2 Add Missing Methods
```python
def create_area(self, name: str, description: str = "") -> Optional[str]:
    """Create new area"""
    return self.area_manager.create(name, description)

def create_goal(self, name: str, description: str, area_name: str = None) -> Optional[str]:
    """Create new goal"""
    area_id = None
    if area_name:
        area_id = self.area_manager.find_or_create(area_name)
    return self.goal_manager.create(name, description, area_id)

def create_note(self, title: str, content: str, context: str = None) -> Optional[str]:
    """Create new note"""
    return self.note_manager.create(title, content, context)
```

### Phase 5: Improve Error Handling (1-2 hours)

#### 5.1 Detailed Error Analysis
```python
def _extract_validation_details(self, error_text: str) -> str:
    """Extract specific validation errors from Claude's response"""
    
    # Look for common validation error patterns
    patterns = [
        r"required field[s]?\s*(?:is|are)?\s*missing:\s*([^.]+)",
        r"invalid format for field[s]?\s*([^.]+)",
        r"field[s]?\s*([^.]+)\s*(?:is|are)\s*required",
        r"schema mismatch.*field[s]?\s*([^.]+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, error_text, re.IGNORECASE)
        if match:
            return f"Validation error: {match.group(1)}"
    
    return f"Unknown validation error: {error_text[:100]}..."
```

#### 5.2 Retry Logic
```python
def create_with_retry(self, entity_type: str, entity_data: Dict, max_retries: int = 2) -> Optional[str]:
    """Create entity with retry logic for common fixes"""
    
    for attempt in range(max_retries + 1):
        success, entity_id, error = self.create_entity(entity_type, entity_data)
        
        if success:
            return entity_id
            
        # Try common fixes
        if attempt < max_retries:
            if "required field" in error.lower():
                entity_data = self._add_default_required_fields(entity_data)
                continue
            elif "format" in error.lower():
                entity_data = self._fix_field_formats(entity_data)
                continue
        
        self.logger.error(f"Entity creation failed after {attempt + 1} attempts: {error}")
        return None
```

### Phase 6: Testing and Validation (2-3 hours)

#### 6.1 Unit Tests
```python
# tests/unit/entities/test_task_manager.py
class TestTaskManager(unittest.TestCase):
    def test_validate_minimal_task(self):
        """Test validation with minimal required fields"""
        
    def test_validate_full_task(self):
        """Test validation with all fields"""
        
    def test_create_task_success(self):
        """Test successful task creation"""
        
    def test_create_task_validation_failure(self):
        """Test handling of validation errors"""
```

#### 6.2 Integration Tests
```python
# tests/integration/test_entity_creation.py
class TestEntityCreation(unittest.TestCase):
    def test_full_hierarchy_creation(self):
        """Test creating Area → Project → Task hierarchy"""
        
    def test_entity_relationships(self):
        """Test that relationships are created correctly"""
        
    def test_embedding_generation(self):
        """Test that embeddings are generated for all entities"""
```

#### 6.3 Manual Testing Script
```python
# scripts/debug/test_full_entity_workflow.py
def test_voice_to_entities():
    """Simulate the full voice processing workflow"""
    
    # Test data similar to actual voice processing
    test_cases = [
        {
            "transcript": "Call Dr. Smith about the test results",
            "expected_area": "Health", 
            "expected_project": "Medical Appointments",
            "expected_task": "Call Dr. Smith about test results"
        },
        {
            "transcript": "Buy soil for the garden project", 
            "expected_area": "House",
            "expected_project": "Garden renovation", 
            "expected_task": "Buy soil for garden"
        }
    ]
    
    for case in test_cases:
        print(f"Testing: {case['transcript']}")
        # Run through full workflow
        # Verify entities are created with proper relationships
```

## Success Criteria

### Functional Requirements
- [ ] Can create all entity types (Task, Project, Area, Goal, Note)
- [ ] Entities have proper relationships (Area ← Project ← Task)
- [ ] Embeddings are generated for all entities
- [ ] Validation errors provide specific details
- [ ] Failed entities can be retried with fixes
- [ ] Voice processing creates complete entity hierarchies

### Quality Requirements
- [ ] Clear error messages that enable debugging
- [ ] Graceful degradation when entities fail to create
- [ ] No more "Could not extract entity ID" errors
- [ ] Logs show specific validation issues
- [ ] All entity managers have unit tests
- [ ] Integration tests cover full workflows

### Performance Requirements
- [ ] Entity creation latency < 5 seconds per entity
- [ ] Batch entity creation for efficiency
- [ ] Minimal redundant MCP calls
- [ ] Proper caching of entity lookups

## Migration Strategy

### 1. Backward Compatibility
- Keep existing `create_task()` and `create_project()` methods
- Add new methods alongside old ones
- Gradually migrate callers to new architecture

### 2. Incremental Rollout
1. Deploy base infrastructure first
2. Replace task creation (most common)
3. Add project creation improvements  
4. Add area/goal/note creation
5. Remove old methods once migration is complete

### 3. Monitoring
- Add metrics for entity creation success rates
- Monitor validation error types
- Track relationship creation success
- Alert on schema validation failures

## Risk Mitigation

### Schema Changes
- **Risk:** MCP schema requirements change
- **Mitigation:** Centralize schema definitions, add schema versioning

### Performance Impact
- **Risk:** Multiple MCP calls slow down processing
- **Mitigation:** Batch operations, cache entity lookups, async processing

### Data Consistency
- **Risk:** Partial entity creation leaves orphaned data
- **Mitigation:** Transaction-like semantics, cleanup on failure

### Backward Compatibility
- **Risk:** Changes break existing voice processing
- **Mitigation:** Feature flags, gradual migration, comprehensive testing

## Next Steps

1. **Immediate (This Session):**
   - Create schema discovery scripts
   - Test current entity creation to understand exact failures
   - Document findings in `docs/ENTITY_SCHEMAS.md`

2. **Short Term (Next 1-2 Days):**
   - Implement base entity manager infrastructure
   - Create task manager with improved validation
   - Test with real voice processing data

3. **Medium Term (Next Week):**
   - Complete all entity managers
   - Add comprehensive testing
   - Deploy to voice processing system

4. **Long Term (Next Month):**
   - Monitor entity creation success rates
   - Add advanced features (batch creation, caching)
   - Optimize performance and reliability

This refactor will transform the GraphRAG adapter from a limited, error-prone system into a robust, extensible entity management platform that properly supports the voice task management workflow.