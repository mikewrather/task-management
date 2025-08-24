# Architecture Documentation

This directory contains technical architecture and design documentation for the voice task management system.

## Documents

### 1. [System Design](system-design.md)
Complete technical architecture with detailed implementation:
- High-level system architecture diagrams
- Component interaction flows
- Docker container architecture
- Implementation examples and code samples
- Deployment considerations

### 2. [Project Design](project-design.md)
Overall project design and planning:
- Feature specifications
- User flow diagrams
- Integration points
- Design decisions and rationale

## Architecture Overview

```
Voice Input → Google Drive → File Watcher → Windmill → AI Processing → Notion
```

### Key Components

1. **Input Layer**: Voice recording via mobile/desktop
2. **Storage Layer**: Google Drive synchronization
3. **Processing Layer**: Windmill orchestration with Docker
4. **AI Layer**: Whisper transcription + Claude analysis
5. **Data Layer**: Notion PARA system via MCP

## Technology Stack

- **Orchestration**: Windmill (TypeScript workflows)
- **Containerization**: Docker & Docker Compose
- **AI Services**: OpenAI Whisper, Anthropic Claude
- **Database**: Notion (via MCP)
- **File Monitoring**: Python watchdog

## Design Principles

1. **Modularity**: Each component is independently scalable
2. **Fault Tolerance**: Graceful handling of service failures
3. **Security**: API keys in environment variables, read-only mounts
4. **Extensibility**: Easy to add new voice commands or integrations

---

*For implementation guides, see the [setup documentation](../setup/).*