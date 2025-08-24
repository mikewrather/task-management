# Voice Note Processing Flow

## Current Architecture Overview

This documents the **current working system** for processing voice notes from recording to Notion task creation.

## System Flow

```mermaid
flowchart TD
    subgraph Recording["Voice Recording"]
        Watch["Pixel Watch<br/>Voice Recorder Pro"]
        AudioFile["Audio File<br/>(.m4a format)"]
    end
    
    subgraph Storage["File Storage"]
        DriveFolder["Google Drive<br/>Shared Folder"]
        PublicLink["Temporary Public Link<br/>(seconds only)"]
    end
    
    subgraph Processing["Claude Code Processing"]
        VoiceManager["voice_task_manager<br/>Python Package"]
        Whisper["OpenAI Whisper<br/>Transcription"]
        ClaudeAI["Claude AI<br/>Task Extraction"]
        MCPServer["Notion MCP Server<br/>Database Operations"]
    end
    
    subgraph Storage2["Task Storage"]
        NotionTasks["Notion Tasks<br/>Database"]
        NotionNotes["Notion Notes<br/>Database"]
    end
    
    Watch -->|Records| AudioFile
    AudioFile -->|Auto-sync| DriveFolder
    DriveFolder -->|Manual share| PublicLink
    
    PublicLink -->|Download| VoiceManager
    VoiceManager -->|Audio data| Whisper
    Whisper -->|Transcript| ClaudeAI
    ClaudeAI -->|Structured commands| MCPServer
    MCPServer -->|Create tasks| NotionTasks
    MCPServer -->|Create notes| NotionNotes
```

## Detailed Processing Pipeline

```mermaid
flowchart TD
    Start["Start: Audio File ID"]
    
    subgraph FileHandling["File Handling"]
        Download["Download from Drive<br/>using public link"]
        Validate["Validate audio format<br/>(.m4a, .mp3, .wav)"]
        TempStore["Store in /tmp"]
    end
    
    subgraph Transcription["Audio Transcription"]
        WhisperAPI["OpenAI Whisper API<br/>model: whisper-1"]
        TextOutput["Raw transcript text"]
    end
    
    subgraph AIProcessing["AI Analysis"]
        ClaudePrompt["Claude with system prompt<br/>PARA methodology rules"]
        TaskExtraction["Extract actionable items"]
        StructuredOutput["JSON commands array"]
    end
    
    subgraph NotionOperations["Notion Operations"]
        CreateTasks["Create tasks in<br/>Tasks database"]
        CreateNotes["Create notes in<br/>Notes database"]
        LinkRelations["Link review tasks<br/>to contextual notes"]
    end
    
    subgraph Cleanup["Cleanup"]
        DeleteTemp["Delete temp files"]
        DeleteDrive["Delete from Drive<br/>(optional)"]
    end
    
    Start --> Download
    Download --> Validate
    Validate --> TempStore
    TempStore --> WhisperAPI
    WhisperAPI --> TextOutput
    TextOutput --> ClaudePrompt
    ClaudePrompt --> TaskExtraction
    TaskExtraction --> StructuredOutput
    StructuredOutput --> CreateTasks
    StructuredOutput --> CreateNotes
    CreateTasks --> LinkRelations
    CreateNotes --> LinkRelations
    LinkRelations --> DeleteTemp
    DeleteTemp --> DeleteDrive
```

## Command Structure

The system processes voice commands into structured JSON:

```json
{
  "commands": [
    {
      "type": "task.create",
      "data": {
        "name": "Review quarterly metrics",
        "status": "Inbox",
        "priority": "Medium",
        "contexts": ["@computer", "@work"],
        "project": "Q4 Planning"
      }
    },
    {
      "type": "note.create", 
      "data": {
        "title": "Meeting notes - Q4 planning",
        "content": "Discussed budget allocation...",
        "tags": ["meeting", "planning"]
      }
    }
  ]
}
```

## Current Implementation

### Technology Stack
- **Python Package**: `voice_task_manager` with CLI interface
- **Transcription**: OpenAI Whisper API
- **AI Processing**: Claude 3.5 Sonnet via Anthropic API
- **Database**: Notion via MCP server integration
- **File Storage**: Google Drive with temporary public sharing

### Key Components

1. **Voice Task Manager** (`src/voice_task_manager/`)
   - Command-line interface for processing
   - Integration with all APIs
   - Error handling and logging

2. **Notion MCP Server** (`notion_mcp_server.py`)
   - Handles all Notion database operations
   - CRUD operations for tasks, notes, projects
   - Relationship management

3. **Processing Scripts** (`scripts/`)
   - Manual processing utilities
   - Cleanup and maintenance tools

### Usage

```bash
# Process a single voice file
python -m voice_task_manager.cli process-voice-file \
  --file-id "GOOGLE_DRIVE_FILE_ID" \
  --delete-after

# Check system status
python -m voice_task_manager.cli check-system-health
```

## Limitations & Considerations

### Current Limitations
- **Manual trigger**: Requires manual execution per voice file
- **Public sharing**: Files must be temporarily made public
- **No automation**: No automated folder monitoring

### Security Notes
- Audio files are public for seconds only during processing
- Files deleted immediately after processing
- API keys stored in environment variables

### Future Enhancements
- Automated folder monitoring
- Private Google Drive API integration
- Real-time processing pipeline
- Web interface for management

---

*This documentation reflects the current working system as of July 2025. The system has evolved from Windmill-based workflows to a direct Python implementation with MCP server integration.*