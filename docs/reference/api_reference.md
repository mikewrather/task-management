# Voice Task Manager - API Reference

## Core Classes

### VoiceProcessor

Main orchestrator for the voice-to-task pipeline.

```python
from voice_task_manager.core.processor import VoiceProcessor

processor = VoiceProcessor(project_root=Path("/path/to/project"))
```

#### Methods

##### `process_all_files(dry_run: bool = False) -> Dict[str, Any]`
Process all discovered voice files.

**Parameters:**
- `dry_run` (bool): If True, simulate processing without making API calls

**Returns:**
- Dictionary with processing results and statistics

**Example:**
```python
results = processor.process_all_files(dry_run=True)
print(f"Processed {results['files_processed']} files")
```

##### `discover_voice_files() -> List[VoiceFile]`
Discover voice files from Google Drive.

**Returns:**
- List of VoiceFile objects representing discovered files

**Example:**
```python
files = processor.discover_voice_files()
for file in files:
    print(f"Found: {file.file_id}")
```

##### `process_single_file(voice_file: VoiceFile) -> bool`
Process a single voice file through the complete pipeline.

**Parameters:**
- `voice_file` (VoiceFile): The voice file to process

**Returns:**
- True if processing succeeded, False otherwise

---

### VoiceFile

Data model representing a voice recording file.

```python
from voice_task_manager.models.voice_file import VoiceFile

voice_file = VoiceFile(
    file_id="abc123",
    file_size=1024000,
    content_type="audio/m4a"
)
```

#### Attributes

- `file_id` (str): Google Drive file ID
- `discovered_at` (datetime): When file was discovered
- `processed_at` (Optional[datetime]): When file was processed
- `status` (str): Processing status ('discovered', 'processing', 'completed', 'failed')
- `file_size` (Optional[int]): File size in bytes
- `content_type` (Optional[str]): MIME type
- `transcript` (Optional[str]): Transcribed text
- `transcript_length` (Optional[int]): Length of transcript
- `duration_seconds` (Optional[float]): Audio duration
- `task_url` (Optional[str]): Created Notion task URL
- `error_message` (Optional[str]): Error details if failed
- `retry_count` (int): Number of processing attempts
- `metadata` (Dict[str, Any]): Additional metadata

#### Properties

##### `is_processed -> bool`
Check if file has been successfully processed.

##### `is_failed -> bool`
Check if file processing has failed.

##### `file_size_mb -> Optional[float]`
Get file size in megabytes.

##### `google_drive_url -> str`
Generate Google Drive URL for the file.

#### Methods

##### `mark_processing() -> None`
Mark file as currently being processed.

##### `mark_completed(transcript: str, task_url: str, duration_seconds: Optional[float] = None) -> None`
Mark file as successfully processed.

##### `mark_failed(error_message: str) -> None`
Mark file processing as failed.

##### `to_dict() -> Dict[str, Any]`
Convert to dictionary for serialization.

##### `from_dict(data: Dict[str, Any]) -> 'VoiceFile'` (classmethod)
Create instance from dictionary.

---

### NotionTask

Data model representing a Notion task created from voice recordings.

```python
from voice_task_manager.models.task import NotionTask

task = NotionTask(
    task_id="task_123",
    title="Meeting Notes",
    content="Transcript content here"
)
```

#### Attributes

- `task_id` (str): Notion page ID
- `title` (str): Task title
- `content` (str): Full task content
- `status` (str): Task status ('Inbox', 'In Progress', 'Done')
- `contexts` (List[str]): Context tags
- `created_at` (datetime): Creation timestamp
- `updated_at` (Optional[datetime]): Last update timestamp
- `url` (Optional[str]): Notion page URL
- `voice_file_id` (Optional[str]): Source voice file ID
- `transcript_source` (Optional[str]): Original transcript
- `metadata` (Dict[str, Any]): Additional metadata

#### Properties

##### `is_completed -> bool`
Check if task is marked as completed.

##### `is_in_progress -> bool`
Check if task is currently in progress.

