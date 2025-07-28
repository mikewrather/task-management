# Voice Task Management System Design

## Overview

This document outlines the architecture for a voice-driven task management system that integrates Google Drive file monitoring, Windmill workflow orchestration, Claude AI processing, and Notion database management.

## System Architecture

### High-Level Architecture

```mermaid
flowchart TB
    subgraph InputLayer["Input Layer"]
        VoiceRecorder["Voice Recorder<br/>(Mobile/Desktop)"]
        VoiceFile["Voice Files<br/>(.m4a, .mp3, .wav)"]
    end
    
    subgraph StorageLayer["Storage Layer"]
        GoogleDrive["Google Drive<br/>(Monitored Folder)"]
        LocalSync["Local Sync Folder"]
    end
    
    subgraph ProcessingLayer["Processing Layer"]
        FileWatcher["File System Watcher<br/>(inotify/FSEvents)"]
        WindmillQueue["Windmill Job Queue"]
        WindmillWorker["Windmill Worker<br/>(Docker Container)"]
    end
    
    subgraph AILayer["AI Processing"]
        Whisper["Whisper API<br/>(Transcription)"]
        Claude["Claude API<br/>(Task Extraction)"]
        MCPServer["MCP Server<br/>(Notion Integration)"]
    end
    
    subgraph DataLayer["Data Layer"]
        NotionDB["Notion Databases<br/>(PARA System)"]
    end
    
    VoiceRecorder -->|Records| VoiceFile
    VoiceFile -->|Uploads| GoogleDrive
    GoogleDrive -->|Syncs| LocalSync
    LocalSync -->|Triggers| FileWatcher
    FileWatcher -->|Creates Job| WindmillQueue
    WindmillQueue -->|Processes| WindmillWorker
    WindmillWorker -->|Calls| Whisper
    Whisper -->|Transcript| WindmillWorker
    WindmillWorker -->|Sends| Claude
    Claude -->|Commands| MCPServer
    MCPServer -->|Updates| NotionDB
```

### Detailed Component Flow

```mermaid
flowchart LR
    subgraph VoiceCapture["Voice Capture"]
        MobileApp["Mobile App"]
        DesktopApp["Desktop App"]
        WebRecorder["Web Recorder"]
    end
    
    subgraph FileProcessing["File Processing Pipeline"]
        direction TB
        FileDetection["File Detection<br/>Event"]
        FileValidation["File Validation<br/>(Format, Size)"]
        QueueJob["Queue Windmill Job"]
        ProcessJob["Process Job"]
    end
    
    subgraph WindmillWorkflow["Windmill Workflow"]
        direction TB
        ReceiveFile["Receive File Path"]
        TranscribeAudio["Transcribe Audio<br/>(Whisper)"]
        ProcessText["Process Text<br/>(Claude + MCP)"]
        HandleResponse["Handle Response"]
        UpdateStatus["Update Status"]
    end
    
    MobileApp --> FileDetection
    DesktopApp --> FileDetection
    WebRecorder --> FileDetection
    
    FileDetection --> FileValidation
    FileValidation --> QueueJob
    QueueJob --> ProcessJob
    
    ProcessJob --> ReceiveFile
    ReceiveFile --> TranscribeAudio
    TranscribeAudio --> ProcessText
    ProcessText --> HandleResponse
    HandleResponse --> UpdateStatus
```

## Component Details

### 1. File System Event Handling

```mermaid
flowchart TB
    subgraph FileWatcherDesign["File System Watcher Design"]
        GoogleDriveSync["Google Drive<br/>Sync Folder"]
        WatchService["Watch Service<br/>(Python/Node.js)"]
        EventFilter["Event Filter"]
        JobCreator["Job Creator"]
    end
    
    subgraph EventTypes["Event Types"]
        FileCreated["File Created"]
        FileModified["File Modified"]
        FileRenamed["File Renamed"]
    end
    
    subgraph FilterRules["Filter Rules"]
        AudioOnly["Audio Files Only<br/>(.m4a, .mp3, .wav)"]
        MinSize["Minimum Size<br/>(> 1KB)"]
        MaxSize["Maximum Size<br/>(< 50MB)"]
        NotTemp["Not Temporary<br/>(no .tmp, ~)"]
    end
    
    GoogleDriveSync --> WatchService
    WatchService --> EventFilter
    
    FileCreated --> EventFilter
    FileModified --> EventFilter
    FileRenamed --> EventFilter
    
    EventFilter --> AudioOnly
    EventFilter --> MinSize
    EventFilter --> MaxSize
    EventFilter --> NotTemp
    
    AudioOnly --> JobCreator
    MinSize --> JobCreator
    MaxSize --> JobCreator
    NotTemp --> JobCreator
```

