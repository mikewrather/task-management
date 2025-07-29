# Voice Task Manager

A professional Python package that automatically converts voice recordings into organized Notion tasks. Seamlessly integrates Google Drive, OpenAI Whisper, and Notion with robust performance monitoring and comprehensive testing.

## 🚀 Quick Start

```bash
# Install with uv (recommended - faster and more reliable)
uv pip install voice-task-manager

# Or install with pip (legacy)
pip install voice-task-manager

# Set up configuration
cp .env.example .env
# Edit .env with your API keys

# Process voice files
vtm process

# View statistics
vtm stats
```

## 📚 Documentation

### Core Documentation
- **[📖 User Guide](docs/user_guide.md)** - Complete setup and usage guide
- **[🔧 API Reference](docs/api_reference.md)** - Detailed API documentation
- **[⚡ Performance Analysis](docs/performance_analysis.md)** - Performance metrics and optimization

### Migration Documentation  
- **[🔄 Python Package Migration](docs/PYTHON_PACKAGE_MIGRATION.md)** - Migration from script-based to package architecture
- **[🧹 Legacy Cleanup](CLEANUP_SUMMARY.md)** - Historical cleanup and organization

## 🎤 Voice to Task Pipeline

1. **Record** voice note on mobile device
2. **Sync** to Google Drive automatically  
3. **Discover** new files via Google Drive API
4. **Transcribe** with OpenAI Whisper API
5. **Create** organized Notion task with context tags
6. **Track** processing state in SQLite database

## ✨ Key Features

- 🚀 **High Performance** - 0.2ms database operations, efficient memory usage
- 🧪 **Fully Tested** - 33+ tests covering models, database, and performance
- 📊 **Performance Monitoring** - Built-in metrics collection and analysis
- 🔄 **Robust Processing** - Automatic retry logic and error handling
- 🗄️ **SQLite Database** - Efficient tracking and duplicate prevention
- 🎯 **Modern Architecture** - Clean Python package with proper separation of concerns
- 📋 **CLI Interface** - Simple command-line tools for all operations

## 📖 Additional Documentation

### Legacy Documentation
- 📂 **[Project Structure](PROJECT_STRUCTURE.md)** - Repository organization
- 📚 **[Documentation Index](docs/README.md)** - Historical documentation
- 🏗️ **[System Architecture](docs/architecture/README.md)** - Technical architecture
- 🎤 **[Voice Commands Reference](VOICE_COMMANDS_REFERENCE.md)** - Example commands
- 🔐 **[Google Drive Setup](docs/guides/google-drive-setup.md)** - Drive integration

## 💡 Examples

### Simple Voice Commands (API-only)
- "Mark the login bug as complete"
- "Create a task to review pull requests" 
- "Add a note about the performance issue"
- "Schedule meeting with John for tomorrow at 2pm"

### Complex Voice Commands (Claude executes)
- "Set up a Python project for the voice recognition system"
- "Debug why the cron job failed last night"
- "Create integration tests for the new API endpoints"
- "Refactor the authentication module to use JWT tokens"

## 🏗️ Architecture

```
Voice Recording (Apple Watch)
        ↓
Google Drive Sync
        ↓
Cron Automation (Every 5 minutes)
        ↓
Python Processing Pipeline
    ├── File Detection (HTML Parsing + Validation)
    ├── Download Audio File
    ├── Transcribe (OpenAI Whisper)
    ├── Create Notion Task
    └── Cleanup Tracking
```

## 🔧 Key Innovation

Pure Python automation that runs reliably via cron with comprehensive error handling, duplicate prevention, and file cleanup management. No complex orchestration needed - just works.

## 🎛️ MCP Inspector Dashboard

Interactive visual testing tool for the enhanced MCP server with 9 tools:

```bash
# Start MCP Inspector dashboard
mcp dev notion_mcp_server.py
# Opens at: http://localhost:6274

# Or use our demo script
./scripts/demo-mcp-inspector.sh
```

**Features:** Test all 9 MCP tools (Tasks, Projects, Areas, Goals, Notes, Events, References, Delete Task, Server Info) with real-time parameter testing and response visualization.

## 📁 Project Structure

```
task-management/
├── docs/                          # 📚 Comprehensive documentation
│   ├── README.md                 # Documentation hub
│   ├── guides/                   # Setup and usage guides
│   ├── architecture/             # System design docs
│   └── setup/                    # Implementation guides
├── scripts/                      # 🛠️ Automation and utility scripts  
│   ├── README.md                # Scripts documentation
│   ├── automated-voice-processor.py  # Main automation
│   ├── cleanup-processed-files.py    # File management
│   ├── voice-status.sh               # System monitoring
│   └── analyze-voice-runs.py         # Statistics and analysis
├── data/                        # 📊 SQLite database and logs
│   └── processed_files.db       # Processing history
├── logs/                        # 📝 System logs
│   ├── voice-automation.log     # Detailed processing logs
│   └── cron-run-history.log     # Run summaries
└── .env.example                 # Configuration template
```

## 🚀 Getting Started

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd task-management
   ```

2. **Configure your environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # - OPENAI_API_KEY (for Whisper transcription)
   # - NOTION_TOKEN (for task creation)
   # - NOTION_TASKS_DB (your tasks database ID)
   # - GOOGLE_DRIVE_FOLDER_ID (your voice files folder)
   ```

3. **Set up Python environment**
   
   **Using uv (recommended):**
   ```bash
   # Install uv (if not already installed)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Run automated migration
   ./scripts/migrate-to-uv.sh
   
   # OR manual setup:
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev,mcp]"
   ```
   
   **Using pip (legacy):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install -r mcp-requirements.txt
   ```

4. **Test the system**
   ```bash
   ./scripts/voice-cron-wrapper.sh
   ```

For detailed instructions, see the **[Feature Specification](docs/FEATURE_SPECIFICATION.md)**.

## 🔑 Required Components

- **Voice Input**: Apple Watch with Voice Recorder Pro
- **Storage**: Google Drive for audio files (public folder access)
- **Transcription**: OpenAI Whisper API
- **Task Management**: Notion databases with PARA method
- **Automation**: Python 3.11+ with cron scheduling
- **Database**: SQLite for processing history and duplicate prevention

## 💰 Cost Estimate

- Whisper API: ~$5/month (500 recordings)
- Notion: Free (personal) or $8/month (Pro)
- Google Drive: Free (15GB) or $6/month (100GB)
- **Total**: ~$5-19/month for fully automated voice-to-task system

## 🌟 Benefits

- **Natural Language**: No rigid command syntax
- **Fully Automated**: Set it and forget it - runs every 5 minutes
- **Reliable Processing**: Duplicate prevention and comprehensive error handling
- **Fast Transcription**: High-accuracy OpenAI Whisper integration
- **Organized Tasks**: PARA methodology with intelligent categorization
- **File Management**: Built-in cleanup tools and storage management

## 🤝 Contributing

When contributing to this project:
1. Keep documentation up-to-date
2. Place scripts in appropriate directories
3. Follow established patterns
4. Update relevant README files

## 📄 License

[Your License Here]

---

*Last Updated: 2025-07-24*