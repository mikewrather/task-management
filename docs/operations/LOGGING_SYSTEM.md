# Voice Processing Logging System Documentation

**Version**: 2.0  
**Date**: 2025-07-24  
**Status**: Production Ready

---

## 📋 **Overview**

The Voice Processing Logging System provides centralized, structured logging for the voice task management automation. It features multiple log levels, JSON-formatted run summaries, error tracking, and automated log maintenance.

### **Key Benefits**
- **Centralized Management**: Single logging class handles all output
- **Structured Data**: JSON logs for easy analysis and monitoring
- **Error Tracking**: Dedicated error logs with stack traces
- **Run Verification**: Every cron execution logged with statistics
- **Performance Monitoring**: Duration, success rates, and system health indicators

---

## 🏗️ **Architecture**

### **Core Components**

```
voice_logging.py              # Centralized logging class
├── VoiceLogger               # Main logging interface
├── Log Files                 # Multiple specialized logs
│   ├── voice-automation.log  # Detailed processing logs
│   ├── cron-run-history.log  # JSON run summaries
│   └── voice-errors.log      # Dedicated error tracking
└── Analysis Tools            # Log analysis utilities
    └── analyze-voice-runs.py # Statistics and monitoring
```

### **Integration Points**

```python
# Main automation script
from voice_logging import VoiceLogger

logger = VoiceLogger()
logger.start_run()
logger.info("Processing started", file_id="abc123")
logger.log_run_summary(files_found=5, files_processed=3)
```

---

## 📄 **Log File Structure**

### **1. Main Processing Log: `voice-automation.log`**

**Purpose**: Detailed step-by-step processing logs  
**Format**: Timestamped messages with context  
**Rotation**: Automatic when > 10MB

```
[2025-07-24T08:15:30.123456] INFO: 🚀 Starting automated voice processing run
[2025-07-24T08:15:30.234567] INFO: 🔍 Scanning Google Drive folder [folder_id=1vUNQV617t5mXHtyYrGro6Q3K-6JCmuUj]
[2025-07-24T08:15:31.345678] INFO: 📁 Found 2 potential audio files [count=2]
[2025-07-24T08:15:31.456789] INFO: 🎤 Processing voice file [file_id=abc123]
[2025-07-24T08:15:35.567890] ✅ SUCCESS: Transcription completed successfully [file_id=abc123, duration_seconds=15.2, preview=I need to call the dentist...]
[2025-07-24T08:15:38.678901] ✅ SUCCESS: Notion task created successfully [file_id=abc123, task_url=https://notion.so/...]
[2025-07-24T08:15:40.789012] INFO: ✅ RUN SUMMARY: Found=2, Processed=1, Errors=0, Warnings=0, Duration=10.7s, Success Rate=50.0%
```

### **2. Run History Log: `cron-run-history.log`**

**Purpose**: JSON-formatted run summaries for analysis  
**Format**: One JSON object per line  
**Retention**: Permanent (for trend analysis)

```json
{"timestamp": "2025-07-24T08:15:40.789012", "run_duration_seconds": 10.65, "status": "success", "files_found": 2, "files_processed": 1, "processing_success_rate": 50.0, "errors": 0, "warnings": 0, "system_health": "healthy", "database_url": "https://www.notion.so/183267fb-e1c1-4b3b-a42a-5ac1ab8353eb", "notification_system_available": true}
{"timestamp": "2025-07-24T08:20:41.123456", "run_duration_seconds": 0.85, "status": "success", "files_found": 0, "files_processed": 0, "processing_success_rate": 0.0, "errors": 0, "warnings": 0, "system_health": "healthy"}
```

### **3. Error Log: `voice-errors.log`**

**Purpose**: Detailed error tracking with stack traces  
**Format**: JSON objects with exception details  
**Usage**: Critical error analysis and debugging

```json
{"timestamp": "2025-07-24T08:15:32.123456", "message": "OpenAI Whisper transcription failed", "context": {"file_id": "abc123", "response_text": "Rate limit exceeded"}, "exception_type": "HTTPError", "exception_message": "429 Client Error", "traceback": "Traceback (most recent call last):\n  File..."}
```

---

## 🔧 **VoiceLogger Class Reference**

