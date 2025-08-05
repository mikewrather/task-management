# Notion Removal Design Document

## Executive Summary

This document outlines the comprehensive plan to remove all Notion dependencies from the Voice Task Management system and transition to a pure GraphRAG/Neo4j architecture. This change will eliminate ID confusion, simplify the codebase, and create a more maintainable system with a single source of truth.

## Current Architecture Problems

### 1. ID System Confusion
- **Dual ID Systems**: The system currently maintains both `notion_id` (UUID strings) and GraphRAG node IDs (integers)
- **Mixed References**: Claude processor receives context with `notion_id` values but creates relationships using GraphRAG node IDs
- **Adapter Confusion**: Two parallel adapters (Notion and GraphRAG) trying to maintain consistency

### 2. Project Creation Ambiguity
When Claude suggests creating a project:
- The `area_id` in the suggestion could be either a Notion UUID or GraphRAG node ID
- No clear way to differentiate between "create new" vs "link to existing"
- Relationship creation fails due to ID type mismatches

### 3. Maintenance Complexity
- Dual adapter maintenance increases code complexity
- Synchronization issues between Notion and GraphRAG
- Configuration complexity with multiple environment variables

## Proposed Architecture

### Single Source of Truth: GraphRAG/Neo4j
- All entities (Tasks, Projects, Areas, Goals) stored in Neo4j
- Single ID system: Neo4j node IDs
- Direct relationships managed through Cypher queries
- MCP server (agent-db) as the primary interface

### Simplified ID Management
- Remove all `notion_id` fields from data models
- Use only Neo4j node IDs for relationships
- Clear distinction between node creation and relationship establishment

## Detailed Implementation Plan

### Phase 1: Remove Notion-Specific Files

#### Files to Delete:
```
src/voice_task_manager/adapters/notion.py
src/voice_task_manager/integrations/notion.py
src/voice_task_manager/models/notion_*.py (6 files)
  - notion_area.py
  - notion_event.py
  - notion_goal.py
  - notion_note.py
  - notion_project.py
  - notion_reference.py
tests/test_notion_integration.py
tests/test_integrations/test_notion_integration.py
```

#### Impact:
- Removes ~3000+ lines of Notion-specific code
- Eliminates all Notion API dependencies
- Simplifies the import structure

### Phase 2: Update Base Models

#### TaskData Model (`adapters/base.py`)
**Current Structure:**
```python
@dataclass
class TaskData:
    name: str
    description: str
    status: str = "Inbox"
    priority: str = "Medium"
    contexts: List[str] = None
    project_id: Optional[str] = None  # Currently Notion UUID
    project_name: Optional[str] = None
    area_id: Optional[str] = None     # Currently Notion UUID
    area_name: Optional[str] = None
    goal_id: Optional[str] = None      # Currently Notion UUID
    goal_name: Optional[str] = None
    source: str = "manual"
    metadata: Dict[str, Any] = None
```

**New Structure:**
```python
@dataclass
class TaskData:
    name: str
    description: str
    status: str = "Inbox"
    priority: str = "Medium"
    contexts: List[str] = None
    project_node_id: Optional[int] = None  # GraphRAG node ID
    project_name: Optional[str] = None
    area_node_id: Optional[int] = None     # GraphRAG node ID
    area_name: Optional[str] = None
    goal_node_id: Optional[int] = None      # GraphRAG node ID
    goal_name: Optional[str] = None
    source: str = "manual"
    metadata: Dict[str, Any] = None
```

### Phase 3: Update GraphRAG Adapter

#### Key Changes to `adapters/graphrag.py`:

1. **Remove notion_id References**
   - Update all Cypher queries to remove `notion_id` properties
   - Change relationship queries to use node IDs directly

2. **Simplify Context Retrieval**
   ```python
   def get_categorization_context(self) -> Dict[str, Any]:
       """Get context for categorization from GraphRAG"""
       # Return entities with their node IDs, not notion_ids
       return {
           "projects": [
               {
                   "node_id": 123,
                   "name": "Project Name",
                   "area_node_id": 456,
                   "area_name": "Area Name"
               }
           ],
           "areas": [
               {
                   "node_id": 456,
                   "name": "Area Name"
               }
           ]
       }
   ```

3. **Clear Node Creation**
   ```python
   def create_project(self, name: str, description: str, area_node_id: Optional[int]) -> Optional[int]:
       """Create a new project and optionally link to existing area"""
       # Create project node
       # If area_node_id provided, create BELONGS_TO relationship
       # Return new project's node ID
   ```

### Phase 4: Update Claude Processor

#### Changes to `processors/claude_processor.py`:

1. **Update Prompt Instructions**
   - Remove references to notion_id
   - Clarify that all IDs are GraphRAG node IDs
   - Update examples to use node IDs

