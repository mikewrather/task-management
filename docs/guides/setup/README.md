# Setup and Implementation Guides

This directory contains step-by-step guides for setting up and implementing the voice task management system.

## Documents

### 1. [Implementation Guide](implementation-guide.md)
Comprehensive guide for implementing the complete system:
- Prerequisites and requirements
- Step-by-step setup instructions
- Configuration details
- Testing procedures

### 2. [Pixel Watch Setup](pixel-watch-setup.md)
Guide for configuring Google Pixel Watch for voice recording:
- Voice Recorder Pro installation
- Google Drive sync configuration
- Recording quality settings
- Battery optimization

### 3. [Voice Recorder Configuration](voice-recorder-config.md)
Detailed configuration for Voice Recorder Pro:
- App settings and preferences
- Audio format selection
- Automatic upload setup
- Troubleshooting common issues

## Quick Setup Checklist

1. **Environment Setup**
   - [ ] Install Docker and Docker Compose
   - [ ] Configure API keys in `.env`
   - [ ] Set up Google Drive sync folder

2. **Voice Recording**
   - [ ] Install Voice Recorder Pro on device
   - [ ] Configure Google Drive integration
   - [ ] Test recording and sync

3. **System Deployment**
   - [ ] Run `./setup.sh`
   - [ ] Start Windmill with `./windmill-setup.sh`
   - [ ] Deploy workflows
   - [ ] Test complete pipeline

## Prerequisites

- Docker & Docker Compose
- Node.js 18+ (see `.nvmrc`)
- Google Drive desktop sync
- API Keys:
  - OpenAI (for Whisper)
  - Anthropic (for Claude)
  - Notion integration (via MCP)

## Getting Help

- Check [Windmill setup guide](../windmill/setup-guide.md) for orchestration details
- See [architecture docs](../architecture/) for system design
- Review [Notion docs](../notion/) for task management

---

*For ongoing operations, refer to the main [README](../../README.md).*