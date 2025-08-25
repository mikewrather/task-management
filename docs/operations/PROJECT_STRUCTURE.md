# Voice Task Management Project Structure

**Date**: 2025-07-31  
**Purpose**: Modern Python package with clean architecture and comprehensive testing

---

## 📁 **Current Directory Structure**

```
task-management/
├── 📦 src/                          # Source code (Python package)
│   └── voice_task_manager/          # Main package
│       ├── __init__.py
│       ├── 🎯 core/                 # Core business logic
│       │   ├── __init__.py
│       │   ├── processor.py        # Main voice processing orchestrator
│       │   ├── database.py         # SQLite database operations
│       │   └── notifications.py    # Notification system
│       ├── 🔌 adapters/             # Storage adapters (Notion, GraphRAG)
│       │   ├── __init__.py
│       │   ├── base.py             # Abstract base adapter
│       │   ├── notion.py           # Notion task adapter
│       │   └── graphrag.py         # GraphRAG/Neo4j adapter
│       ├── 🌐 integrations/         # External service integrations
│       │   ├── __init__.py
│       │   ├── drive.py            # Google Drive client
│       │   ├── whisper.py          # OpenAI Whisper client
│       │   └── notion.py           # Notion API client
│       ├── 📊 models/               # Data models
│       │   ├── __init__.py
│       │   ├── task.py             # Task data model
│       │   ├── voice_file.py       # Voice file model
│       │   └── notion_*.py         # Notion entity models (7 types)
│       ├── 🔄 processors/           # Processing logic
│       │   ├── __init__.py
│       │   ├── claude.py           # Claude AI processor
│       │   └── context.py          # Context extraction
│       └── 🛠️ utils/                # Utility functions
│           ├── __init__.py
│           └── logging.py          # Logging configuration
│
├── 🧪 tests/                        # Test suites
│   ├── __init__.py
│   ├── unit/                        # Unit tests
│   │   ├── test_adapters.py
│   │   ├── test_database.py
│   │   ├── test_models.py
│   │   ├── test_processors.py
│   │   └── test_performance.py
│   ├── integration/                 # Integration tests
│   │   ├── test_api_integration_flow.py
│   │   ├── test_google_drive_integration.py
│   │   ├── test_notion_integration.py
│   │   ├── test_openai_integration.py
│   │   └── test_*_crud_methods.py
│   └── e2e/                         # End-to-end tests
│       ├── test_system_scenarios.py
│       └── test_user_workflows.py
│
├── 📜 scripts/                      # Utility scripts (organized)
│   ├── 📖 README.md                 # Scripts documentation
│   ├── debug/                       # Debugging utilities
│   │   ├── check_*.py              # Various check scripts
│   │   ├── test_*.py               # Test utilities
│   │   └── verify_*.py             # Verification scripts
│   ├── analysis/                    # Log and performance analysis
│   │   ├── analyze_*.py            # Analysis tools
│   │   └── performance_*.py        # Performance tools
│   ├── maintenance/                 # System maintenance
│   │   ├── check_project_structure.py
│   │   ├── fix_*.py                # Fix utilities
│   │   └── clean_*.py              # Cleanup tools
│   └── legacy/                      # Legacy utilities (to be removed)
│       └── migrate_to_uv.sh
│
├── 📚 docs/                         # Documentation
│   ├── 📖 README.md                 # Documentation hub
│   ├── architecture/                # System design
│   │   ├── mcp-server-design.md
│   │   └── project-design.md
│   ├── guides/                      # User guides
│   │   ├── setup/                   # Setup guides
│   │   ├── integrations/            # Integration guides
│   │   └── workflows/               # Workflow guides
│   ├── operations/                  # Operational docs
│   │   ├── PROJECT_STRUCTURE.md    # This file
│   │   └── LOGGING_SYSTEM.md
│   ├── reference/                   # API references
│   │   ├── api_reference.md
│   │   └── mcp-server-reference.md
│   └── specifications/              # Feature specs
│       └── FEATURE_SPECIFICATION.md
│
├── 📊 data/                         # Persistent data
│   ├── processed_files.db          # SQLite database
│   └── README.md
│
├── 📝 logs/                         # System logs
│   ├── voice-automation.log
│   └── README.md
│
├── 🔧 Configuration                 # Config files
│   ├── pyproject.toml              # Python package configuration
│   ├── uv.lock                     # UV lock file
│   ├── .env.example                # Environment template
│   ├── .gitignore
│   ├── notion_mcp_server.py        # MCP server implementation
│   └── .mcp.json                   # MCP configuration
│
└── 📋 Project Files
    ├── README.md                   # Project overview
    ├── CLAUDE.md                   # Project-specific Claude instructions
    ├── CLAUDE_LOG.md              # Development history
    └── UV_MIGRATION_SUMMARY.md    # UV migration details
```