##### `is_inbox -> bool`
Check if task is in inbox (unprocessed).

##### `has_voice_context -> bool`
Check if task has voice-related context tags.

##### `age_hours -> float`
Get task age in hours.

##### `age_days -> float`
Get task age in days.

#### Methods

##### `update_status(new_status: str) -> None`
Update task status and timestamp.

##### `add_context(context: str) -> None`
Add a context tag if not present.

##### `remove_context(context: str) -> None`
Remove a context tag if present.

##### `update_content(new_content: str) -> None`
Update task content and timestamp.

##### `create_from_voice(voice_file_id: str, transcript: str, task_id: str, url: str) -> 'NotionTask'` (classmethod)
Create NotionTask from voice recording.

##### `to_notion_data() -> Dict[str, Any]`
Convert to Notion API format.

##### `to_dict() -> Dict[str, Any]`
Convert to dictionary for serialization.

##### `from_dict(data: Dict[str, Any]) -> 'NotionTask'` (classmethod)
Create instance from dictionary.

---

### VoiceDatabase

Database interface for voice processing data.

```python
from voice_task_manager.utils.database import VoiceDatabase

db = VoiceDatabase(project_root=Path("/path/to/project"))
```

#### Methods

##### `save_voice_file(voice_file: VoiceFile) -> None`
Save or update a voice file record.

##### `get_voice_file(file_id: str) -> Optional[VoiceFile]`
Retrieve voice file by ID.

##### `get_all_voice_files(limit: Optional[int] = None) -> List[VoiceFile]`
Get all voice files.

##### `is_file_processed(file_id: str) -> bool`
Check if file has been processed.

##### `save_task(task: NotionTask) -> None`
Save or update a task record.

##### `get_task(task_id: str) -> Optional[NotionTask]`
Retrieve task by ID.

##### `get_tasks_by_voice_file(voice_file_id: str) -> List[NotionTask]`
Get tasks created from specific voice file.

##### `get_processing_stats() -> Dict[str, Any]`
Get processing statistics.

##### `get_files_by_date_range(start_date: datetime, end_date: datetime) -> List[VoiceFile]`
Get files within date range.

##### `cleanup_old_records(days_old: int = 90) -> int`
Remove old completed records.

---

## Integration Clients

### GoogleDriveClient

Interface to Google Drive API.

```python
from voice_task_manager.integrations.drive import GoogleDriveClient

drive = GoogleDriveClient()
```

#### Methods

##### `list_voice_files() -> List[Dict[str, Any]]`
List voice files from configured Drive folder.

##### `download_file(file_id: str, destination: Path) -> bool`
Download file from Drive.

##### `get_file_metadata(file_id: str) -> Dict[str, Any]`
Get file metadata from Drive.

---

### WhisperClient

Interface to OpenAI Whisper API.

```python
from voice_task_manager.integrations.whisper import WhisperClient

whisper = WhisperClient()
```

#### Methods

##### `transcribe_audio(audio_path: Path) -> str`
Transcribe audio file to text.

##### `transcribe_with_metadata(audio_path: Path) -> Dict[str, Any]`
Transcribe with additional metadata.

---

### NotionClient

Interface to Notion API.

```python
from voice_task_manager.integrations.notion import NotionClient

notion = NotionClient()
```

#### Methods

##### `create_task(title: str, content: str, contexts: List[str] = None) -> Dict[str, Any]`
Create new task in Notion.

##### `update_task(page_id: str, updates: Dict[str, Any]) -> Dict[str, Any]`
Update existing task.

##### `get_task(page_id: str) -> Dict[str, Any]`
Retrieve task from Notion.

---

## Utilities

### VoiceLogger

Logging system for voice processing.

```python
from voice_task_manager.utils.logging import VoiceLogger

logger = VoiceLogger(project_root)
```

#### Methods

##### `start_run() -> None`
Start a new processing run.

##### `log_file_processing(file_id: str, status: str, details: Dict[str, Any] = None) -> None`
Log file processing event.

##### `log_error(error: Exception, context: Dict[str, Any] = None) -> None`
Log error with context.

