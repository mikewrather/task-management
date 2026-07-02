import os
from datetime import datetime
from pathlib import Path

from voice_task_manager.core.processor import VoiceProcessorV2
from voice_task_manager.models.voice_file import VoiceFile
from voice_task_manager.utils.database import VoiceDatabase


class FakeLogger:
    def info(self, *args, **kwargs):
        pass

    def success(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass


class FakeDriveClient:
    def download_file(self, voice_file):
        return b"audio bytes"


class FakeWhisperClient:
    def validate_audio_format(self, voice_file):
        return True, "ok"

    def transcribe_with_retry(self, voice_file, audio_content):
        return {
            "text": "Remember to send the updated project plan.",
            "duration": 12.5,
            "word_count": 8,
        }


class FailingAdapter:
    def create_task(self, task_data):
        raise RuntimeError("GraphRAG unavailable")


class SuccessfulAdapter:
    def create_task(self, task_data):
        return "task-123"


def build_processor(project_root: Path, adapter):
    processor = VoiceProcessorV2.__new__(VoiceProcessorV2)
    processor.project_root = project_root
    processor.logger = FakeLogger()
    processor.database = VoiceDatabase(project_root)
    processor.drive_client = FakeDriveClient()
    processor.whisper_client = FakeWhisperClient()
    processor.use_claude_processor = False
    processor.adapters = [adapter]
    return processor


def test_process_single_file_writes_transcript_file_with_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("WRITE_TRANSCRIPT_FILE", "true")
    processor = build_processor(tmp_path, SuccessfulAdapter())
    discovered_at = datetime(2026, 7, 2, 9, 30, 0)
    voice_file = VoiceFile(file_id="drive-file-123", discovered_at=discovered_at)

    result = processor.process_single_file(voice_file)

    transcript_path = tmp_path / "transcripts" / "2026-07-02-drive-file-123.md"
    assert result is not None
    assert result["transcript_file"] == str(transcript_path)
    assert transcript_path.exists()
    content = transcript_path.read_text(encoding="utf-8")
    assert "source_file_id: drive-file-123" in content
    assert "discovered_at: 2026-07-02T09:30:00" in content
    assert "processed_at:" in content
    assert "duration_seconds: 12.5" in content
    assert content.endswith("Remember to send the updated project plan.\n")

    saved_file = processor.database.get_voice_file("drive-file-123")
    assert saved_file.status == "completed"
    assert saved_file.transcript == "Remember to send the updated project plan."


def test_process_single_file_writes_transcript_when_graphrag_fails_and_mcp_disabled(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("WRITE_TRANSCRIPT_FILE", "true")
    monkeypatch.setenv("USE_REAL_MCP", "false")
    processor = build_processor(tmp_path, FailingAdapter())
    voice_file = VoiceFile(file_id="drive/file:bad", discovered_at=datetime(2026, 7, 3))

    result = processor.process_single_file(voice_file)

    transcript_path = tmp_path / "transcripts" / "2026-07-03-drive_file_bad.md"
    assert result is not None
    assert result["created_tasks"] == []
    assert result["transcript_file"] == str(transcript_path)
    assert transcript_path.exists()
    assert "Remember to send the updated project plan." in transcript_path.read_text(
        encoding="utf-8",
    )

    saved_file = processor.database.get_voice_file("drive/file:bad")
    assert saved_file.status == "completed"
    assert saved_file.transcript == "Remember to send the updated project plan."
    assert saved_file.task_url == f"Transcript written: {transcript_path}"
    assert os.environ["USE_REAL_MCP"] == "false"
