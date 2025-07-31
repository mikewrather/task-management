# Voice Task Manager - API Reference

## Package Structure

```python
voice_task_manager/
├── adapters/       # Storage adapter implementations
├── core/           # Core business logic
├── integrations/   # External service clients
├── models/         # Data models
├── processors/     # Processing logic
└── utils/          # Utility functions
```

## Core Module

### VoiceProcessor

Main orchestrator for the voice-to-task pipeline.

```python
from voice_task_manager.core.processor import VoiceProcessor

processor = VoiceProcessor()
```

#### Methods

##### `process_voice_files() -> Dict[str, Any]`
Process all pending voice files from Google Drive.

**Returns:**
- Dictionary with processing statistics

**Example:**
```python
results = processor.process_voice_files()
print(f"Processed: {results['processed_count']}")
print(f"Errors: {results['error_count']}")
```

### VoiceDatabase

SQLite database interface for tracking processed files.

```python
from voice_task_manager.core.database import VoiceDatabase

db = VoiceDatabase("data/processed_files.db")
```

#### Methods

##### `is_file_processed(file_id: str) -> bool`
Check if a file has already been processed.

##### `save_voice_file(voice_file: VoiceFile) -> None`
Save voice file processing record.

##### `get_processing_stats() -> Dict[str, Any]`
Get processing statistics.

## Adapters Module

### BaseTaskAdapter

Abstract base class for task storage adapters.

```python
from voice_task_manager.adapters.base import BaseTaskAdapter

class MyAdapter(BaseTaskAdapter):
    def create_task(self, task_data: TaskData) -> str:
        # Implementation
        pass
```

### NotionTaskAdapter

Notion storage adapter implementation.

```python
from voice_task_manager.adapters.notion import NotionTaskAdapter

adapter = NotionTaskAdapter(notion_client)
task_id = adapter.create_task(task_data)
```

### GraphRAGAdapter

Neo4j/GraphRAG storage adapter implementation.

```python
from voice_task_manager.adapters.graphrag import GraphRAGAdapter

adapter = GraphRAGAdapter()
task_id = adapter.create_task(task_data)
```

## Models Module

### TaskData

Core task data model.

```python
from voice_task_manager.models.task import TaskData

task = TaskData(
    name="Review quarterly reports",
    description="Analyze Q4 financial data",
    contexts=["work", "finance"],
    project_name="Financial Review",
    area_name="Finance"
)
```

#### Attributes
- `name` (str): Task title
- `description` (Optional[str]): Task description
- `status` (str): Task status (default: "Inbox")
- `priority` (str): Priority level (default: "Medium")
- `contexts` (List[str]): Context tags
- `project_id` (Optional[str]): Associated project ID
- `project_name` (Optional[str]): Associated project name
- `area_id` (Optional[str]): Associated area ID
- `area_name` (Optional[str]): Associated area name

### VoiceFile

Voice file model for tracking.

```python
from voice_task_manager.models.voice_file import VoiceFile

voice_file = VoiceFile(
    file_id="drive_123",
    file_name="recording.m4a",
    file_size=1024000,
    created_time=datetime.now()
)
```

### Notion Entity Models

Models for all 7 Notion entity types:

```python
from voice_task_manager.models.notion_project import NotionProject
from voice_task_manager.models.notion_area import NotionArea
from voice_task_manager.models.notion_goal import NotionGoal
from voice_task_manager.models.notion_note import NotionNote
from voice_task_manager.models.notion_event import NotionEvent
from voice_task_manager.models.notion_reference import NotionReference
from voice_task_manager.models.task import NotionTask
```

## Integrations Module

### GoogleDriveClient

Google Drive integration for file discovery and download.

```python
from voice_task_manager.integrations.drive import GoogleDriveClient

client = GoogleDriveClient()
files = client.list_audio_files(folder_id="...")
```

#### Methods

##### `list_audio_files(folder_id: str) -> List[Dict[str, Any]]`
List audio files in specified folder.

