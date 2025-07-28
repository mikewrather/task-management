#!/usr/bin/env python3
"""
Test script for voice task management pipeline
Tests each component individually before setting up n8n
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
import openai
from notion_client import Client

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_TASKS_DB = os.getenv("NOTION_TASKS_DB")
NOTION_REVIEW_DB = os.getenv("NOTION_REVIEW_DB")

class VoiceTaskPipeline:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.notion = Client(auth=NOTION_TOKEN)
        
    def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio file using Whisper"""
        print(f"Transcribing {audio_file_path}...")
        
        with open(audio_file_path, "rb") as audio_file:
            response = self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        
        print(f"Transcript: {response}")
        return response
    
    def fetch_notion_context(self) -> Dict:
        """Fetch current tasks and projects from Notion"""
        print("Fetching Notion context...")
        
        # Query open tasks
        tasks_response = self.notion.databases.query(
            database_id=NOTION_TASKS_DB,
            filter={
                "property": "Status",
                "select": {
                    "does_not_equal": "Done"
                }
            }
        )
        
        tasks = []
        for page in tasks_response["results"]:
            task = {
                "id": page["id"],
                "title": page["properties"]["Title"]["title"][0]["plain_text"] if page["properties"]["Title"]["title"] else "",
                "status": page["properties"]["Status"]["select"]["name"] if page["properties"]["Status"]["select"] else "Todo"
            }
            tasks.append(task)
        
        context = {
            "open_tasks": tasks,
            "task_count": len(tasks)
        }
        
        print(f"Found {len(tasks)} open tasks")
        return context
    
    def analyze_transcript(self, transcript: str, context: Dict) -> Dict:
        """Use GPT-4 to analyze transcript and extract tasks"""
        print("Analyzing transcript with GPT-4...")
        
        system_prompt = """You are a task management assistant. Analyze voice transcripts and extract:
1. completed_tasks: Array of task titles that were completed
2. new_tasks: Array of {title, priority} objects
3. notes: Array of {content} objects  
4. ambiguous_notes: Array of {content, confidence, reason} objects

Be conservative - if unsure about interpretation, mark as ambiguous.
Output valid JSON only."""

        user_prompt = f"""Transcript: {transcript}

Current open tasks: {json.dumps(context['open_tasks'], indent=2)}

Extract tasks and notes from the transcript."""

        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        print(f"Analysis result: {json.dumps(result, indent=2)}")
        return result
    
    def update_notion(self, analysis: Dict, original_transcript: str):
        """Update Notion based on analysis results"""
        print("Updating Notion...")
        
        # Create new tasks
        for task in analysis.get("new_tasks", []):
            self.notion.pages.create(
                parent={"database_id": NOTION_TASKS_DB},
                properties={
                    "Title": {"title": [{"text": {"content": task["title"]}}]},
                    "Status": {"select": {"name": "Todo"}},
                    "Priority": {"select": {"name": task.get("priority", "Medium")}},
                    "Source": {"select": {"name": "Voice"}},
                    "Original Transcript": {"rich_text": [{"text": {"content": original_transcript}}]}
                }
            )
            print(f"Created task: {task['title']}")
        
        # Add ambiguous notes to review queue
        for note in analysis.get("ambiguous_notes", []):
            self.notion.pages.create(
                parent={"database_id": NOTION_REVIEW_DB},
                properties={
                    "Transcript": {"title": [{"text": {"content": note["content"]}}]},
                    "Recording Date": {"date": {"start": datetime.now().isoformat()}},
                    "Confidence": {"number": note.get("confidence", 50)},
                    "Suggested Action": {"rich_text": [{"text": {"content": note.get("reason", "")}}]},
                    "Status": {"select": {"name": "Pending"}}
                }
            )
            print(f"Added to review: {note['content'][:50]}...")
    
    def process_voice_note(self, audio_file_path: str):
        """Complete pipeline for processing a voice note"""
        print(f"\n{'='*50}")
        print(f"Processing voice note: {audio_file_path}")
        print(f"{'='*50}\n")
        
        try:
            # Step 1: Transcribe
            transcript = self.transcribe_audio(audio_file_path)
            
            # Step 2: Get context
            context = self.fetch_notion_context()
            
            # Step 3: Analyze
            analysis = self.analyze_transcript(transcript, context)
            
            # Step 4: Update Notion
            self.update_notion(analysis, transcript)
            
            print("\n✅ Processing complete!")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            raise

def test_components():
    """Test individual components before full pipeline"""
    pipeline = VoiceTaskPipeline()
    
    print("Testing Notion connection...")
    try:
        context = pipeline.fetch_notion_context()
        print("✅ Notion connection successful")
    except Exception as e:
        print(f"❌ Notion connection failed: {e}")
        return
    
    print("\nTesting OpenAI connection...")
    try:
        test_transcript = "This is a test transcript"
        analysis = pipeline.analyze_transcript(test_transcript, context)
        print("✅ OpenAI connection successful")
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return
    
    print("\n✅ All components working!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Test components: python test-voice-pipeline.py test")
        print("  Process file: python test-voice-pipeline.py process <audio_file>")
        sys.exit(1)
    
    if sys.argv[1] == "test":
        test_components()
    elif sys.argv[1] == "process" and len(sys.argv) > 2:
        pipeline = VoiceTaskPipeline()
        pipeline.process_voice_note(sys.argv[2])
    else:
        print("Invalid arguments")