### 2. Windmill Docker Architecture

```mermaid
flowchart TB
    subgraph DockerCompose["Docker Compose Stack"]
        WindmillServer["Windmill Server<br/>Container"]
        WindmillWorker1["Worker 1<br/>(Python)"]
        WindmillWorker2["Worker 2<br/>(Python)"]
        WindmillDB["PostgreSQL<br/>Database"]
        RedisCache["Redis Cache<br/>(Optional)"]
    end
    
    subgraph SharedVolumes["Shared Volumes"]
        ScriptsVolume["Scripts Volume<br/>/app/scripts"]
        DataVolume["Data Volume<br/>/app/data"]
        TempVolume["Temp Volume<br/>/tmp/audio"]
    end
    
    subgraph HostSystem["Host System"]
        GoogleDriveFolder["Google Drive<br/>Sync Folder"]
        FileWatcherService["File Watcher<br/>Service"]
    end
    
    WindmillServer ---|Port 8000| WindmillDB
    WindmillWorker1 ---|Jobs| WindmillServer
    WindmillWorker2 ---|Jobs| WindmillServer
    WindmillServer ---|Cache| RedisCache
    
    GoogleDriveFolder ---|Mount| DataVolume
    FileWatcherService ---|API Calls| WindmillServer
    
    ScriptsVolume ---|Mount| WindmillWorker1
    ScriptsVolume ---|Mount| WindmillWorker2
    DataVolume ---|Mount| WindmillWorker1
    DataVolume ---|Mount| WindmillWorker2
```

### 3. Windmill Workflow Design

```mermaid
flowchart TD
    subgraph WindmillFlow["Windmill Workflow: process_voice_task"]
        Start["Start<br/>Input: file_path"]
        
        ValidateFile["Validate File<br/>- Check exists<br/>- Check format<br/>- Check size"]
        
        TranscribeAudio["Transcribe Audio<br/>- Call Whisper API<br/>- Handle errors<br/>- Return text"]
        
        ProcessWithClaude["Process with Claude<br/>- Send transcript<br/>- Include context<br/>- Parse response"]
        
        ExtractCommands["Extract Commands<br/>- Parse JSON<br/>- Validate structure<br/>- Queue actions"]
        
        ExecuteActions["Execute Actions<br/>- Create tasks<br/>- Create notes<br/>- Update projects"]
        
        LogResults["Log Results<br/>- Success/failure<br/>- Metrics<br/>- Cleanup"]
        
        End["End"]
    end
    
    Start --> ValidateFile
    ValidateFile -->|Valid| TranscribeAudio
    ValidateFile -->|Invalid| LogResults
    TranscribeAudio -->|Success| ProcessWithClaude
    TranscribeAudio -->|Error| LogResults
    ProcessWithClaude --> ExtractCommands
    ExtractCommands --> ExecuteActions
    ExecuteActions --> LogResults
    LogResults --> End
```

### 4. Claude Integration Pattern

```mermaid
flowchart LR
    subgraph ClaudeProcessing["Claude Processing Pipeline"]
        Transcript["Voice Transcript"]
        SystemPrompt["System Prompt<br/>+ PARA Rules"]
        ClaudeAPI["Claude API"]
        
        subgraph ResponseFormat["Response Format"]
            Commands["Commands Array"]
            TaskCreate["task.create"]
            NoteCreate["note.create"]
            ProjectUpdate["project.update"]
        end
    end
    
    subgraph MCPExecution["MCP Execution"]
        MCPRouter["MCP Router"]
        NotionAPI["Notion API"]
        ResponseHandler["Response Handler"]
    end
    
    Transcript --> ClaudeAPI
    SystemPrompt --> ClaudeAPI
    ClaudeAPI --> Commands
    Commands --> TaskCreate
    Commands --> NoteCreate
    Commands --> ProjectUpdate
    
    TaskCreate --> MCPRouter
    NoteCreate --> MCPRouter
    ProjectUpdate --> MCPRouter
    
    MCPRouter --> NotionAPI
    NotionAPI --> ResponseHandler
```