---

## 🎯 **Key Design Principles**

### **Modern Python Package Structure**
- Follows Python best practices with `src/` layout
- Clean separation of concerns with dedicated modules
- Comprehensive test coverage (unit, integration, e2e)
- Uses UV package manager for fast, reliable dependency management

### **Multi-Adapter Architecture**
- Base adapter pattern for extensibility
- Notion adapter for task management
- GraphRAG adapter for knowledge graph integration
- Easy to add new storage backends

### **External Service Integration**
- Clean integration layer for external APIs
- Google Drive for voice file storage
- OpenAI Whisper for transcription
- Notion API for task creation
- Claude AI for intelligent categorization

### **Comprehensive Testing**
- Unit tests for all core components
- Integration tests for API interactions
- End-to-end tests for complete workflows
- Performance tests for optimization

---

## 🔄 **Voice Processing Pipeline**

```
Voice Recording (Mobile Device)
        ↓
Google Drive Sync
        ↓
Voice Processor Discovery
        ↓
Download & Validation
        ↓
Whisper Transcription
        ↓
Claude AI Categorization
        ↓
Multi-Adapter Storage
    ├── Notion (Tasks, Projects, Areas, etc.)
    └── GraphRAG (Knowledge Graph)
        ↓
SQLite Tracking & Deduplication
```

---

## 📦 **Package Installation**

### **Using UV (Recommended)**
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate

# Install package with all dependencies
uv pip install -e ".[dev,mcp,all]"
```

### **Note on pip**
This project uses UV exclusively for package management. Do not use pip or venv - all dependencies are managed through UV and pyproject.toml.

---

## 🧪 **Running Tests**

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=voice_task_manager

# Run specific test file
pytest tests/unit/test_adapters.py -v
```

---

## 🚀 **Quick Navigation**

1. **New to the project?** → Start with [README.md](../../README.md)
2. **Understanding the code?** → Check module docstrings in `src/`
3. **Running tests?** → See test files in `tests/`
4. **Need API docs?** → Read [API Reference](../reference/api_reference.md)
5. **System monitoring?** → Check logs in `logs/`

---

## 🔧 **Development Guidelines**

### **Code Organization**
- Keep related functionality in appropriate modules
- Use clear, descriptive names
- Follow PEP 8 style guidelines
- Add comprehensive docstrings

### **Testing Requirements**
- Write tests for new features
- Maintain test coverage above 80%
- Use mocks for external services
- Include both positive and negative test cases

### **Documentation Standards**
- Update docs when changing functionality
- Keep README files current
- Document breaking changes
- Include code examples

---

## 🔮 **Architecture Highlights**

### **Modular Design**
- Clear separation between core logic and integrations
- Pluggable adapter system for storage backends
- Isolated external service clients
- Reusable utility functions

### **Error Handling**
- Comprehensive exception handling
- Graceful degradation for service failures
- Detailed logging for debugging
- User-friendly error messages

### **Performance Optimization**
- Efficient database queries
- Batch processing capabilities
- Caching where appropriate
- Async operations for I/O

---

*This structure reflects the current state of the Voice Task Management system as a modern Python package with professional architecture and comprehensive testing.*