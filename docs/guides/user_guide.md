# Voice Task Manager - User Guide

## Overview

The Voice Task Manager automatically converts voice recordings stored in Google Drive into organized tasks in Notion. This guide covers installation, setup, and daily usage.

## Quick Start

### 1. Installation

```bash
# Install the package
pip install voice-task-manager

# Or install from source
git clone <repository>
cd voice-task-manager
pip install -e .
```

### 2. Basic Setup

1. **Create a `.env` file** in your project directory:
```bash
# Google Drive Configuration
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Notion Configuration
NOTION_API_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_notion_database_id
```

2. **Set up API integrations** (see Setup Guide below)

3. **Test the setup**:
```bash
vtm process --dry-run
```

### 3. Basic Usage

```bash
# Process all new voice files
vtm process

# View processing statistics
vtm stats

# Check recent activity
vtm logs
```

---

## Setup Guide

### Google Drive Setup

1. **Create Google Drive API credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Google Drive API
   - Create service account credentials
   - Download JSON key file

2. **Find your voice recordings folder ID**:
   - Open Google Drive in browser
   - Navigate to your voice recordings folder
   - Copy the folder ID from the URL: `drive.google.com/drive/folders/FOLDER_ID_HERE`

3. **Share folder with service account**:
   - Right-click your voice recordings folder
   - Click "Share"
   - Add your service account email with "Viewer" permissions

### OpenAI Setup

1. **Get OpenAI API key**:
   - Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
   - Create new secret key
   - Copy the key (starts with `sk-`)

2. **Add to `.env` file**:
```bash
OPENAI_API_KEY=sk-your-key-here
```

### Notion Setup