## Implementation Details

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  windmill-postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: windmill
      POSTGRES_USER: windmill
      POSTGRES_PASSWORD: windmill
    volumes:
      - windmill-db:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U windmill"]
      interval: 10s
      timeout: 5s
      retries: 5

  windmill-server:
    image: ghcr.io/windmill-labs/windmill:latest
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgres://windmill:windmill@windmill-postgres/windmill
      MODE: server
    depends_on:
      windmill-postgres:
        condition: service_healthy
    volumes:
      - ./windmill-scripts:/usr/src/app/scripts
      - ${GOOGLE_DRIVE_SYNC_PATH}:/data/voice-files:ro

  windmill-worker:
    image: ghcr.io/windmill-labs/windmill:latest
    environment:
      DATABASE_URL: postgres://windmill:windmill@windmill-postgres/windmill
      MODE: worker
      WORKER_TAGS: "voice,transcription"
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    depends_on:
      - windmill-server
    volumes:
      - ./windmill-scripts:/usr/src/app/scripts
      - ${GOOGLE_DRIVE_SYNC_PATH}:/data/voice-files:ro
      - /tmp/windmill-audio:/tmp/audio
    deploy:
      replicas: 2

  file-watcher:
    build: ./file-watcher
    environment:
      WATCH_PATH: /data/voice-files
      WINDMILL_URL: http://windmill-server:8000
      WINDMILL_TOKEN: ${WINDMILL_TOKEN}
    volumes:
      - ${GOOGLE_DRIVE_SYNC_PATH}:/data/voice-files:ro
    depends_on:
      - windmill-server

volumes:
  windmill-db:
```

### File Watcher Implementation

```python
# file-watcher/watcher.py
import os
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

class VoiceFileHandler(FileSystemEventHandler):
    def __init__(self, windmill_url, windmill_token):
        self.windmill_url = windmill_url
        self.windmill_token = windmill_token
        self.processed_files = set()
        
    def on_created(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Check if audio file
        if file_path.suffix.lower() not in ['.m4a', '.mp3', '.wav']:
            return
            
        # Check if already processed
        if str(file_path) in self.processed_files:
            return
            
        # Wait for file to be fully written
        time.sleep(2)
        
        # Check file size
        if file_path.stat().st_size < 1024:  # Less than 1KB
            return
            
        # Queue job in Windmill
        self.queue_windmill_job(str(file_path))
        self.processed_files.add(str(file_path))
        
    def queue_windmill_job(self, file_path):
        """Queue a job in Windmill to process the voice file"""
        try:
            response = requests.post(
                f"{self.windmill_url}/api/w/main/jobs/run/f/process_voice_task",
                headers={
                    "Authorization": f"Bearer {self.windmill_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "args": {
                        "file_path": file_path,
                        "timestamp": time.time()
                    }
                }
            )
            response.raise_for_status()
            print(f"Queued job for: {file_path}")
        except Exception as e:
            print(f"Error queueing job: {e}")

