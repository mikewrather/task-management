# Notion Chat Feature Development Plan

## Overview

This document outlines the development plan for integrating natural language chat functionality with the existing Voice Task Management System. The goal is to enable conversational querying, listing, and management of Notion data (tasks, projects, areas, notes) using Claude Code as the natural language interface.

## Architecture

### High-Level Flow
```
User Natural Language Query
         ↓
Claude Code (NL Parsing)
         ↓
CLI Command Construction
         ↓
Voice Task Manager CLI
         ↓
Notion API Integration
         ↓
Formatted Response
```

### Key Components

1. **Claude Code Integration**: Acts as the natural language processor
2. **Extended CLI Interface**: New commands for querying and managing Notion data
3. **Enhanced NotionClient**: Extended querying capabilities across all databases
4. **Query Engine**: Translates natural language to structured queries
5. **Response Formatter**: Presents data in conversational format

## Current System Integration Points

### Existing Infrastructure to Leverage
- **NotionClient** (`src/voice_task_manager/integrations/notion.py`)
- **VoiceDatabase** (`src/voice_task_manager/utils/database.py`)
- **CLI Framework** (`src/voice_task_manager/cli.py`) - Click-based with Rich output
- **Data Models**: `NotionTask` model as foundation for additional models

### Notion Databases Available
- **Tasks DB**: `183267fb-e1c1-4b3b-a42a-5ac1ab8353eb`
- **Projects DB**: `9abc79db-e5c2-4046-b812-585804df2e41`
- **Areas DB**: `f71ab7c6-ac29-4b00-99a1-5eb44156a2bf`
- **Notes DB**: `eb339471-752a-4090-b93e-39079a661098`

## Implementation Phases

### Phase 1: Foundation - Basic Query Infrastructure
**Goal**: Establish core CLI commands for structured data retrieval

#### New CLI Commands
1. **`vtm list`** - Structured listing commands
   ```bash
   vtm list tasks [--status] [--context] [--project] [--area] [--format json|table|rich]
   vtm list projects [--area] [--active-only] [--format json|table|rich]
   vtm list areas [--format json|table|rich]
   vtm list notes [--recent] [--project] [--format json|table|rich]
   ```

2. **`vtm search`** - Text-based search across databases
   ```bash
   vtm search "meeting notes" [--database tasks|projects|areas|notes|all]
   vtm search "overdue" [--in-transcripts] [--in-content]
   ```

3. **`vtm filter`** - Advanced filtering capabilities
   ```bash
   vtm filter tasks --status="Next Action" --created-after="2025-01-01"
   vtm filter tasks --context="voice" --priority="High"
   ```

#### Required Components
- **Enhanced Data Models**: `NotionProject`, `NotionArea`, `NotionNote` classes
- **Query Builder**: Database query construction utilities
- **Response Formatters**: JSON, table, and Rich console output
- **Filter Engine**: Advanced filtering logic
- **Intelligent Help System**: Context-aware parameter validation and suggestion

### Phase 2: Natural Language Interface
**Goal**: Enable natural language queries through Claude Code integration

#### New CLI Commands
1. **`vtm query`** - Natural language interface
   ```bash
   vtm query "show me my overdue tasks"
   vtm query "what projects am I working on this week?"
   vtm query "find meeting notes from last month"
   vtm query "tasks in my inbox that need attention"
   ```

#### Query Translation Examples
| Natural Language | CLI Command |
|------------------|-------------|
| "show me overdue tasks" | `vtm filter tasks --due-before=today --status!="Completed"` |
| "what's in my inbox?" | `vtm list tasks --status="Inbox"` |
| "recent voice notes" | `vtm list tasks --context="voice" --created-after="7 days ago"` |
| "high priority items" | `vtm filter tasks --priority="High,Urgent" --status!="Completed"` |
| "next actions for computer work" | `vtm list tasks --status="Next Action" --context="Computer"` |
| "waiting on items from last week" | `vtm filter tasks --status="Waiting On" --created-after="last week"` |
| "active projects in progress" | `vtm list projects --status="In Progress"` |
| "voice tasks that need review" | `vtm filter tasks --context="voice,needs-review" --status="Inbox"` |
| "someday items about mobile development" | `vtm filter tasks --status="Someday" --context="Mobile Development"` |

