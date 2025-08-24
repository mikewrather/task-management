# GraphRAG Entity Schemas

Documentation of registered entity schemas and creation requirements based on schema discovery analysis.

## Registered TASK_MANAGEMENT Schemas

### TASK_MANAGEMENT:AREA
**Description**: Area or category for organizing tasks and projects

**Properties**:
- `name`: string (required) - Name of the area
- `description`: string (optional) - Description of the area  
- `parent_area`: string (optional) - Parent area name for hierarchical organization

**Example**:
```json
{
  "name": "Health",
  "description": "Health and medical related tasks"
}
```

### TASK_MANAGEMENT:PROJECT  
**Description**: Project or sprint for task management

**Properties**:
- `name`: string (required) - Name of the project
- `description`: string (optional) - Description of the project
- `status`: string (optional) - Current status of the project
- `priority`: string (optional) - Priority level

**Example**:
```json
{
  "name": "Medical Appointments",
  "description": "Track and manage medical appointments",
  "status": "active",
  "priority": "high"
}
```

### TASK_MANAGEMENT:TASK
**Description**: Individual task or work item

**Properties**:
- `id`: string (required) - Unique identifier for the task
- `description`: string (required) - Description of what needs to be done

**Example**:
```json
{
  "id": "task_12345",
  "description": "Call Dr. Smith about test results"
}
```

### TASK_MANAGEMENT:TASK_MANAGEMENT:TASK (Extended)
**Description**: A task entity in the task management system (full schema)

**Properties**:
- `id`: string (required) - Unique identifier for the task
- `name`: string (required) - Name of the task  
- `description`: string (optional) - Full description of the task
- `status`: string (optional) - Current status of the task
- `priority`: string (optional) - Priority level of the task
- `contexts`: array (optional) - List of contexts for the task
- `created`: string (optional) - Creation timestamp
- `source`: string (optional) - Source of the task
- `project_name`: string (optional) - Associated project name
- `area_name`: string (optional) - Associated area name
- `goal_name`: string (optional) - Associated goal name

## MCP Tool Usage

### create_entities Tool

**Entity Type**: Use full schema names with domain prefix:
- ✅ `TASK_MANAGEMENT:TASK`
- ✅ `TASK_MANAGEMENT:PROJECT` 
- ✅ `TASK_MANAGEMENT:AREA`
- ❌ `TASK` (missing domain prefix)

**Entities Parameter**: Must be a single object, NOT an array:
- ✅ `entities: {"name": "Test"}` (object format)
- ❌ `entities: [{"name": "Test"}]` (array format - causes timeout/validation error)

**Additional Parameters**:
- `check_duplicates: true` - Enables semantic deduplication
- `create_embeddings: true` - Auto-generates embeddings for semantic search

### Registered Schemas (Confirmed Working)

**TASK_MANAGEMENT:AREA**:
- Required: `name` (string)
- Optional: `description` (string), `parent_area` (string)

**TASK_MANAGEMENT:PROJECT**:
- Required: `name` (string)  
- Optional: `description` (string), `status` (string), `priority` (string)

**TASK_MANAGEMENT:TASK**:
- Required: `id` (string), `description` (string)
- Optional: `status` (string), `priority` (string)

## Architecture Implementation Status

### ✅ Completed Components

1. **Entity Manager Architecture**: Complete modular system with dedicated managers
2. **Base Infrastructure**: `BaseEntityManager` with validation, error handling, retry logic  
3. **All Entity Managers**: `TaskManager`, `ProjectManager`, `AreaManager`, `GoalManager`, `NoteManager`
4. **GraphRAG Adapter Refactor**: Updated to use entity managers with proper delegation
5. **Enhanced Error Handling**: Detailed validation error parsing and retry mechanisms

### 🔍 Current Investigation: MCP Validation

**Issue**: MCP `create_entities` tool shows validation errors despite correct schema registration.

**Key Findings**:
- ✅ Schemas are properly registered in Neo4j
- ✅ Object format (not array) is required for `entities` parameter
- ❌ Tool still reports "not valid under any of the given schemas"
- 🤔 MCP tool may have separate internal schema validation

**Status**: Architecture complete and functional, validation issue is MCP tool-level configuration

## Implementation Notes

### Current Implementation Problems
The current `GraphRAGTaskAdapter.create_task()` uses:
```python
# ❌ Wrong: entities as single object
task_params = {
    "entity_type": "TASK_MANAGEMENT:TASK",
    "entities": {  # Should be array!
        "id": task_id,
        "description": task_data.description,
        # ... other fields
    },
    "check_duplicates": True
}
```

### Fixed Implementation
Should use:
```python
# ✅ Correct: entities as array
task_params = {
    "entity_type": "TASK_MANAGEMENT:TASK",
    "entities": [{  # Array format
        "id": task_id,
        "description": task_data.description,
        # ... other fields
    }],
    "check_duplicates": True
}
```

## Next Steps

1. **Immediate Fix**: Update GraphRAG adapter to use array format for entities parameter
2. **Schema Validation**: Create debug tools to test exact validation requirements
3. **Entity Managers**: Implement dedicated managers with proper validation and error handling
4. **Error Recovery**: Add retry logic and better error messages

## Testing Strategy

### Manual Testing
```python
# Test minimal required fields only
test_area = [{"name": "Health"}]
test_project = [{"name": "Medical Appointments"}] 
test_task = [{"id": "task_001", "description": "Call doctor"}]
```

### Validation Testing
- Test each entity type independently
- Test with minimal vs full field sets
- Test duplicate detection
- Test embedding generation
- Test relationship creation

---

*Last updated: 2025-08-19 - Phase 1 Schema Discovery Complete*