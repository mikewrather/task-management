# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Voice Task Management system that automatically converts voice recordings into organized tasks using pure GraphRAG (Neo4j) knowledge graph storage. The system integrates Google Drive, OpenAI Whisper, Claude AI, and MCP (Model Context Protocol) servers.

## Python Best Practices & Structure

This project follows Python best practices with a clean package structure:

### Package Structure
```
task-management/
├── src/voice_task_manager/      # Main package (following src layout)
│   ├── __init__.py             # Package initialization
│   ├── cli.py                  # CLI entry point
│   ├── adapters/               # Storage adapters
│   ├── core/                   # Core business logic
│   ├── integrations/           # External service integrations
│   ├── models/                 # Data models
│   ├── processors/             # Processing logic
│   └── utils/                  # Utility functions
├── tests/                      # Test suite (mirrors src structure)
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── e2e/                    # End-to-end tests
├── scripts/                    # Maintenance and utility scripts
│   ├── debug/                  # Debugging utilities
│   ├── analysis/               # Analysis tools
│   └── maintenance/            # System maintenance
├── docs/                       # Documentation
├── pyproject.toml             # Project configuration (PEP 621)
├── uv.lock                    # Dependency lock file
└── .env.example               # Environment template
```

### Key Principles
- **Package Manager**: Use `uv` exclusively (not pip/venv)
- **Source Layout**: All code in `src/` directory
- **Testing**: Comprehensive test coverage with pytest
- **Type Hints**: Full type annotations throughout
- **Code Quality**: Enforced with black, ruff, and mypy
- **No Root Scripts**: All scripts organized in appropriate directories

## Key Commands

### Development Setup
```bash
# Using uv (recommended - faster dependency resolution)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev,mcp]"

# Run tests
pytest
pytest tests/test_integrations/test_notion_integration.py -v  # Specific test file

# Linting and formatting
black src/ tests/
ruff check src/ tests/
mypy src/

# Run the voice processing pipeline
vtm process  # or python -m voice_task_manager.cli process
```

### MCP Inspector (Interactive Testing)
```bash
# Start MCP Inspector dashboard for testing Notion tools
mcp dev notion_mcp_server.py
# Opens at: http://localhost:6274

# Or use the demo script
./scripts/demo-mcp-inspector.sh
```

## Architecture Overview

### Core Components

1. **GraphRAG Storage Architecture** (`src/voice_task_manager/adapters/`)
   - `base.py`: Defines TaskAdapter interface and TaskData model
   - `graphrag.py`: GraphRAG/Neo4j integration for knowledge graph storage
   - Pure GraphRAG implementation for all task storage

2. **Voice Processing Pipeline** (`src/voice_task_manager/core/processor_v2.py`)
   - Enhanced processor with GraphRAG storage integration
   - Processes voice files through: Discovery → Download → Transcription → AI Analysis → Task Creation
   - Handles file cleanup and state management

3. **Claude AI Integration** (`src/voice_task_manager/processors/claude_processor.py`)
   - Intelligent task categorization using Claude with MCP access
   - Extracts tasks, projects, areas, and relationships from transcripts
   - Handles multi-task voice memos by focusing on primary task

4. **MCP Servers** (`.mcp.json`)
   - **agent-db**: GraphRAG database operations via Neo4j

### Database Schema

**SQLite** (`data/processed_files.db`):
- `processed_files`: Tracks voice file processing status
- `tasks`: Local record of created tasks

**GraphRAG** (Neo4j):
- Nodes: TASK, PROJECT, AREA, GOAL
- Relationships: BELONGS_TO, RELATES_TO, CONTRIBUTES_TO

## Critical Implementation Details

### MCP Execution from Python

When calling Claude with MCP tools from subprocess:

```python
# CORRECT: Change to project directory first
os.chdir("/home/mike/development/task-management")
cmd = [
    "/home/mike/.nvm/versions/node/v24.2.0/bin/claude",
    "-p", prompt,  # -p takes the PROMPT text, NOT project name!
    "--dangerously-skip-permissions",
    "--output-format", "json"
]
# Set timeout=None for long-running MCP operations (30-60s typical)
result = subprocess.run(cmd, timeout=None, capture_output=True, text=True)
```

### GraphRAG Configuration

In `.env`:
```bash
# GraphRAG Configuration (Required)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Use real MCP vs mock implementation
USE_REAL_MCP=true  # Set to false for testing without MCP servers

# Use Claude for intelligent categorization
USE_CLAUDE_PROCESSOR=true

# File cleanup
CLEANUP_PROCESSED_FILES=true  # Move files to processed/ folder
```

### Error Handling Patterns

The system uses comprehensive error handling with fallbacks:
- GraphRAG operations fall back to mock implementation if MCP fails
- Failed voice files are marked with status and can be retried
- Detailed logging in `logs/voice-automation.log` and `logs/voice-errors.log`

## Known Issues

1. **GraphRAG Adapter**: `get_categorization_context()` expects dict but receives list from MCP cypher queries (line 384, 390 in `adapters/graphrag.py`)

2. **MCP Performance**: Each Claude subprocess call takes 30-60 seconds due to initialization overhead

3. **Project-Area Relationships**: Projects in GraphRAG have null area_name, preventing proper relationship discovery

## Testing Considerations

- Integration tests require proper `.env` configuration
- Mock implementations available for testing without external services
- Use `USE_REAL_MCP=false` for unit testing GraphRAG functionality

## File Organization

```
task-management/
├── src/voice_task_manager/     # Main package
│   ├── adapters/               # Storage adapters (Notion, GraphRAG)
│   ├── core/                   # Core processing logic
│   ├── processors/             # Claude AI integration
│   └── integrations/           # External service integrations
├── scripts/                    # Utility scripts
│   ├── debug/                  # Debugging utilities (not for production)
│   ├── analysis/               # Log and performance analysis
│   └── maintenance/            # System maintenance and cleanup
├── tests/                      # Test suites
│   ├── unit/                   # Unit tests for individual components
│   ├── integration/            # Integration tests with external services
│   └── e2e/                    # End-to-end workflow tests
├── logs/                       # Runtime logs
├── data/                       # SQLite database and results
└── notion_mcp_server.py        # MCP server for Notion operations
```

## Maintaining Code Quality

### Structure Verification
```bash
# Check project structure compliance
python scripts/maintenance/check_project_structure.py
```

### Code Quality Tools
```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/

# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Development Workflow
1. All new scripts go in `scripts/` subdirectories, never in root
2. Use type hints for all function signatures
3. Write unit tests for new functionality
4. Run structure checker before committing
5. Use `uv` for all dependency management