#### Required Components
- **Natural Language Parser**: Integration with Claude Code
- **Query Intent Recognition**: Classify query types (list, filter, search, stats)
- **Date Parser**: Natural language date interpretation
- **Context Manager**: Multi-turn conversation support

### Phase 3: Advanced Management Features
**Goal**: Enable task modification and advanced operations via chat

#### Extended Functionality
1. **Task Management Commands**
   ```bash
   vtm update task <id> --status="Next Action"
   vtm complete task <id>
   vtm create task "New task description" [--project] [--area] [--priority]
   ```

2. **Bulk Operations**
   ```bash
   vtm bulk complete --filter="context:voice AND status:Inbox"
   vtm bulk update --filter="project:Website" --status="Next Action"
   ```

3. **Analytics and Insights**
   ```bash
   vtm analyze productivity [--timeframe="last month"]
   vtm analyze contexts --usage-stats
   vtm analyze projects --completion-rates
   ```

## Testing Strategy

### Test-Driven Development Requirements
> **CRITICAL**: Every new piece of functionality MUST have tests written before or during development. Tests MUST be run during development to ensure they pass.

### Test Types

#### 1. Unit Tests
- **Query Engine Tests**: Natural language parsing accuracy
- **Data Model Tests**: NotionProject, NotionArea, NotionNote model validation
- **Filter Engine Tests**: Query construction and validation
- **Response Formatter Tests**: Output format consistency

#### 2. Integration Tests
- **CLI Command Tests**: All new CLI commands with various options
- **Notion API Tests**: Database queries and operations
- **Database Tests**: Local SQLite operations and caching
- **Help System Tests**: Parameter validation and error message accuracy

#### 3. End-to-End Tests
- **Natural Language Flow**: Complete NL → CLI → Notion → Response pipeline
- **Multi-turn Conversations**: Context preservation across queries
- **Error Handling**: Graceful handling of invalid queries and API errors

### Testing Framework
- **Primary**: pytest (existing framework)
- **CLI Testing**: Click testing utilities
- **API Mocking**: For Notion API calls during testing
- **Test Data**: Sanitized sample data for comprehensive testing

### Test Organization
```
tests/
├── unit/
│   ├── test_query_engine.py
│   ├── test_notion_models.py
│   ├── test_response_formatters.py
│   └── test_parameter_validation.py  # Help system validation tests
├── integration/
│   ├── test_cli_commands.py
│   ├── test_notion_integration.py
│   ├── test_database_operations.py
│   └── test_help_system.py           # Invalid parameter response tests  
└── e2e/
    ├── test_natural_language_flow.py
    └── test_conversation_context.py
```

### Help System Test Requirements
- **Invalid Parameter Tests**: Verify helpful error messages for all invalid inputs
- **Dynamic Help Tests**: Ensure help content reflects current database state
- **Fuzzy Matching Tests**: Validate suggestion accuracy for similar inputs
- **Error Format Tests**: Consistent error message formatting across all commands

## Intelligent Help System Design

> **📊 Based on Actual Database Schema**: All valid field values below are from the current production Notion database schema analyzed on 2025-07-25. See `/docs/NOTION_DATABASE_SCHEMA_ANALYSIS.md` for complete details.

### Context-Aware Parameter Validation
> **CRITICAL UX REQUIREMENT**: When users provide invalid parameters, the system MUST respond with all valid options rather than just throwing an error.

#### Help System Behavior Examples

**Invalid Status Parameter**:
```bash
$ vtm list tasks --status=InvalidStatus
❌ Error: 'InvalidStatus' is not a valid status.

✅ Valid status options (from current Tasks database):
  • Inbox (new, unprocessed items)
  • Next Action (ready to work on)  
  • Waiting On (blocked by external dependencies)
  • Someday (future consideration)
  • Completed (finished items)

💡 Example: vtm list tasks --status="Next Action"
```