### **Initialization**

```python
from voice_logging import VoiceLogger

# Auto-detect project root
logger = VoiceLogger()

# Specify project root explicitly
logger = VoiceLogger(project_root=Path("/path/to/project"))
```

### **Run Management**

```python
# Start a processing run (resets statistics)
logger.start_run()

# Update run statistics during processing
logger.update_run_stats(files_found=5, files_processed=3)

# Log comprehensive run summary
summary = logger.log_run_summary(
    files_found=5, 
    files_processed=3, 
    errors=1, 
    warnings=0,
    additional_data={'custom_metric': 42}
)
```

### **Logging Methods**

```python
# Debug (only shows when DEBUG=1 environment variable)
logger.debug("Debug information", variable=value)

# Informational messages
logger.info("Processing started", file_id="abc123")

# Warnings (increments warning counter)
logger.warning("File validation failed", file_id="abc123", reason="too_small")

# Errors (increments error counter, logs to error file)
logger.error("API request failed", exception=e, file_id="abc123")

# Success messages
logger.success("Task created", file_id="abc123", task_url="https://...")
```

### **Context Data**

All logging methods accept keyword arguments for structured context:

```python
logger.info("Processing file", 
           file_id="abc123",
           size_bytes=1024000,
           content_type="audio/m4a")

# Results in log:
# [2025-07-24T08:15:30.123456] INFO: Processing file [file_id=abc123, size_bytes=1024000, content_type=audio/m4a]
```

---

## 📊 **Log Analysis Tools**

### **Basic Analysis: `analyze-voice-runs.py`**

```bash
# View recent runs
./scripts/analyze-voice-runs.py

# Show comprehensive statistics
./scripts/analyze-voice-runs.py --stats

# View today's activity only
./scripts/analyze-voice-runs.py --today

# Show error summary
./scripts/analyze-voice-runs.py --errors

# Custom number of recent runs
./scripts/analyze-voice-runs.py --last 25
```

### **Advanced Analysis Examples**

```bash
# Count successful runs today
grep "$(date +%Y-%m-%d)" logs/cron-run-history.log | grep '"status":"success"' | wc -l

# Average processing time
grep "run_duration_seconds" logs/cron-run-history.log | jq -r '.run_duration_seconds' | awk '{sum+=$1; count++} END {print sum/count}'

# Files processed in last 24 hours
grep "$(date -d '1 day ago' +%Y-%m-%d)" logs/cron-run-history.log | jq -r '.files_processed' | awk '{sum+=$1} END {print sum}'
```

---

## 🔧 **Maintenance & Operations**

### **Log Rotation**

Automatic log rotation is built-in:

```python
# Manual rotation (called automatically)
logger.rotate_logs(max_size_mb=10.0, keep_backups=5)

# Check log file information
info = logger.get_log_files_info()
print(f"Main log size: {info['main_log']['size_mb']} MB")
```

### **Log File Locations**

```bash
logs/
├── voice-automation.log      # Current detailed logs
├── voice-automation_20250724_081530.log  # Rotated backup
├── cron-run-history.log      # JSON run summaries (never rotated)
├── voice-errors.log          # Error details
└── voice-errors_20250724_081530.log      # Rotated error backup
```

### **Monitoring Commands**

```bash
# Real-time log monitoring
tail -f logs/voice-automation.log

# Monitor run summaries
tail -f logs/cron-run-history.log | jq .

# Check system health
./scripts/analyze-voice-runs.py --stats | grep "System Health"

# View recent errors
tail -10 logs/voice-errors.log | jq .
```

---

## 🚨 **Error Handling & Troubleshooting**

### **Common Error Patterns**

**Missing Environment Variables**:
```json
{"message": "Missing required environment variables", "context": {"missing_vars": ["OPENAI_API_KEY"]}}
```
**Fix**: Check `.env` file configuration

**Google Drive Access Failed**:
```json
{"message": "Failed to access Google Drive folder", "context": {"status_code": 403, "folder_id": "1vUNQV617t5mXHtyYrGro6Q3K-6JCmuUj"}}
```
**Fix**: Verify folder is publicly accessible

