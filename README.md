# Voice Task Manager

A modern Python package that automatically converts voice recordings into organized tasks using pure GraphRAG/Neo4j knowledge graphs. Features intelligent AI categorization, comprehensive testing, and a clean architecture following Python best practices.

## 🚀 Quick Start

```bash
# Install UV (recommended - faster and more reliable than pip)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <repository-url>
cd task-management

# Create virtual environment and install
uv venv
source .venv/bin/activate
uv pip install -e ".[dev,mcp,all]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run tests to verify setup
pytest tests/unit/

# Process voice files
python -m voice_task_manager.core.processor
```

## 🎤 Voice to Task Pipeline

```mermaid
flowchart TB
    VoiceRecording["🎤 Voice Recording<br/>(Mobile Device)"]
    GoogleDrive["☁️ Google Drive Sync"]
    Discovery["🔍 File Discovery"]
    Whisper["🎯 Whisper Transcription"]
    Claude["🤖 Claude AI Categorization"]
    Storage["💾 GraphRAG Storage"]
    GraphRAG["🧠 GraphRAG<br/>(Knowledge Graph)"]
    SQLite["🗄️ SQLite Tracking"]
    
    VoiceRecording --> GoogleDrive
    GoogleDrive --> Discovery
    Discovery --> Whisper
    Whisper --> Claude
    Claude --> Storage
    Storage --> GraphRAG
    Storage --> SQLite
```

## ✨ Key Features

### 🏗️ Modern Architecture
- **Clean Package Structure** - `src/` layout following Python best practices
- **GraphRAG Architecture** - Pure Neo4j knowledge graph storage
- **Comprehensive Testing** - Unit, integration, and E2E test suites
- **UV Package Manager** - Fast, reliable dependency management

### 🤖 Intelligent Processing
- **Claude AI Integration** - Smart categorization into projects, areas, and contexts
- **Whisper Transcription** - High-accuracy voice-to-text conversion
- **Duplicate Prevention** - SQLite tracking ensures no duplicate processing
- **Error Recovery** - Robust error handling and retry logic

### 🕸️ GraphRAG Knowledge Graph
- **4 Core Entities** - Tasks, Projects, Areas, Goals with rich relationships
- **PARA Method** - Automatic organization following productivity best practices
- **Neo4j Storage** - Direct graph database operations with semantic relationships
- **MCP Server** - Agent-db server for comprehensive graph operations
- **Semantic Search** - Find related tasks and concepts using natural language
- **Context Preservation** - Maintains relationships between entities automatically
- **Future-Ready** - Prepared for advanced AI features

## 📁 Project Structure

```
task-management/
├── src/voice_task_manager/     # Main package (following src layout)
│   ├── adapters/              # GraphRAG storage adapter
│   ├── core/                  # Core business logic
│   ├── integrations/          # External services (Drive, Whisper)
│   ├── models/                # Data models for all entities
│   ├── processors/            # AI processing (Claude)
│   └── utils/                 # Utility functions
├── tests/                     # Comprehensive test suites
│   ├── unit/                  # Unit tests for components
│   ├── integration/           # API integration tests
│   └── e2e/                   # End-to-end workflow tests
├── scripts/                   # Utility scripts (organized)
│   ├── debug/                 # Debugging tools
│   ├── analysis/              # Performance analysis
│   └── maintenance/           # System maintenance
└── docs/                      # Complete documentation
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.10+
- UV package manager (recommended) or pip
- API Keys: OpenAI, Anthropic (Claude), Google Drive credentials
- Neo4j database for GraphRAG knowledge graph

### Detailed Setup

1. **Install UV (Recommended)**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and Install**
   ```bash
   git clone <repository-url>
   cd task-management
   
   # Create virtual environment
   uv venv
   source .venv/bin/activate
   
   # Install with all features
   uv pip install -e ".[dev,mcp,all]"
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials:
   ```env
   # Core APIs
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   
   # Google Drive
   GOOGLE_DRIVE_FOLDER_ID=...
   
   # GraphRAG (Required)
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=...
   ```

4. **Verify Installation**
   ```bash
   # Run tests
   pytest tests/unit/ -v
   
   # Check imports
   python -c "from voice_task_manager.core.processor import VoiceProcessor; print('✅ Setup complete!')"
   ```

## 🔄 Voice Processing Service