**Invalid Context Parameter**:
```bash
$ vtm filter tasks --context=badcontext
❌ Error: 'badcontext' is not a valid context.

✅ Available contexts (from current Tasks database):
  Location-based: Phone, Computer, Home
  Action-based: Email, Online Shopping
  Domain-based: Digital Marketing, Mobile Development, Infrastructure
  System-generated: voice, voice-created, auto-processed, needs-review, test

💡 Example: vtm filter tasks --context=voice,Computer
```

**Invalid Date Format**:
```bash
$ vtm filter tasks --created-after=baddate
❌ Error: Could not parse date 'baddate'.

✅ Supported date formats:
  • ISO format: 2025-07-25
  • Relative: "7 days ago", "last week", "yesterday"
  • Keywords: "today", "tomorrow"

💡 Example: vtm filter tasks --created-after="last week"
```

**Invalid Priority Parameter**:
```bash
$ vtm filter tasks --priority=invalid
❌ Error: 'invalid' is not a valid priority level.

✅ Valid priority options (from current database):
  • Low (when time allows)
  • Medium (normal priority - default)
  • High (important, soon)
  • Urgent (immediate attention required)

💡 Example: vtm filter tasks --priority=High,Urgent
```

**Invalid Energy Parameter**:
```bash
$ vtm list tasks --energy=badlevel
❌ Error: 'badlevel' is not a valid energy level.

✅ Valid energy levels (from current database):
  • Low (light, routine tasks)
  • Medium (moderate effort)
  • High (significant concentration needed)
  • Extreme (high focus, complex work)

💡 Example: vtm list tasks --energy=High --status="Next Action"
```

**Invalid Project Status**:
```bash
$ vtm list projects --status=invalid
❌ Error: 'invalid' is not a valid project status.

✅ Valid project status options (from Projects database):
  • Inbox (new, unprocessed projects)
  • Not Started (approved but not begun)
  • In Progress (currently active)
  • On Hold (temporarily paused)
  • Completed (finished projects)

💡 Example: vtm list projects --status="In Progress"
```

**Invalid Area Status**:
```bash
$ vtm list areas --status=invalid
❌ Error: 'invalid' is not a valid area status.

✅ Valid area status options (from Areas database):
  • Inbox (new areas of responsibility)
  • Not Started (identified but not active)
  • In Progress (actively maintained)
  • On Hold (temporarily inactive)
  • Completed (no longer relevant)

💡 Example: vtm list areas --status="In Progress"
```

> **📋 Complete Database Schema**: For full details on all database properties, relationships, and current data, see `/docs/NOTION_DATABASE_SCHEMA_ANALYSIS.md`

#### Help Command Design

**Comprehensive Help for Each Command**:
```bash
# Standard help
$ vtm list tasks --help

# Dynamic help based on database state
$ vtm list --help-parameters
Shows all available values for each parameter based on current Notion data:
  • Available statuses (from actual task data)
  • Available contexts (from actual task data)  
  • Available projects (from Projects database)
  • Available areas (from Areas database)
```

#### Implementation Requirements

1. **Parameter Validation Classes**: Each command parameter has a validator that:
   - Validates input against known good values
   - Fetches current valid options from Notion when needed
   - Provides helpful error messages with examples

2. **Dynamic Help Generation**: Help text is generated from actual database state:
   - Status options from current tasks
   - Context options from current tasks
   - Project/Area options from respective databases

3. **Consistent Error Format**: All parameter errors follow the same pattern:
   - Clear error message explaining what's wrong
   - List of valid options
   - Example of correct usage
   - Suggestion for related help command

4. **Fuzzy Matching**: When possible, suggest closest valid option:
   ```bash
   $ vtm list tasks --status=inbox
   ❌ Error: 'inbox' is not a valid status.
   💡 Did you mean 'Inbox'? (case-sensitive)
   ```

## Implementation Prerequisites

> **🔧 Critical technical details that must be resolved before starting Phase 1 implementation**

### Natural Language Processing Architecture

