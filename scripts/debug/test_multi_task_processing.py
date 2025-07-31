#!/usr/bin/env python3
"""Test multi-task processing from a single voice transcript"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from voice_task_manager.processors.claude_processor import ClaudeVoiceProcessor
from voice_task_manager.utils.logging import VoiceLogger

# Test transcript with multiple tasks
test_transcript = """
I need to do a few things today. First, I need to call the dentist to schedule my cleaning. 
Also, I should review the Q4 budget report for the finance meeting. 
And don't forget to pick up groceries on the way home - we need milk, eggs, and bread.
"""

# Initialize processor
logger = VoiceLogger()
processor = ClaudeVoiceProcessor(logger=logger)

# Process the transcript
print("\n🎤 Processing transcript with multiple tasks...\n")
print(f"Transcript: {test_transcript.strip()}\n")
print("="*80)

tasks = processor.process_transcript(test_transcript, "test_multi_001")

print(f"\n✅ Created {len(tasks)} tasks:\n")

for i, task in enumerate(tasks, 1):
    print(f"Task {i}: {task.name}")
    print(f"  Project: {task.project_name or 'None'}")
    print(f"  Area: {task.area_name or 'None'}")
    print(f"  Priority: {task.priority}")
    print(f"  Contexts: {', '.join(task.contexts)}")
    print(f"  Description: {task.description[:100]}..." if len(task.description) > 100 else f"  Description: {task.description}")
    print()