def main():
    watch_path = os.environ.get('WATCH_PATH', '/data/voice-files')
    windmill_url = os.environ.get('WINDMILL_URL', 'http://localhost:8000')
    windmill_token = os.environ.get('WINDMILL_TOKEN')
    
    event_handler = VoiceFileHandler(windmill_url, windmill_token)
    observer = Observer()
    observer.schedule(event_handler, watch_path, recursive=True)
    observer.start()
    
    print(f"Watching for voice files in: {watch_path}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
```

### Windmill Workflow Script

```python
# windmill-scripts/process_voice_task.py
import json
import os
from pathlib import Path
import openai
from anthropic import Anthropic
import requests

def main(file_path: str, timestamp: float):
    """Process a voice file through the complete pipeline"""
    
    # Step 1: Validate file
    if not validate_file(file_path):
        return {"status": "error", "message": "Invalid file"}
    
    # Step 2: Transcribe audio
    transcript = transcribe_audio(file_path)
    if not transcript:
        return {"status": "error", "message": "Transcription failed"}
    
    # Step 3: Process with Claude
    commands = process_with_claude(transcript)
    if not commands:
        return {"status": "error", "message": "Command extraction failed"}
    
    # Step 4: Execute commands
    results = execute_commands(commands)
    
    # Step 5: Cleanup and return
    return {
        "status": "success",
        "transcript": transcript,
        "commands": commands,
        "results": results
    }

def validate_file(file_path: str) -> bool:
    """Validate the audio file"""
    path = Path(file_path)
    
    if not path.exists():
        return False
        
    if path.suffix.lower() not in ['.m4a', '.mp3', '.wav']:
        return False
        
    if path.stat().st_size > 50 * 1024 * 1024:  # 50MB limit
        return False
        
    return True

def transcribe_audio(file_path: str) -> str:
    """Transcribe audio using Whisper API"""
    client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    
    with open(file_path, 'rb') as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
    
    return response

def process_with_claude(transcript: str) -> list:
    """Process transcript with Claude to extract commands"""
    client = Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    
    system_prompt = """
    You are a task management assistant. Extract actionable items from the transcript.
    Return a JSON array of commands in this format:
    [
        {
            "type": "task.create",
            "data": {
                "name": "Task description",
                "status": "inbox",
                "priority": "medium",
                "date": "2025-06-24",
                "contexts": ["phone", "office"]
            }
        }
    ]
    
    Supported command types:
    - task.create
    - note.create
    - project.create
    """
    
    response = client.messages.create(
        model="claude-3-opus-20240229",
        system=system_prompt,
        messages=[
            {"role": "user", "content": f"Extract commands from: {transcript}"}
        ],
        max_tokens=1000
    )
    
    try:
        return json.loads(response.content[0].text)
    except:
        return []

def execute_commands(commands: list) -> list:
    """Execute commands via MCP/Notion API"""
    results = []
    
    for command in commands:
        if command['type'] == 'task.create':
            result = create_task(command['data'])
        elif command['type'] == 'note.create':
            result = create_note(command['data'])
        elif command['type'] == 'project.create':
            result = create_project(command['data'])
        else:
            result = {"error": "Unknown command type"}
            
        results.append(result)
    
    return results

def create_task(data: dict) -> dict:
    """Create a task in Notion"""
    # Implementation would use MCP or direct Notion API
    # This is a placeholder
    return {"success": True, "task_id": "123"}
```

## Deployment Considerations

### 1. Security
- API keys stored in environment variables
- File access limited to read-only for voice files
- Windmill authentication tokens for job submission
- Network isolation between containers

### 2. Scalability
- Multiple Windmill workers for parallel processing
- Redis cache for job queuing if needed
- Horizontal scaling of file watchers
- Rate limiting for API calls

### 3. Monitoring
- Windmill dashboard for job status
- Logging aggregation for debugging
- Metrics for processing times
- Alert on failed transcriptions

### 4. Error Handling
- Retry logic for API failures
- Dead letter queue for failed jobs
- File quarantine for problematic audio
- Graceful degradation

## Future Enhancements

### 1. Real-time Processing
```mermaid
flowchart LR
    VoiceStream["Voice Stream"] --> RealtimeTranscript["Real-time<br/>Transcription"]
    RealtimeTranscript --> LivePreview["Live Preview"]
    LivePreview --> Confirmation["User Confirmation"]
    Confirmation --> Execute["Execute Commands"]
```

### 2. Multi-modal Input
- Image attachment support
- Document scanning integration
- Screen capture with annotations

### 3. Advanced AI Features
- Context awareness from previous commands
- Predictive task suggestions
- Natural language project templates

### 4. Integration Extensions
- Calendar integration for scheduling
- Email integration for task creation
- Slack/Discord notifications

---

*This design document provides the technical architecture for the voice task management system. Implementation should follow these patterns while allowing for flexibility in specific technology choices.*