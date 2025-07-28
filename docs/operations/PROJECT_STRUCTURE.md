# Voice Task Management Project Structure

**Date**: 2025-07-24  
**Purpose**: Clean Python-based automation system structure

---

## 📁 **Current Directory Structure**

```
task-management/
├── 📚 docs/                     # All documentation
│   ├── 📖 README.md            # Documentation hub and index
│   ├── 📋 FEATURE_SPECIFICATION.md  # Complete system spec
│   ├── 🏗️ architecture/        # System design and diagrams
│   │   ├── README.md
│   │   └── system-design.md
│   ├── 📐 setup/                # Installation and configuration
│   │   └── README.md
│   ├── 📚 guides/               # User guides and workflows
│   │   ├── complete-voice-flow.md
│   │   ├── voice-workflow-guide.md
│   │   ├── google-drive-setup.md
│   │   ├── claude-agent-voice-workflow.md
│   │   └── file-cleanup-guide.md
│   ├── 📝 notion/               # Notion integration docs
│   │   └── para-methodology.md
│   └── 📊 PROJECT_ORGANIZATION.md
├── 🛠️ scripts/                  # All automation and utility scripts
│   ├── 📖 README.md            # Scripts documentation
│   ├── 🎤 automated-voice-processor.py  # Main automation
│   ├── 📊 analyze-voice-runs.py # Log analysis and stats
│   ├── 🔍 voice-status.sh      # System health check
│   ├── 🧹 cleanup-processed-files.py  # File management
│   ├── 📬 notification-system.py # Desktop notifications
│   ├── 🔄 voice-cron-wrapper.sh # Cron execution wrapper
│   └── 📋 voice_logging.py      # Centralized logging system
├── 📊 data/                    # System data and databases
│   └── processed_files.db     # SQLite tracking database
├── 📝 logs/                    # System logs
│   ├── voice-automation.log   # Detailed processing logs
│   └── cron-run-history.log   # Run summaries
├── 📄 Configuration Files
│   ├── .env.example           # Environment template
│   ├── 📋 README.md            # Project overview and quick start
│   ├── 📚 CLAUDE_LOG.md        # Development session history
│   └── 🎤 VOICE_COMMANDS_REFERENCE.md # Example voice commands
└── 🗂️ Root Organization
    └── PROJECT_STRUCTURE.md    # This file
```

---

## 🎯 **Key Design Principles**

### **Documentation First**
- All documentation centralized in `/docs/` with clear hierarchy
- README files at every level for navigation
- Feature specification as single source of truth
- Development history preserved in CLAUDE_LOG.md

### **Script Organization**
- All automation in `/scripts/` directory
- Clear naming conventions (purpose-context-type.extension)
- Comprehensive script documentation in scripts/README.md
- Executable scripts have proper permissions and shebangs

### **Python Automation**
- Pure Python implementation with minimal dependencies
- Cron-based scheduling for reliable automation
- SQLite database for persistent state and tracking
- Comprehensive logging with structured data

---

## 🔄 **Workflow Architecture**

### **Voice Processing Pipeline**
```
Apple Watch Recording
        ↓
Google Drive Sync
        ↓
Cron Automation (5 min)
        ↓
Python File Detection
        ↓
Whisper Transcription
        ↓
Notion Task Creation
        ↓
SQLite Tracking
```

### **System Components**
- **Input**: Apple Watch Voice Recorder Pro
- **Storage**: Google Drive public folder
- **Automation**: Python scripts with cron scheduling
- **Transcription**: OpenAI Whisper API
- **Database**: SQLite for processing history
- **Output**: Notion PARA databases
- **Monitoring**: Comprehensive logging and notifications

---

## 📋 **File Management Strategy**

### **Configuration Management**
- Environment variables in `.env` (not tracked)
- Configuration templates provided (.env.example)
- API keys and secrets properly isolated
- Python virtual environment for dependencies

### **Data Persistence**
- SQLite database for processing history and duplicate prevention
- Structured logging with rotation
- File cleanup tracking and management tools
- Development history in CLAUDE_LOG.md

---

## 🚀 **Quick Navigation**

1. **New to the project?** → Start with [README.md](../README.md)
2. **Setting up?** → Check [Feature Specification](FEATURE_SPECIFICATION.md)
3. **Understanding scripts?** → See [scripts/README.md](../scripts/README.md)
4. **File cleanup?** → Read [File Cleanup Guide](guides/file-cleanup-guide.md)
5. **System monitoring?** → Use `./scripts/voice-status.sh`

---

## 🔮 **Next Steps**

### **Planned Improvements**
1. **Phase 1**: Google Drive API integration for automated file cleanup
2. **Phase 2**: Enhanced context analysis for intelligent categorization
3. **Phase 3**: Real-time processing with webhook triggers
4. **Phase 4**: Web dashboard for monitoring and control

---

*This structure reflects the current Python-based automation system, optimized for simplicity and reliability.*