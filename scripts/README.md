# Scripts Directory

This directory contains automation scripts and utilities for the voice task management system.

## 🔧 **Core Scripts**

### **Voice Processing**
- **`automated-voice-processor.py`** - Main automation script for cron execution
  - Scans Google Drive, transcribes audio, creates Notion tasks
  - Comprehensive logging and error handling
  - Usage: `python automated-voice-processor.py`

- **`voice-cron-wrapper.sh`** - Cron-compatible wrapper script
  - Sets up environment and executes automation
  - Auto-generated during cron installation
  - Usage: `./voice-cron-wrapper.sh`

### **Setup & Configuration**
- **`setup-voice-cron.sh`** - Interactive cron job installer
  - Creates wrapper script and installs cron job
  - Configures 5-minute automation intervals
  - Usage: `./setup-voice-cron.sh`

### **Monitoring & Analysis**
- **`analyze-voice-runs.py`** - Log analysis and statistics
  - View recent runs, comprehensive stats, error summaries
  - Usage: `./analyze-voice-runs.py [--stats|--today|--errors]`

- **`voice-status.sh`** - Quick system status dashboard
  - Shows cron status, recent activity, system health
  - Usage: `./voice-status.sh`

### **File Management**
- **`cleanup-processed-files.py`** - Processed files cleanup manager
  - Track and manage processed voice files
  - Manual cleanup guidance and statistics
  - Usage: `./cleanup-processed-files.py [--list|--guide|--stats]`

### **Notifications**
- **`notification-system.py`** - Desktop notification handler
  - Sends popup notifications when files are processed
  - Optional email notifications (SMTP configuration required)
  - Auto-invoked by main automation script

## 📊 **Logging System**

### **Core Logging Module**
- **`voice_logging.py`** - Centralized logging class
  - Structured logging with context data
  - Multiple log levels (debug, info, warning, error, success)
  - JSON-formatted run summaries for analysis
  - Automatic log rotation and maintenance

### **Log Files Generated**
- **`logs/voice-automation.log`** - Detailed processing logs
- **`logs/cron-run-history.log`** - JSON run summaries
- **`logs/voice-errors.log`** - Dedicated error tracking

## 🚀 **Quick Start**

### **Initial Setup**
```bash
# Install cron automation
./scripts/setup-voice-cron.sh

# Check system status
./scripts/voice-status.sh

# View recent activity
./scripts/analyze-voice-runs.py
```

### **Manual Testing**
```bash
# Test voice processing manually
source venv/bin/activate
python scripts/automated-voice-processor.py

# View comprehensive statistics
./scripts/analyze-voice-runs.py --stats

# Monitor logs in real-time
tail -f logs/voice-automation.log
```

### **Monitoring Commands**
```bash
# System health overview
./scripts/analyze-voice-runs.py --stats

# Today's activity
./scripts/analyze-voice-runs.py --today

# Error analysis
./scripts/analyze-voice-runs.py --errors

# Cron job status
crontab -l

# File cleanup management
./scripts/cleanup-processed-files.py --stats
```

## 📁 **Directory Structure**

```
scripts/
├── automated-voice-processor.py    # Main automation script
├── voice_logging.py                # Centralized logging system
├── analyze-voice-runs.py           # Log analysis tool
├── setup-voice-cron.sh            # Cron installation
├── voice-cron-wrapper.sh          # Auto-generated cron wrapper
├── voice-status.sh                 # Status dashboard
├── notification-system.py         # Desktop notifications
├── archive/                        # Historical/completed scripts
├── setup/                          # One-time setup utilities
├── testing/                        # Development test scripts
├── utilities/                      # General maintenance tools
└── README.md                       # This documentation
```

## 🔧 **Configuration**

All scripts read configuration from the project `.env` file:

```bash
# Required for voice processing
OPENAI_API_KEY=sk-proj-...
NOTION_TOKEN=ntn_...
NOTION_TASKS_DB=183267fb-...
GOOGLE_DRIVE_FOLDER_ID=1vUNQV617t5mXHtyYrGro6Q3K-6JCmuUj

# File cleanup configuration
CLEANUP_PROCESSED_FILES=false  # Enable cleanup tracking
CLEANUP_DELAY_HOURS=24         # Hours before cleanup eligible

# Optional for notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
NOTIFICATION_EMAIL=your-email@gmail.com
```

## 🚨 **Troubleshooting**

### **Common Issues**

**Cron not running**:
```bash
# Check cron service
sudo systemctl status cron

# Verify cron job exists
crontab -l
```

**Environment variables not loaded**:
```bash
# Verify .env file exists and has correct format
cat .env

# Test manual execution
source venv/bin/activate
python scripts/automated-voice-processor.py
```

**No files detected**:
```bash
# Check Google Drive folder accessibility
# Ensure files are publicly shared
# Verify GOOGLE_DRIVE_FOLDER_ID in .env
```

### **Log Analysis**
```bash
# Recent errors
./scripts/analyze-voice-runs.py --errors

# System health check
./scripts/analyze-voice-runs.py --stats | grep "System Health"

# Detailed error investigation
tail logs/voice-errors.log | jq .
```

## 📚 **Development**

### **Adding New Scripts**
1. Follow existing patterns in `automated-voice-processor.py`
2. Use the centralized `VoiceLogger` class
3. Include comprehensive error handling
4. Add documentation to this README

### **Logging Best Practices**
```python
from voice_logging import VoiceLogger

logger = VoiceLogger()
logger.start_run()

# Provide rich context
logger.info("Processing file", file_id=file_id, size_bytes=1024)

# Always log run summaries
logger.log_run_summary(files_found=5, files_processed=3)
```

### **Testing Scripts**
```bash
# Test individual components
python -m pytest scripts/test_*.py

# Validate logging format
python scripts/analyze-voice-runs.py --last 1

# Check script permissions
ls -la scripts/*.sh
```

## 🗄️ **Legacy & Maintenance Scripts**

The following scripts are available for system maintenance but are not part of the core voice processing workflow:

- **Repository Management**: `organize-repo.sh`, `consolidate-docs.sh`
- **Windmill Management**: `backup-restore-windmill.sh`, `start-windmill-with-restore.sh`
- **Development Tools**: Various utilities in `archive/`, `testing/`, and `utilities/` subdirectories

---

**Last Updated**: 2025-07-24  
**Documentation**: See `/docs/LOGGING_SYSTEM.md` for comprehensive logging details