1. **Create Notion integration**:
   - Go to [Notion Integrations](https://www.notion.so/my-integrations)
   - Click "Create new integration"
   - Name it "Voice Task Manager"
   - Copy the "Internal Integration Token"

2. **Create Notion database**:
   - Create a new Notion page
   - Add a database with these properties:
     - **Name** (Title)
     - **Status** (Status: Inbox, In Progress, Done)
     - **Contexts** (Multi-select)
     - **Source** (Text) - optional
     - **Created** (Created time) - optional

3. **Share database with integration**:
   - Click "Share" on your database page
   - Add your integration with "Edit" permissions

4. **Get database ID**:
   - Copy database URL: `notion.so/DATABASE_ID?v=...`
   - Extract the database ID (32-character string)

5. **Add to `.env` file**:
```bash
NOTION_API_TOKEN=secret_your_token_here
NOTION_DATABASE_ID=your_database_id_here
```

---

## Daily Usage

### Processing Voice Files

#### Automatic Processing
```bash
# Process all new voice files
vtm process

# Process with detailed output
vtm process --verbose

# Test without making changes
vtm process --dry-run
```

#### Manual Processing
```python
from voice_task_manager.core.processor import VoiceProcessor

processor = VoiceProcessor()

# Get unprocessed files
files = processor.discover_voice_files()
unprocessed = [f for f in files if not f.is_processed]

# Process specific files
for file in unprocessed[:3]:  # Process first 3
    success = processor.process_single_file(file)
    print(f"Processed {file.file_id}: {'✅' if success else '❌'}")
```

### Monitoring and Stats

#### Command Line
```bash
# View processing statistics
vtm stats

# View recent logs
vtm logs --limit 50

# View files processed today
vtm stats --today

# View failed processing attempts
vtm logs --failed-only
```

#### Programmatic
```python
from voice_task_manager.utils.database import VoiceDatabase

db = VoiceDatabase()

# Get processing statistics
stats = db.get_processing_stats()
print(f"Total files: {stats['total_files']}")
print(f"Processed: {stats['processed_files']}")
print(f"Success rate: {stats['success_rate']:.1%}")

# Get recent files
from datetime import datetime, timedelta
recent = db.get_files_by_date_range(
    datetime.now() - timedelta(days=7),
    datetime.now()
)
print(f"Files this week: {len(recent)}")
```

### Managing Tasks

#### View Created Tasks
```python
from voice_task_manager.utils.database import VoiceDatabase

db = VoiceDatabase()

# Get all tasks
tasks = db.get_all_tasks()
for task in tasks:
    print(f"📋 {task.title} ({task.status})")

# Get tasks from specific voice file
voice_tasks = db.get_tasks_by_voice_file("voice_file_id")
```

#### Update Task Status
Tasks are automatically created in Notion with "Inbox" status. You can:
- Update status in Notion directly
- Use the Notion API to programmatically update tasks
- Set up automation rules in Notion

---

## Advanced Usage

### Custom Processing Workflows

#### Batch Processing
```python
from voice_task_manager.core.processor import VoiceProcessor
from voice_task_manager.utils.database import VoiceDatabase

processor = VoiceProcessor()
db = VoiceDatabase()

# Get files from specific date range
from datetime import datetime, timedelta
start_date = datetime.now() - timedelta(days=7)
end_date = datetime.now()

files = db.get_files_by_date_range(start_date, end_date)
unprocessed = [f for f in files if not f.is_processed]

print(f"Processing {len(unprocessed)} files from last week...")

for file in unprocessed:
    try:
        success = processor.process_single_file(file)
        if success:
            print(f"✅ {file.file_id}")
        else:
            print(f"❌ {file.file_id}")
    except Exception as e:
        print(f"💥 {file.file_id}: {e}")
```

#### Filtering and Categorization
```python
# Process only larger files (likely longer recordings)
large_files = [f for f in files if f.file_size and f.file_size > 1024*1024]  # >1MB

# Process files by content type
audio_files = [f for f in files if f.content_type and 'audio' in f.content_type]

# Skip files that have failed multiple times
reliable_files = [f for f in files if f.retry_count < 3]
```

### Performance Monitoring

#### Enable Performance Tracking
```python
from voice_task_manager.core.processor import VoiceProcessor
from voice_task_manager.utils.performance import PerformanceIntegration

# Create processor with performance monitoring
processor = VoiceProcessor()
PerformanceIntegration.enhance_voice_processor(type(processor))

# Process files (now with monitoring)
results = processor.process_all_files()

# View performance metrics
from voice_task_manager.utils.performance import print_performance_summary
print_performance_summary()
```

#### Custom Performance Metrics
```python
from voice_task_manager.utils.performance import track_performance
import time

@track_performance("custom_operation", track_memory=True)
def my_custom_processing():
    # Your custom processing logic
    time.sleep(1)  # Simulate work
    return "completed"

# Run operations
for i in range(5):
    my_custom_processing()

# Get detailed metrics
from voice_task_manager.utils.performance import get_performance_summary
summary = get_performance_summary()
print(summary)
```

### Database Management

#### Backup and Restore
```python
from voice_task_manager.utils.database import VoiceDatabase
import json

db = VoiceDatabase()

# Export all data
all_files = db.get_all_voice_files()
all_tasks = db.get_all_tasks()

backup_data = {
    'voice_files': [f.to_dict() for f in all_files],
    'tasks': [t.to_dict() for t in all_tasks],
    'backup_date': datetime.now().isoformat()
}

with open('voice_manager_backup.json', 'w') as f:
    json.dump(backup_data, f, indent=2)
```

#### Cleanup Old Records
```bash
# Clean up records older than 90 days
vtm cleanup --days 90

# Clean up only completed records
vtm cleanup --days 30 --completed-only
```

```python
# Programmatic cleanup
db = VoiceDatabase()
deleted_count = db.cleanup_old_records(days_old=90)
print(f"Deleted {deleted_count} old records")
```

---

## Automation

### Scheduled Processing

#### Using Cron (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Add entry to run every hour
0 * * * * cd /path/to/project && vtm process >> /var/log/voice-manager.log 2>&1
```

#### Using Task Scheduler (Windows)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., every hour)
4. Set action: `vtm process`
5. Set start in: your project directory

#### Python Scheduler
```python
import schedule
import time
from voice_task_manager.core.processor import VoiceProcessor

def process_voice_files():
    processor = VoiceProcessor()
    try:
        results = processor.process_all_files()
        print(f"Processed {results['files_processed']} files")
    except Exception as e:
        print(f"Processing failed: {e}")

# Schedule processing every hour
schedule.every().hour.do(process_voice_files)

# Keep running
while True:
    schedule.run_pending()
    time.sleep(60)
```

### Integration with Other Tools

#### Slack Notifications
```python
import requests
from voice_task_manager.core.processor import VoiceProcessor

def send_slack_notification(message):
    webhook_url = "your_slack_webhook_url"
    payload = {"text": message}
    requests.post(webhook_url, json=payload)

# Process files and notify
processor = VoiceProcessor()
results = processor.process_all_files()

if results['files_processed'] > 0:
    message = f"🎤 Processed {results['files_processed']} voice files"
    send_slack_notification(message)
```

#### Email Reports
```python
import smtplib
from email.mime.text import MIMEText
from voice_task_manager.utils.database import VoiceDatabase

def send_daily_report():
    db = VoiceDatabase()
    stats = db.get_processing_stats()
    
    # Get today's files
    today = datetime.now().date()
    today_files = db.get_files_by_date_range(
        datetime.combine(today, datetime.min.time()),
        datetime.combine(today, datetime.max.time())
    )
    
    report = f"""
    Daily Voice Processing Report
    
    Today's Activity:
    - Files processed: {len(today_files)}
    - Success rate: {stats['success_rate']:.1%}
    
    Overall Statistics:
    - Total files: {stats['total_files']}
    - Total processed: {stats['processed_files']}
    """
    
    # Send email (configure your SMTP settings)
    msg = MIMEText(report)
    msg['Subject'] = 'Voice Task Manager Daily Report'
    msg['From'] = 'your_email@example.com'
    msg['To'] = 'recipient@example.com'
    
    # ... email sending code
```

---

## Troubleshooting

### Common Issues

#### 1. "No voice files found"
**Cause**: Google Drive folder ID incorrect or permissions not set
**Solution**:
- Verify `GOOGLE_DRIVE_FOLDER_ID` in `.env`
- Check folder sharing permissions with service account
- Test with: `vtm test-drive-connection`

#### 2. "OpenAI API authentication failed"
**Cause**: Invalid or missing OpenAI API key
**Solution**:
- Verify `OPENAI_API_KEY` in `.env`
- Check API key has sufficient credits
- Test with: `vtm test-openai-connection`

#### 3. "Notion API error"
**Cause**: Invalid token or database permissions
**Solution**:
- Verify `NOTION_API_TOKEN` and `NOTION_DATABASE_ID`
- Check integration permissions on database
- Test with: `vtm test-notion-connection`

#### 4. "Database locked" error
**Cause**: Multiple processes accessing database simultaneously
**Solution**:
```python
# Use database context manager
from voice_task_manager.utils.database import VoiceDatabase

with VoiceDatabase() as db:
    # Database operations here
    files = db.get_all_voice_files()
```

#### 5. "File not found" during processing
**Cause**: File deleted from Drive after discovery
**Solution**:
- Check if file still exists in Drive
- Clean up stale records: `vtm cleanup --verify-files`

### Debug Mode

#### Enable Verbose Logging
```bash
# Command line
vtm process --verbose --debug

# Environment variable
DEBUG=1 vtm process
```

#### Programmatic Debugging
```python
import logging
from voice_task_manager.core.processor import VoiceProcessor

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

processor = VoiceProcessor()
# Now all operations will show detailed logs
```

### Performance Issues

#### Slow Processing
1. **Check API rate limits**:
   - OpenAI: 3 requests/minute for free tier
   - Notion: 3 requests/second
   - Google Drive: 1000 requests/day

2. **Optimize file sizes**:
   - Large audio files take longer to transcribe
   - Consider compressing audio files

3. **Monitor system resources**:
```python
from voice_task_manager.utils.performance import PerformanceMonitor

monitor = PerformanceMonitor()
# ... run operations
monitor.print_summary()
```

#### High Memory Usage
```python
# Process files in batches
def process_in_batches(files, batch_size=10):
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        for file in batch:
            processor.process_single_file(file)
        # Clear memory between batches
        import gc
        gc.collect()
```

---

## Best Practices

### File Organization
- Use consistent naming for voice recordings
- Keep recordings in dedicated Google Drive folder
- Regularly clean up processed files from Drive

### Notion Database Design
- Use consistent status values (Inbox, In Progress, Done)
- Add helpful properties like Priority, Due Date
- Set up database views for different contexts

### Monitoring and Maintenance
- Set up daily/weekly processing schedules
- Monitor success rates and investigate failures
- Regularly backup database and configurations
- Update API keys before expiration

### Security
- Store API keys in `.env` file (never in code)
- Add `.env` to `.gitignore`
- Use environment variables in production
- Regularly rotate API keys
- Review service account permissions

---

## Tips and Tricks

### Improving Transcription Quality
- Record in quiet environments
- Speak clearly and at moderate pace
- Use good quality microphone
- Keep recordings under 10 minutes for faster processing

### Notion Integration Tips
- Use templates for consistent task format
- Set up automation rules in Notion
- Create views filtered by voice context
- Use relation properties to link related tasks

### Workflow Optimization
- Process files during off-peak hours
- Use dry-run mode to test changes
- Monitor processing logs regularly
- Set up alerts for failed processing

### Custom Extensions
```python
# Custom post-processing
def custom_task_processor(task):
    # Add custom logic after task creation
    if "meeting" in task.title.lower():
        task.add_context("meetings")
        task.update_status("In Progress")

# Integrate with processor
processor = VoiceProcessor()
# Add custom hooks to processor workflow
```

---

## Getting Help

### Documentation
- [API Reference](api_reference.md)
- [Performance Analysis](performance_analysis.md)
- [Development Guide](development_guide.md)

### Community
- GitHub Issues: Report bugs and feature requests
- Discussions: Ask questions and share tips

### Support
For technical support:
1. Check troubleshooting section above
2. Enable debug logging and collect logs
3. Search existing GitHub issues
4. Create new issue with detailed information