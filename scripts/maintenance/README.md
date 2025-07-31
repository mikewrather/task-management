# Maintenance Scripts

This directory contains scripts for system maintenance, cleanup, and monitoring.

## Core Scripts

### `automated-voice-processor.py`
The main voice processing script that:
- Discovers new voice files in Google Drive
- Transcribes audio using OpenAI Whisper
- Creates tasks in Notion/GraphRAG
- Manages file cleanup

### `cleanup-processed-files.py`
Manages cleanup of processed voice files:
- Moves processed files to archive
- Removes old entries from database
- Maintains system performance

### `check_project_structure.py`
Verifies the project follows Python best practices:
- Checks for clean root directory
- Validates package structure
- Ensures proper test organization

## Duplicate Management

- `delete-duplicate-voice-tasks.py` - Remove duplicate tasks from Notion
- `simple-delete-duplicates.py` - Simple duplicate removal
- `direct-delete-duplicates.py` - Direct API duplicate removal
- `clean-duplicates-cli.sh` - CLI wrapper for duplicate cleaning

## System Utilities

### `notification-system.py`
Sends email notifications for:
- Processing errors
- Daily summaries
- System alerts

### `voice_logging.py`
Logging utilities for the voice processing system

## Usage

```bash
# Process voice files
python scripts/maintenance/automated-voice-processor.py

# Clean up old files
python scripts/maintenance/cleanup-processed-files.py

# Check project structure
python scripts/maintenance/check_project_structure.py
```

## Cron Integration

Most maintenance scripts are designed to be run via cron. See the cron wrapper scripts in the parent directory for examples.