##### `get_recent_logs(limit: int = 100) -> List[Dict[str, Any]]`
Get recent log entries.

---

### PerformanceMonitor

Performance monitoring and metrics collection.

```python
from voice_task_manager.utils.performance import PerformanceMonitor, track_performance

# Using decorator
@track_performance("my_operation")
def my_function():
    # ... operation
    pass

# Using monitor directly
monitor = PerformanceMonitor()

@monitor.track_performance("database_query", track_memory=True)
def query_database():
    # ... database operation
    pass

# Get performance summary
summary = monitor.get_summary()
monitor.print_summary()
```

---

## CLI Interface

### Command Line Usage

```bash
# Process all voice files
vtm process

# Process with dry run
vtm process --dry-run

# Show processing stats
vtm stats

# Show recent logs
vtm logs --limit 20

# Clean up old records
vtm cleanup --days 90
```

### Programmatic CLI

```python
from voice_task_manager.cli import main

# Run CLI programmatically
main(['process', '--dry-run'])
```

---

## Configuration

### Environment Variables

- `GOOGLE_DRIVE_FOLDER_ID`: Google Drive folder to monitor
- `OPENAI_API_KEY`: OpenAI API key for Whisper
- `NOTION_API_TOKEN`: Notion integration token
- `NOTION_DATABASE_ID`: Notion database ID for tasks
- `PROJECT_ROOT`: Project root directory (optional)

### Configuration Files

The package looks for configuration in:
1. `.env` file in project root
2. Environment variables
3. Default values

---

## Error Handling

### Common Exceptions

```python
from voice_task_manager.exceptions import (
    VoiceProcessingError,
    TranscriptionError,
    NotionAPIError,
    DriveAPIError
)

try:
    processor.process_all_files()
except TranscriptionError as e:
    print(f"Transcription failed: {e}")
except NotionAPIError as e:
    print(f"Notion API error: {e}")
```

### Error Recovery

The system includes automatic retry logic:
- Failed transcriptions: Up to 3 retries
- API timeouts: Exponential backoff
- Network errors: Automatic retry with delays

---

## Examples

### Basic Usage

```python
from pathlib import Path
from voice_task_manager.core.processor import VoiceProcessor

# Initialize processor
processor = VoiceProcessor(project_root=Path("/path/to/project"))

# Process all files
results = processor.process_all_files()
print(f"Processed {results['files_processed']} files")
print(f"Success rate: {results['success_rate']}%")
```

### Custom Processing

```python
from voice_task_manager.models.voice_file import VoiceFile
from voice_task_manager.utils.database import VoiceDatabase

# Get database instance
db = VoiceDatabase(project_root)

# Find unprocessed files
unprocessed = [f for f in db.get_all_voice_files() if not f.is_processed]

# Process specific files
for voice_file in unprocessed[:5]:  # Process first 5
    success = processor.process_single_file(voice_file)
    print(f"File {voice_file.file_id}: {'✅' if success else '❌'}")
```

### Performance Monitoring

```python
from voice_task_manager.utils.performance import PerformanceIntegration

# Enhance processor with monitoring
processor = VoiceProcessor()
PerformanceIntegration.enhance_voice_processor(type(processor))

# Process files (now with monitoring)
processor.process_all_files()

# View performance summary
from voice_task_manager.utils.performance import print_performance_summary
print_performance_summary()
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_models.py
pytest tests/test_database.py
pytest tests/test_performance.py

# Run with coverage
pytest --cov=voice_task_manager
```

### Creating Test Data

```python
from voice_task_manager.models.voice_file import VoiceFile
from voice_task_manager.models.task import NotionTask

# Create test voice file
test_file = VoiceFile(
    file_id="test_123",
    file_size=1024000,
    content_type="audio/m4a"
)
test_file.mark_completed("Test transcript", "https://notion.so/test")

# Create test task
test_task = NotionTask(
    task_id="task_123",
    title="Test Task",
    content="Test content",
    contexts=["test", "voice"]
)
```