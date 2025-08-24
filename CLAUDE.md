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

### Claude Authentication

**This system uses Claude Code CLI (native binary) to leverage the Claude Max plan via OAuth, NOT API credits.**

#### Binary Selection
- **ALWAYS use**: `/home/mike/.claude/local/claude` (native binary v1.0.83+)
- **NEVER use**: NVM binary at `/home/mike/.nvm/versions/node/v24.2.0/bin/claude` (outdated)

#### Authentication Methods

**1. Interactive Development (Default)**
- Relies on OAuth credentials at `~/.claude/.credentials.json`
- Authenticate with: `claude login`
- Credentials persist for 30-90 days
- Subprocess must have `HOME` environment variable set to find credentials

**2. Headless/CI Environments**
- Generate long-lived token: `claude setup-token`
- Export token: `export CLAUDE_CODE_OAUTH_TOKEN="Claude-..."`
- Token works without interactive login

#### MCP Execution from Python

Use the shared utility for robust subprocess execution:

```python
from voice_task_manager.utils.claude_cli import execute_claude_command

# Automatic preflight check, environment setup, and error handling
success, stdout, stderr = execute_claude_command(
    prompt="Your prompt here",
    mcp_config=".mcp.json",
    timeout=None  # No timeout for long MCP operations
)
```

Or use the lower-level utilities:

```python
from voice_task_manager.utils.claude_cli import get_claude_path, build_claude_env, preflight_claude_ok

# Build robust environment
env = build_claude_env()

# Run preflight check
ok, error_msg = preflight_claude_ok(env)
if not ok:
    print(f"Auth failed: {error_msg}")
    # Fall back to mock or handle error

# Execute command
cmd = [
    get_claude_path(),  # Always returns native binary
    "-p", prompt,
    "--dangerously-skip-permissions",
    "--mcp-config", ".mcp.json",
    "--strict-mcp-config",
    "--debug",  # Use --debug not --mcp-debug
    "--output-format", "json"
]
result = subprocess.run(cmd, cwd=PROJECT_DIR, env=env, capture_output=True, text=True, timeout=None)
```

#### Troubleshooting Authentication

**If subprocess authentication fails:**
1. Check Claude binary: `/home/mike/.claude/local/claude --version`
2. Verify credentials exist: `ls -la ~/.claude/.credentials.json`
3. Test authentication: `python scripts/debug/test_claude_auth.py`
4. Check MCP access: `USE_REAL_MCP=true python scripts/debug/test_mcp_connection.py`

**Common Issues:**
- Missing HOME environment → Can't find credentials
- Using wrong binary → Outdated CLI version
- Expired OAuth token → Run `claude login` again
- Deprecated flags → Use `--debug` not `--mcp-debug`

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