**Whisper API Rate Limit**:
```json
{"message": "OpenAI Whisper transcription failed", "context": {"response_text": "Rate limit exceeded"}}
```
**Fix**: Implement backoff retry or reduce processing frequency

### **Health Status Indicators**

- **`healthy`**: Success rate > 90%, errors = 0, warnings ≤ 1
- **`warning`**: Success rate 70-90% or errors ≤ 2  
- **`critical`**: Success rate < 70% or errors > 2

### **Log Analysis for Debugging**

```bash
# Find all errors in last hour
python3 -c "
import json
from datetime import datetime, timedelta
cutoff = datetime.now() - timedelta(hours=1)
with open('logs/voice-errors.log') as f:
    for line in f:
        error = json.loads(line)
        if datetime.fromisoformat(error['timestamp']) > cutoff:
            print(f\"{error['timestamp']}: {error['message']}\")
"

# Processing success trends
python3 -c "
import json
with open('logs/cron-run-history.log') as f:
    rates = [json.loads(line)['processing_success_rate'] for line in f]
    print(f'Average success rate: {sum(rates)/len(rates):.1f}%')
"
```

---

## 📚 **Integration Examples**

### **Custom Script Integration**

```python
#!/usr/bin/env python3
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from voice_logging import VoiceLogger

def my_custom_processor():
    logger = VoiceLogger()
    logger.start_run()
    
    try:
        logger.info("Starting custom processing")
        
        # Your processing logic here
        files_processed = process_files()
        
        logger.success("Custom processing completed", count=files_processed)
        
        # Log final summary
        logger.log_run_summary(
            files_found=10,
            files_processed=files_processed,
            additional_data={'processor': 'custom_v1.0'}
        )
        
    except Exception as e:
        logger.error("Custom processing failed", exception=e)
        logger.log_run_summary(files_found=10, files_processed=0, errors=1)

if __name__ == "__main__":
    my_custom_processor()
```

### **Cron Integration**

The logging system is designed for cron automation:

```bash
# Current cron job (every 5 minutes)
*/5 * * * * /home/mike/development/task-management/scripts/voice-cron-wrapper.sh

# The wrapper script ensures proper environment and logging
#!/bin/bash
cd /home/mike/development/task-management
source venv/bin/activate
python scripts/automated-voice-processor.py >> logs/cron-voice.log 2>&1
```

---

## 🔍 **Performance Considerations**

### **Log File Sizes**

- **Main Log**: ~1KB per run, rotates at 10MB (~10,000 runs)
- **Run History**: ~200 bytes per run, never rotated (permanent history)
- **Error Log**: Variable size, rotates at 10MB

### **I/O Impact**

- Synchronous file writes (minimal performance impact)
- JSON parsing only during analysis (not during logging)
- Log rotation handled automatically in background

### **Memory Usage**

- Logger instance: ~1KB memory footprint
- No in-memory log buffering (immediate file writes)
- Context data serialized efficiently

---

## 🎯 **Best Practices**

### **Logging Strategy**

1. **Use appropriate log levels**:
   - `debug()`: Development/troubleshooting only
   - `info()`: Normal operations and status updates
   - `warning()`: Issues that don't prevent processing
   - `error()`: Failures that prevent processing
   - `success()`: Completed operations

2. **Provide rich context**:
   ```python
   # Good: Rich context
   logger.error("Transcription failed", file_id=file_id, status_code=response.status_code, duration=duration)
   
   # Avoid: Minimal context
   logger.error("Transcription failed")
   ```

3. **Use run summaries consistently**:
   ```python
   # Always log run summary at end
   logger.log_run_summary(files_found=count, files_processed=processed)
   ```

### **Monitoring Strategy**

1. **Daily**: Check `analyze-voice-runs.py --stats` for health
2. **Weekly**: Review error trends and success rates
3. **Monthly**: Analyze processing patterns and performance

### **Error Response**

1. **Immediate**: Check recent errors with `analyze-voice-runs.py --errors`
2. **Investigation**: Review detailed error log: `tail logs/voice-errors.log | jq .`
3. **Resolution**: Fix root cause and monitor recovery

---

**Last Updated**: 2025-07-24  
**Next Review**: After system performance analysis

*This documentation covers the complete logging system implementation for the voice task management project.*