**MCP-Style Tool Call Approach**:
The natural language processing will work similarly to MCP tool calls, where Claude Code:
1. Parses natural language query into structured intent
2. Maps intent to appropriate CLI command with parameters  
3. Executes CLI command via Bash tool
4. Interprets CLI output and presents conversationally

**Advantages of This Approach**:
- Leverages Claude Code's existing natural language capabilities
- No need to build custom NLP parsing into the Python application
- CLI commands remain testable and usable independently
- Avoids loading CLI documentation into context repeatedly

**Implementation Pattern**:
```python
# Claude Code internally maps:
"show me overdue tasks" → bash_command("vtm filter tasks --due-before=today --status!=Completed")
# Then interprets JSON output conversationally
```

### Data Model Specifications

#### NotionTask Model (Existing - Enhanced)
```python
@dataclass
class NotionTask:
    task_id: str
    title: str
    status: str  # Inbox|Next Action|Waiting On|Someday|Completed
    priority: str  # Low|Medium|High|Urgent
    energy: str  # Low|Medium|High|Extreme
    contexts: List[str]  # Phone,Computer,Home,Email,etc.
    project_id: Optional[str] = None
    area_id: Optional[str] = None
    due_date: Optional[datetime] = None
    created_time: datetime
    # ... existing fields
```

#### NotionProject Model (New)
```python
@dataclass
class NotionProject:
    project_id: str
    name: str
    status: str  # Inbox|Not Started|In Progress|On Hold|Completed
    priority: str  # Low|Medium|High|Urgent
    area_id: Optional[str] = None
    timeline: Optional[DateRange] = None
    progress: Optional[float] = None  # From rollup
    created_time: datetime
    archive: bool = False
```

#### NotionArea Model (New)
```python
@dataclass  
class NotionArea:
    area_id: str
    name: str
    status: str  # Inbox|Not Started|In Progress|On Hold|Completed
    priority: str  # Low|Medium|High|Urgent
    timeline: Optional[DateRange] = None
    progress: Optional[float] = None  # From rollup
    created_time: datetime
    archive: bool = False
```

### Performance & Caching Strategy

**Response Time Requirements**:
- **Target**: < 2 seconds for simple queries (single database)
- **Acceptable**: < 5 seconds for complex queries (cross-database)
- **Fallback**: Cached results with freshness indicator if API slow

**Caching Implementation**:
```python
# Local SQLite cache for frequently accessed data
class NotionCache:
    def get_valid_options(self, database: str, property: str) -> List[str]:
        # Cache status/priority/context options for help system
        
    def get_recent_items(self, database: str, limit: int = 50) -> List[dict]:
        # Cache recent items for quick listing
        
    def invalidate_cache(self, max_age_minutes: int = 30):
        # Refresh cache when data might be stale
```

**Rate Limiting Protection**:
- Implement request throttling (max 10 requests/minute to Notion API)
- Batch requests when possible
- Graceful degradation to cached data during rate limits

### CLI Pattern Alignment

**Error Handling Standardization**:
All new commands must follow existing Rich console patterns:
```python
# Existing pattern (from current codebase):
console.print(f"❌ Error: {message}", style="red")
console.print(f"💡 Suggestion: {suggestion}", style="blue")

# Help system responses must use Rich formatting:
console.print("✅ Valid options:", style="green")
for option in valid_options:
    console.print(f"  • {option}", style="dim")
```

**Verbose Flag Integration**:
```python
# New commands must integrate with existing verbose context:
@click.pass_context
def list_tasks(ctx, **kwargs):
    verbose = ctx.obj.get('verbose', False)
    if verbose:
        console.print("🔍 Querying Notion API...", style="dim")
```

**JSON Output Consistency**:
All commands with `--format json` must return consistent structure:
```json
{
    "success": true,
    "data": [...],
    "metadata": {
        "total_count": 42,
        "query_time_ms": 1250,
        "cached": false
    },
    "timestamp": "2025-07-25T14:30:00Z"
}
```

### Database Schema Handling

**Schema Validation on Startup**:
```python
class NotionSchemaValidator:
    def validate_database_schema(self, db_id: str) -> SchemaValidationResult:
        # Verify expected properties exist
        # Check for schema changes since last run
        # Provide migration suggestions if needed
```