The recommended way to run voice processing is using the long-running service daemon, which maintains Claude OAuth sessions and provides better monitoring than cron.

### Service Features
- **OAuth Session Persistence** - Maintains Claude authentication between runs
- **Automatic Fallback** - Uses simple parsing when OAuth expires
- **Health Monitoring** - Real-time status and statistics
- **Desktop Notifications** - Alerts for important events
- **Systemd Integration** - Auto-start on boot

### Quick Start
```bash
# Start the service
vtm service start

# Check status
vtm service status

# Stop when needed
vtm service stop

# View logs
tail -f logs/voice-automation.log
```

### Systemd Installation
```bash
# Install as system service
sudo cp scripts/services/voice-processing.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable voice-processing
sudo systemctl start voice-processing

# Check service status
sudo systemctl status voice-processing

# View logs
sudo journalctl -u voice-processing -f
```

### Alternative: Cron Job
If you prefer cron over the service:
```bash
crontab -e
# Add: */5 * * * * /path/to/project/scripts/vtm-cron-wrapper.sh
```

## 🎛️ MCP Inspector Dashboard

Interactive visual testing tool for the GraphRAG agent-db MCP server:

```bash
# Start MCP Inspector for agent-db server
# Configure with .mcp.json to test GraphRAG operations
npx @modelcontextprotocol/inspector

# Or use the convenience script
./scripts/demo-mcp-inspector.sh
```

**Available Tools:**
- `create-task`, `delete-task` - Task management
- `create-project`, `create-area`, `create-goal` - PARA entities
- `create-note`, `create-event`, `create-reference` - Content entities
- `server-info` - Server diagnostics

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/unit/              # Fast unit tests
pytest tests/integration/       # API integration tests
pytest tests/e2e/              # Full workflow tests

# Run with coverage
pytest --cov=voice_task_manager --cov-report=html

# Run specific test
pytest tests/unit/test_adapters.py::TestTaskData -v
```

## 📊 Performance

- **Database Operations**: ~0.2ms per query
- **Transcription**: ~5-10s per minute of audio
- **Task Creation**: <1s including categorization
- **Memory Usage**: <100MB for typical workload
- **Test Coverage**: 135+ passing tests

## 💡 Usage Examples

### Simple Voice Commands
```
"Create a task to review the quarterly reports"
"Add a note about the team meeting decisions"
"New project for the mobile app redesign"
"Schedule dentist appointment for next Tuesday"
```

### Complex Commands (Claude processes)
```
"Set up a comprehensive testing strategy for the new API endpoints"
"Create a project plan for migrating to microservices"
"Research and document best practices for GraphQL implementation"
```

## 🤝 Contributing

1. **Follow Python Best Practices**
   - Use `src/` layout
   - Write comprehensive tests
   - Update documentation
   - Run `ruff` and `black` before committing

2. **Testing Requirements**
   - Add unit tests for new features
   - Update integration tests for API changes
   - Maintain >80% test coverage

3. **Documentation**
   - Update relevant `.md` files
   - Add docstrings to new functions
   - Update API reference if needed

## 📚 Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete guide for end users ⭐
- **[Project Structure](docs/operations/PROJECT_STRUCTURE.md)** - Detailed code organization
- **[API Reference](docs/reference/api_reference.md)** - Complete API documentation
- **[Functionality Overview](docs/COMPREHENSIVE_FUNCTIONALITY_OVERVIEW.md)** - All features listed
- **[Architecture](docs/architecture/)** - System design documentation
- **[MCP Server Guide](docs/mcp-server-guide.md)** - MCP server details

## 🔮 Roadmap

### Recently Completed ✅
- [x] Fix GraphRAG adapter list/dict issue
- [x] Multi-task extraction from single voice notes
- [x] Enhanced notification system integration
- [x] Comprehensive documentation updates

### In Progress 🚧
- [ ] Complete voice file processing into GraphRAG
- [ ] Add async processing support

### Future Features 🔮
- [ ] Implement real-time webhook processing
- [ ] Add web dashboard for monitoring
- [ ] Support for more voice input sources
- [ ] Enhanced AI categorization with fine-tuning
- [ ] Batch processing optimizations

## 📄 License

[Your License Here]

---

*A modern, well-architected Python package for voice-driven task management with AI-powered categorization and multi-backend storage.*