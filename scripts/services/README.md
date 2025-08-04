# Voice Processing Service

This directory contains the voice processing service implementation that replaces the cron-based approach with a long-running daemon.

## Overview

The service maintains Claude OAuth session between runs and provides better error handling, monitoring, and resource management compared to cron.

## Components

- **voice-processing-service.py** - Service manager script with start/stop/status commands
- **voice-processing.service** - Systemd service file for auto-start on boot

## Installation

1. **Test the service manually first:**
   ```bash
   cd /home/mike/development/task-management
   source .venv/bin/activate
   python scripts/services/voice-processing-service.py start
   ```

2. **Check status:**
   ```bash
   python scripts/services/voice-processing-service.py status
   ```

3. **Install as systemd service:**
   ```bash
   # Copy service file
   sudo cp scripts/services/voice-processing.service /etc/systemd/system/
   
   # Reload systemd
   sudo systemctl daemon-reload
   
   # Enable service (auto-start on boot)
   sudo systemctl enable voice-processing
   
   # Start service
   sudo systemctl start voice-processing
   
   # Check status
   sudo systemctl status voice-processing
   ```

## Usage

### Manual Control
```bash
# Start service
python scripts/services/voice-processing-service.py start

# Stop service
python scripts/services/voice-processing-service.py stop

# Restart service
python scripts/services/voice-processing-service.py restart

# Check status
python scripts/services/voice-processing-service.py status

# Get health info
python scripts/services/voice-processing-service.py health
```

### Systemd Control
```bash
# Start
sudo systemctl start voice-processing

# Stop
sudo systemctl stop voice-processing

# Restart
sudo systemctl restart voice-processing

# Status
sudo systemctl status voice-processing

# View logs
sudo journalctl -u voice-processing -f
```

## Features

### OAuth Session Management
- Monitors Claude credentials at `~/.claude/.credentials.json`
- Tests Claude execution periodically
- Sends desktop notifications when re-authentication needed
- Falls back to simple processing when OAuth expires

### Processing
- Runs every 5 minutes (configurable)
- Processes all unprocessed voice files
- Creates tasks in Notion and GraphRAG
- Tracks statistics and errors

### Monitoring
- PID file at `data/voice-daemon.pid`
- Health endpoint with detailed statistics
- Desktop notifications for important events
- Structured logging to systemd journal

## Configuration

Edit the service file or pass arguments:

```bash
# Change interval to 10 minutes (600 seconds)
python scripts/services/voice-processing-service.py start --interval 600

# Run in foreground (for debugging)
python scripts/services/voice-processing-service.py start --foreground
```

## Troubleshooting

### Service won't start
1. Check Claude authentication: `claude login`
2. Check virtual environment: `.venv/bin/python --version`
3. Check logs: `sudo journalctl -u voice-processing -n 50`

### OAuth expires frequently
- This is expected (~30 day expiry)
- Service will notify when re-auth needed
- Run `claude login` to refresh

### Desktop notifications not working
- Ensure DISPLAY and DBUS variables are set
- Check notification daemon is running
- Test with: `notify-send "Test" "Message"`

## Migration from Cron

1. **Keep cron initially** (disable but don't remove)
2. **Run service in parallel** for testing
3. **Monitor for 1 week**
4. **Disable cron**: `crontab -e` and comment out the line
5. **Remove cron** after 1 month of stable operation

## Architecture

The service uses a multi-threaded architecture:

```
VoiceProcessingDaemon (main thread)
├── Processing Loop (5 min intervals)
├── ClaudeSessionManager (OAuth monitoring)
└── VoiceProcessorV2 (actual processing)
    ├── Google Drive discovery
    ├── Whisper transcription
    ├── Claude AI categorization
    └── Multi-adapter storage
```

## Development

To modify the service:

1. Edit source files in `src/voice_task_manager/services/`
2. Test changes with manual start
3. Update systemd service if needed
4. Restart service to apply changes

## Logs

- **Application logs**: `logs/voice-automation.log`
- **Systemd logs**: `journalctl -u voice-processing`
- **Error tracking**: `logs/voice-errors.log`