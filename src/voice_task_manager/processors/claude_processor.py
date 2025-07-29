"""Claude-based intelligent voice task processor"""

import subprocess
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..adapters.base import TaskData
from ..adapters.graphrag import GraphRAGTaskAdapter
from ..utils.logging import VoiceLogger


class ClaudeVoiceProcessor:
    """Process voice transcripts using Claude with full context awareness"""
    
    def __init__(self, adapter: GraphRAGTaskAdapter = None, logger: Optional[VoiceLogger] = None):
        """
        Initialize Claude processor
        
        Args:
            adapter: GraphRAG adapter for context retrieval
            logger: Logger instance
        """
        self.adapter = adapter or GraphRAGTaskAdapter(logger=logger)
        self.logger = logger or VoiceLogger()
        self.claude_project = "task-management"
    
    def process_transcript(self, transcript: str, voice_file_id: str) -> Optional[TaskData]:
        """
        Process voice transcript with intelligent categorization
        
        Args:
            transcript: Transcribed voice text
            voice_file_id: ID of the source voice file
            
        Returns:
            TaskData with proper categorization, or None if failed
        """
        self.logger.info(f"Processing transcript with Claude: {transcript[:100]}...")
        
        # Get categorization context from GraphRAG
        context = self.adapter.get_categorization_context()
        
        # Build Claude prompt with context
        prompt = self._build_categorization_prompt(transcript, context)
        
        # Execute Claude with MCP access
        try:
            result = self._execute_claude_with_mcp(prompt)
            
            if not result.get("success"):
                self.logger.error(f"Claude processing failed: {result.get('error')}")
                return None
            
            # Parse the structured response
            task_info = result.get("task_data", {})
            
            # Create TaskData object
            task_data = TaskData(
                name=task_info.get("name", f"Voice Note: {transcript[:60]}..."),
                description=task_info.get("description", transcript),
                status=task_info.get("status", "Inbox"),
                priority=task_info.get("priority", "Medium"),
                contexts=task_info.get("contexts", ["voice", "auto-processed"]),
                project_id=task_info.get("project_id"),
                project_name=task_info.get("project_name"),
                area_id=task_info.get("area_id"),
                area_name=task_info.get("area_name"),
                goal_id=task_info.get("goal_id"),
                goal_name=task_info.get("goal_name"),
                source="voice",
                metadata={
                    "voice_file_id": voice_file_id,
                    "claude_confidence": task_info.get("confidence", 0),
                    "reasoning": task_info.get("reasoning", "")
                }
            )
            
            self.logger.success(
                f"Task categorized: Project={task_data.project_name}, "
                f"Area={task_data.area_name}, Priority={task_data.priority}"
            )
            
            return task_data
            
        except Exception as e:
            self.logger.error(f"Error in Claude processing: {e}")
            return None
    
    def _build_categorization_prompt(self, transcript: str, context: Dict[str, Any]) -> str:
        """Build Claude prompt with full context"""
        
        # Format recent tasks for context
        recent_tasks_text = ""
        if context.get("recent_tasks"):
            recent_examples = []
            for task in context["recent_tasks"][:5]:  # Show 5 most recent
                if task.get("project_name"):
                    recent_examples.append(
                        f'- "{task["title"]}" → Project: {task["project_name"]}'
                    )
            if recent_examples:
                recent_tasks_text = "Recent voice task categorizations:\\n" + "\\n".join(recent_examples)
        
        # Format available projects
        projects_text = ""
        if context.get("project_patterns"):
            project_list = []
            for proj_id, proj_info in context["project_patterns"].items():
                project_list.append(
                    f'- {proj_info["name"]} (Area: {proj_info["area_name"]})'
                )
            if project_list:
                projects_text = "Available projects:\\n" + "\\n".join(project_list[:20])  # Top 20
        
        # Format available areas
        areas_text = ""
        if context.get("area_descriptions"):
            area_list = []
            for area_id, area_info in context["area_descriptions"].items():
                area_list.append(f'- {area_info["name"]}')
            if area_list:
                areas_text = "Available areas:\\n" + "\\n".join(area_list)
        
        prompt = f"""You are processing a voice task transcript. Analyze it and determine:
1. The appropriate task name (concise, action-oriented)
2. Which project it belongs to (if any)
3. Which area it relates to
4. The priority level
5. Any specific contexts/tags

Voice transcript: "{transcript}"

{recent_tasks_text}

{projects_text}

{areas_text}

Instructions:
1. First, use the mcp__agent-db__query_natural_language tool to search for relevant projects based on the transcript content
2. If you find a matching project, get its area relationship
3. If no exact project match, consider creating a new task without a project but suggest which area it might belong to
4. Extract any specific contexts mentioned (e.g., @phone, @computer, @home)
5. Determine priority based on urgency words or context

Return a JSON response with this structure:
{{
    "success": true,
    "task_data": {{
        "name": "Clear, actionable task name",
        "description": "Full transcript or enhanced description",
        "status": "Inbox",
        "priority": "Low|Medium|High|Urgent",
        "contexts": ["voice", "auto-processed", "any-other-contexts"],
        "project_id": "notion_id if found",
        "project_name": "Project name if found",
        "area_id": "notion_id if found",
        "area_name": "Area name if found",
        "confidence": 0.0-1.0,
        "reasoning": "Brief explanation of categorization"
    }}
}}

IMPORTANT: Use the MCP tools to search for and verify project/area relationships before making assignments."""
        
        return prompt
    
    def _execute_claude_with_mcp(self, prompt: str) -> Dict[str, Any]:
        """Execute Claude with MCP access for intelligent processing"""
        try:
            # Use Claude with project context and MCP access
            cmd = [
                "claude", 
                "-p", self.claude_project,
                "--dangerously-skip-permissions"
            ]
            
            # Add instruction to use MCP tools
            full_prompt = f"""{prompt}

Remember to:
1. Use mcp__agent-db__query_natural_language to search for relevant projects
2. Use mcp__agent-db__execute_cypher if you need specific relationship queries
3. Return ONLY the JSON response, no explanations"""
            
            result = subprocess.run(
                cmd,
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=60  # Longer timeout for MCP operations
            )
            
            if result.returncode != 0:
                return {"success": False, "error": f"Claude execution failed: {result.stderr}"}
            
            # Parse JSON from Claude's response
            output = result.stdout.strip()
            
            # Extract JSON (Claude might include tool use output)
            import re
            json_match = re.search(r'\{.*"success".*\}', output, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback: try to parse the whole output
                try:
                    return json.loads(output)
                except:
                    self.logger.error(f"Failed to parse Claude response: {output[:500]}")
                    return {"success": False, "error": "Invalid JSON response"}
                    
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Claude execution timed out"}
        except Exception as e:
            return {"success": False, "error": f"Execution error: {str(e)}"}
    
    def batch_process_transcripts(self, transcripts: List[Dict[str, str]]) -> List[TaskData]:
        """
        Process multiple transcripts in batch
        
        Args:
            transcripts: List of dicts with 'transcript' and 'file_id' keys
            
        Returns:
            List of TaskData objects
        """
        results = []
        
        for item in transcripts:
            task_data = self.process_transcript(
                item['transcript'], 
                item.get('file_id', 'unknown')
            )
            if task_data:
                results.append(task_data)
        
        return results