##### `download_file(file_id: str, destination: Path) -> Path`
Download file to local path.

### WhisperClient

OpenAI Whisper integration for transcription.

```python
from voice_task_manager.integrations.whisper import WhisperClient

client = WhisperClient(api_key="sk-...")
transcript = client.transcribe(audio_path)
```

#### Methods

##### `transcribe(audio_path: Path) -> str`
Transcribe audio file to text.

### NotionClient

Notion API client with full CRUD operations.

```python
from voice_task_manager.integrations.notion import NotionClient

client = NotionClient()
```

#### Task Methods
- `create_task(task_data: Dict) -> Dict`
- `get_task(task_id: str) -> Dict`
- `update_task(task_id: str, updates: Dict) -> Dict`
- `delete_task(task_id: str) -> bool`

#### Project Methods
- `create_project(project: NotionProject) -> NotionProject`
- `update_project(project: NotionProject) -> bool`
- `delete_project(project_id: str) -> bool`
- `query_projects() -> List[NotionProject]`

#### Similar methods for Areas, Goals, Notes, Events, and References

## Processors Module

### ClaudeVoiceProcessor

Claude AI integration for intelligent task categorization.

```python
from voice_task_manager.processors.claude import ClaudeVoiceProcessor

processor = ClaudeVoiceProcessor()
task_data = processor.process_transcript(
    transcript="Create a task to review the reports",
    adapters=[notion_adapter, graphrag_adapter]
)
```

#### Methods

##### `process_transcript(transcript: str, adapters: List[BaseTaskAdapter]) -> TaskData`
Process transcript and create categorized task using all adapters.

## Utils Module

### Logging Configuration

```python
from voice_task_manager.utils.logging import setup_logging

logger = setup_logging(
    log_file="logs/voice-automation.log",
    level="INFO"
)
```

## Environment Variables

Required environment variables:

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Notion
NOTION_TOKEN=secret_...
NOTION_TASKS_DB=...
NOTION_PROJECTS_DB=...
NOTION_AREAS_DB=...
NOTION_GOALS_DB=...
NOTION_NOTES_DB=...
NOTION_EVENTS_DB=...
NOTION_REFERENCES_DB=...

# Google Drive
GOOGLE_DRIVE_FOLDER_ID=...

# Neo4j (Optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...

# Claude
ANTHROPIC_API_KEY=sk-ant-...
```

## Error Handling

All methods follow consistent error handling:

```python
try:
    result = processor.process_voice_files()
except ProcessingError as e:
    logger.error(f"Processing failed: {e}")
except NotionAPIError as e:
    logger.error(f"Notion API error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

## Example Usage

### Complete Processing Pipeline

```python
from voice_task_manager.core.processor import VoiceProcessor
from voice_task_manager.adapters.notion import NotionTaskAdapter
from voice_task_manager.adapters.graphrag import GraphRAGAdapter

# Initialize processor
processor = VoiceProcessor()

# Process all pending files
results = processor.process_voice_files()

# Check results
if results['processed_count'] > 0:
    print(f"Successfully processed {results['processed_count']} files")
if results['error_count'] > 0:
    print(f"Errors: {results['error_count']}")
```

### Manual Task Creation

```python
from voice_task_manager.models.task import TaskData
from voice_task_manager.adapters.notion import NotionTaskAdapter

# Create task data
task = TaskData(
    name="Review API documentation",
    contexts=["development", "documentation"],
    project_name="API Redesign"
)

# Create in Notion
adapter = NotionTaskAdapter(notion_client)
task_id = adapter.create_task(task)
print(f"Created task: {task_id}")
```

### Database Statistics

```python
from voice_task_manager.core.database import VoiceDatabase

db = VoiceDatabase()
stats = db.get_processing_stats()

print(f"Total processed: {stats['total_processed']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Average processing time: {stats['avg_processing_time']:.2f}s")
```