**Graceful Schema Evolution**:
- If new properties appear: log warning, continue operation
- If properties disappear: fallback to alternative fields or cached data
- If property types change: attempt conversion, fail gracefully

## Technical Implementation Details

### New File Structure
```
src/voice_task_manager/
├── core/
│   ├── query_engine.py          # Natural language processing
│   ├── response_formatter.py    # Output formatting
│   └── parameter_validator.py   # Help system and validation logic
├── models/
│   ├── notion_project.py        # Project data model
│   ├── notion_area.py           # Area data model
│   └── notion_note.py           # Note data model
├── integrations/
│   └── notion.py                # Extended with new query methods
└── cli/
    ├── query_commands.py        # New query-related CLI commands
    ├── management_commands.py   # Task management CLI commands
    └── help_system.py           # Intelligent help and error handling
```

### Database Schema Extensions
- **Query Cache**: Store frequently accessed Notion data locally
- **Conversation Context**: Track multi-turn conversation state
- **Query History**: Log successful queries for learning and optimization

## Development Workflow

### Session Management
1. **Planning Document Updates**: Update this document as implementation progresses
2. **Progress Tracking**: Use TodoWrite tool to track development milestones
3. **Test Execution**: Run tests after each component completion
4. **Documentation**: Update CLI help text and user documentation

### Milestone Checkpoints
- [ ] **Phase 1 Complete**: Basic CLI commands working with full test coverage
- [ ] **Phase 2 Complete**: Natural language queries functional via Claude Code
- [ ] **Phase 3 Complete**: Advanced management features implemented
- [ ] **Documentation Complete**: User guide and API reference updated
- [ ] **Production Ready**: Full test suite passing, error handling robust

## Integration with Existing System

### Backward Compatibility
- All existing voice processing functionality remains unchanged
- New chat features are additive, not replacement
- Existing CLI commands continue to work as before

### Data Consistency
- Voice-generated tasks remain fully compatible with chat interface
- Unified data models ensure consistency across interfaces
- Archive and cleanup systems work with both voice and chat-created data

### Notification Integration
- Chat-initiated task changes trigger same notification system
- Desktop notifications work for both voice and chat operations
- Unified logging across all system interactions

## Success Criteria

### Functional Requirements
- [ ] Users can query Notion data using natural language
- [ ] All CRUD operations available via chat interface
- [ ] Multi-database queries work seamlessly
- [ ] Natural language date parsing works accurately
- [ ] Conversation context preserved across queries

### Technical Requirements
- [ ] 100% test coverage for new functionality
- [ ] All tests passing continuously during development
- [ ] Response times under 2 seconds for typical queries
- [ ] Robust error handling and user feedback
- [ ] CLI follows existing patterns and conventions

### User Experience Requirements
- [ ] Intuitive natural language command structure
- [ ] Helpful error messages and suggestions
- [ ] **Intelligent help system**: Invalid parameters show all valid options with examples
- [ ] Consistent output formatting across commands
- [ ] Comprehensive help and documentation
- [ ] Seamless integration with existing workflow

## Risk Mitigation

### Technical Risks
- **Notion API Rate Limits**: Implement caching and request throttling
- **Natural Language Ambiguity**: Provide clarification prompts and examples
- **Data Consistency**: Implement validation and rollback mechanisms

### Development Risks
- **Scope Creep**: Stick to phased approach, resist feature expansion
- **Testing Complexity**: Start with simple tests, build complexity gradually
- **Integration Issues**: Test integration points early and frequently

## Future Enhancements

### Potential Extensions
- **Voice Command Integration**: "Show me my tasks" via voice
- **Smart Suggestions**: AI-powered task prioritization and organization
- **Team Collaboration**: Shared workspaces and task assignment
- **Mobile Interface**: Extend chat functionality to mobile apps
- **Automation Rules**: Custom triggers and actions based on task patterns

---

**Document Status**: Initial Draft  
**Last Updated**: 2025-07-25  
**Next Review**: After Phase 1 completion  
**Maintainer**: Voice Task Management System