# Voice Processing Service Architecture

## Overview

The Voice Processing Service is a long-running daemon that replaces the cron-based approach for processing voice recordings. It provides better OAuth session management, error handling, and monitoring compared to periodic cron execution.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    Voice Processing Service               │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────┐      ┌─────────────────────┐   │
│  │ VoiceProcessingDaemon│      │ ClaudeSessionManager│   │
│  │  (Main Thread)      │ ────▶│  (OAuth Monitor)    │   │
│  └────────┬───────────┘      └─────────────────────┘   │
│           │                                              │
│           ▼                                              │
│  ┌────────────────────┐                                │
│  │  Processing Loop    │                                │
│  │  (5 min intervals) │                                │
│  └────────┬───────────┘                                │
│           │                                              │
│           ▼                                              │
│  ┌────────────────────┐                                │
│  │ VoiceProcessorV2    │                                │
│  │ ├─ Drive Discovery │                                │
│  │ ├─ Whisper Trans.  │                                │
│  │ ├─ Claude AI       │                                │
│  │ └─ Multi-Adapter   │                                │
│  └────────────────────┘                                │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Components

### 1. VoiceProcessingDaemon (`services/voice_daemon.py`)

The main service class that runs as a daemon thread:

- **Lifecycle Management**: Start, stop, pause, resume operations
- **Processing Loop**: Runs every 5 minutes (configurable)
- **Health Monitoring**: Tracks statistics and writes health status
- **Signal Handling**: Graceful shutdown on SIGTERM/SIGINT
- **PID Management**: Writes PID file for process control

### 2. ClaudeSessionManager (`services/session_manager.py`)

Manages Claude OAuth authentication:

- **Token Monitoring**: Checks `~/.claude/.credentials.json`
- **Expiry Detection**: Estimates token lifetime (~30 days)
- **Test Execution**: Validates Claude can actually run
- **Notifications**: Alerts when re-authentication needed
- **Fallback Control**: Disables AI when auth fails

### 3. Service Wrapper (`scripts/services/voice-processing-service.py`)

Entry point for service management:

- **Commands**: start, stop, restart, status, health
- **Process Management**: PID file handling
- **Signal Forwarding**: Passes signals to daemon
- **Foreground Mode**: For systemd compatibility

### 4. Systemd Integration (`scripts/services/voice-processing.service`)

Systemd service file for auto-start:

- **Auto-start**: Starts on boot
- **Restart Policy**: Automatic restart on failure
- **Resource Limits**: Memory and CPU quotas
- **Environment**: Proper PATH and HOME setup
- **Logging**: Integrated with journald

## Data Flow

### 1. Service Startup
```
systemd start → service wrapper → daemon thread → initial OAuth check
```

### 2. Processing Cycle
```
Timer (5 min) → Check OAuth → Process files → Update stats → Write health
```

### 3. OAuth Expiry
```
OAuth check fails → Send notification → Disable Claude → Use simple parsing
```

### 4. Service Shutdown
```
SIGTERM → Stop daemon → Cleanup → Remove PID → Final notification
```

## Key Features

### OAuth Session Management

Unlike cron which starts fresh each time, the service:
- Maintains OAuth state between runs
- Monitors token validity
- Sends desktop notifications before expiry
- Gracefully degrades when auth fails

### Health Monitoring

The service provides detailed health information:
- Service state (running, paused, stopped)
- Processing statistics
- Error tracking
- Claude authentication status

### Resource Management

- Single long-running process (vs spawning every 5 min)
- Configurable memory/CPU limits
- Proper cleanup on shutdown
- PID file for process control

## Configuration

### Environment Variables
- `HOME`: Required for Claude credentials
- `PATH`: Must include node for Claude CLI
- `DISPLAY`/`DBUS`: For desktop notifications

### Service Parameters
- `--interval`: Processing interval (default: 300s)
- `--foreground`: Run in foreground for systemd

## Monitoring

### Health Endpoint
```bash
vtm service status
```

Shows:
- Service state
- Uptime
- Processing statistics  
- Claude OAuth status
- Last error (if any)

### Logs
- **Application**: `logs/voice-automation.log`
- **Systemd**: `journalctl -u voice-processing`
- **Errors**: `logs/voice-errors.log`

### Health File
`data/voice-daemon-health.json` - Updated each cycle

## Advantages Over Cron

1. **Persistent OAuth**: No need to re-authenticate each run
2. **Better Monitoring**: Real-time health and statistics
3. **Error Recovery**: Can retry and handle transient failures
4. **Resource Efficient**: Single process vs repeated spawning
5. **Notifications**: Proactive alerts for OAuth expiry

## Troubleshooting

### Service Won't Start
- Check Claude auth: `claude login`
- Verify virtual environment
- Check systemd logs: `journalctl -u voice-processing -n 50`

### OAuth Expires Frequently
- Normal behavior (~30 day lifetime)
- Watch for notifications
- Run `claude login` when prompted

### High Resource Usage
- Adjust interval: `--interval 600` (10 minutes)
- Check systemd limits in service file
- Monitor with: `systemctl status voice-processing`

## Future Enhancements

1. **API Key Support**: Add fallback to Anthropic API keys
2. **Web Dashboard**: HTTP endpoint for monitoring
3. **Metrics Export**: Prometheus/Grafana integration
4. **Dynamic Intervals**: Adjust based on activity
5. **Multi-instance**: Process multiple folders in parallel