2. **Simplify Project Creation Logic**
   ```python
   "suggested_project": {
       "name": "Project Name",
       "description": "Project Description",
       "area_node_id": 456,  # Existing area's node ID
       "create_area": false  # Explicitly state if area exists
   }
   ```

3. **Clear Relationship Handling**
   ```python
   def _create_project_if_needed(self, suggested_project: Dict[str, Any]) -> Tuple[Optional[int], Optional[str]]:
       """Create project and return (node_id, name)"""
       area_node_id = suggested_project.get("area_node_id")
       
       # If area doesn't exist and should be created
       if suggested_project.get("create_area"):
           area_node_id = self._create_area(suggested_project.get("area_name"))
       
       # Create project with clear node ID reference
       project_node_id = self.adapter.create_project(
           name=suggested_project["name"],
           description=suggested_project.get("description", ""),
           area_node_id=area_node_id
       )
       
       return project_node_id, suggested_project["name"]
   ```

### Phase 5: Update Core Processors

#### VoiceProcessorV2 (`core/processor_v2.py`)
- Remove `ENABLE_NOTION_ADAPTER` environment variable check
- Remove NotionTaskAdapter imports and initialization
- Simplify to single GraphRAG adapter usage

#### CLI (`cli.py`)
- Remove Notion-related command options
- Update help text to reflect GraphRAG-only operation
- Remove Notion configuration validation

### Phase 6: Update Configuration

#### Environment Variables to Remove:
```
NOTION_TOKEN
NOTION_DATABASE_ID
NOTION_TASKS_DB
NOTION_PROJECTS_DB
NOTION_AREAS_DB
NOTION_GOALS_DB
NOTION_EVENTS_DB
NOTION_NOTES_DB
NOTION_REFERENCES_DB
ENABLE_NOTION_ADAPTER
```

#### Update `.env.example`:
- Remove all Notion-related variables
- Add clear GraphRAG/Neo4j configuration section
- Simplify to essential variables only

### Phase 7: Update Tests

#### Remove Notion Tests:
- Delete all Notion-specific test files
- Update integration tests to use GraphRAG only

#### Update Existing Tests:
- Modify mock data to use node IDs instead of UUIDs
- Update assertions to check for integer IDs
- Simplify test setup without Notion configuration

### Phase 8: Update Database Schema

#### SQLite Database (`processed_files.db`):
- Update tasks table to store GraphRAG node IDs
- Remove any notion_id columns if present
- Add migration script for existing data

### Phase 9: Update MCP Configuration

#### Remove from `.mcp.json`:
- notion-task-management server (if custom)
- notionApi server configuration

#### Update Documentation:
- Remove references to Notion integration
- Update setup instructions
- Clarify GraphRAG as sole storage backend

## Migration Strategy

### For Existing Data:
1. Export any critical data from Notion before removal
2. Map existing Notion IDs to GraphRAG node IDs where needed
3. Update any stored references in SQLite database
4. Provide migration script for users with existing installations

### Rollback Plan:
1. Git commit before starting removal
2. Tag release as "last-notion-support"
3. Document Notion removal in changelog
4. Keep notion adapter code in a separate branch if needed

## Benefits of This Change

### 1. Simplified Architecture
- Single storage backend
- One ID system
- Clearer data flow

### 2. Improved Reliability
- No synchronization issues
- Consistent relationships
- Predictable behavior

### 3. Easier Maintenance
- Less code to maintain
- Simpler debugging
- Clearer error messages

### 4. Better Performance
- Single database queries
- No cross-system synchronization
- Direct relationship traversal

### 5. Clearer Project Creation
- Unambiguous node references
- Explicit creation vs linking
- Consistent ID types

## Implementation Timeline

1. **Phase 1-3**: Core removal and model updates (2-3 hours)
2. **Phase 4-5**: Processor updates (1-2 hours)
3. **Phase 6-7**: Configuration and test updates (1 hour)
4. **Phase 8-9**: Database and documentation updates (1 hour)
5. **Testing**: Full system testing (1 hour)

**Total Estimated Time**: 6-8 hours

## Risk Assessment

### Low Risk:
- File deletion is reversible via git
- Changes are well-scoped
- Single storage system is simpler

### Medium Risk:
- Existing users may have Notion dependencies
- Some features might be Notion-specific
- Test coverage might decrease temporarily

### Mitigation:
- Comprehensive testing before merge
- Clear migration documentation
- Maintain notion-support branch

## Success Criteria

1. All Notion code removed
2. System operates with GraphRAG only
3. Project creation works reliably
4. All tests pass
5. No notion_id references remain
6. Clear documentation updated

## Conclusion

Removing Notion will significantly simplify the Voice Task Management system, eliminate ID confusion, and create a more maintainable codebase. The change aligns with the project's evolution toward GraphRAG as the primary knowledge store and will make future enhancements easier to implement.