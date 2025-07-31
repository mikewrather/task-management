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
                    "reasoning": task_info.get("reasoning", ""),
                    "additional_tasks": task_info.get("additional_tasks", [])
                }
            )
            
            self.logger.success(
                f"Task categorized: Project={task_data.project_name}, "
                f"Area={task_data.area_name}, Priority={task_data.priority}"
            )
            
            # Log if additional tasks were mentioned
            additional_tasks = task_info.get("additional_tasks", [])
            if additional_tasks and len(additional_tasks) > 0:
                # Filter out example entries
                real_additional_tasks = [t for t in additional_tasks if not t.startswith("List any") and not t.startswith("E.g.,")]
                if real_additional_tasks:
                    self.logger.info(
                        f"📝 Additional tasks mentioned ({len(real_additional_tasks)}): {', '.join(real_additional_tasks[:3])}"
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
        
        prompt = f"""You are an intelligent task categorization system. Your job is to analyze a voice transcript and establish proper relationships with existing projects and areas in the GraphRAG database.

Voice transcript: "{transcript}"

{recent_tasks_text}

{projects_text}

{areas_text}

IMPORTANT: ANALYZE THE TRANSCRIPT STRUCTURE FIRST:

1. **Single vs Multiple Tasks**:
   - If the transcript contains multiple distinct tasks (e.g., "I need to do X. Also, Y. And don't forget Z"), you should focus on the FIRST task only
   - Return a clear, actionable task name, NOT the entire transcript
   - Examples:
     - Bad: "I just thought of a couple things for sleep worlds..."
     - Good: "Set up Android emulator for Adapty migration testing"

2. **Task Extraction Guidelines**:
   - Extract the core action from conversational language
   - Create succinct, actionable task names (verb + object)
   - Put additional context in the description, not the title
   - If multiple tasks are mentioned, note in reasoning that additional tasks were mentioned

CRITICAL INSTRUCTIONS FOR RELATIONSHIP DISCOVERY:

1. **Search for Related Entities** (MANDATORY):
   - Use mcp__agent-db__query_natural_language to search for: "{transcript}"
   - Look for projects, areas, and similar tasks that might be related
   - Search with different keywords from the transcript if the first search yields no results
   - Consider partial matches and semantic similarity

2. **Establish Project Relationships**:
   - If the transcript mentions a project name (even partially), search for it
   - If the task is clearly related to an existing project's scope, link it
   - Use mcp__agent-db__execute_cypher to query relationships if needed:
     MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA) WHERE p.name CONTAINS 'keyword' RETURN p, a

3. **Determine Area Assignment**:
   - Every task should have an area if possible
   - If no project is found, still try to match to an appropriate area
   - Areas are broader than projects (e.g., "Work", "Personal", "Health", etc.)

4. **Create Meaningful Relationships**:
   - Don't leave tasks orphaned without relationships
   - If unsure between two projects/areas, choose the most likely one and explain in reasoning
   - Look at similar recent tasks to understand patterns

5. **Extract Context and Priority**:
   - Contexts: location (@home, @office), tool (@computer, @phone), time (@evening)
   - Priority: Listen for urgency words ("urgent", "ASAP", "important", "quick")

SEARCH STRATEGY:
- First search: Full transcript
- Second search: Key nouns/verbs from transcript
- Third search: Look for similar tasks and their relationships

EXAMPLES OF GOOD TASK EXTRACTION:

Transcript: "I just thought of a couple things for sleep worlds. I need to figure out if I can get the emulator set up for android to automate the testing of the adapty migration. Also, I need to make sure that I'm forwarding events from adapty to revenuecat until we cut over"
Good Task Name: "Set up Android emulator for Adapty migration testing"
Description: "Configure Android emulator to automate testing of the Adapty migration in Sleep Worlds. Note: Also need to forward events from Adapty to RevenueCat until cutover."
Project: Search for "Adapty Migration" project
Area: "Sleep Worlds" or "[Sleep Worlds] Android"

Transcript: "For the house, I need to call the plumber about the kitchen sink and also get quotes for the new fence"
Good Task Name: "Call plumber about kitchen sink"
Description: "Kitchen sink issue needs plumber attention. Note: Also need to get fence quotes."
Project: Search for home maintenance projects
Area: "House"

Return a JSON response:
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
        "reasoning": "Explain: 1) What searches you performed, 2) Why you chose this project/area, 3) If multiple tasks were mentioned, list them, 4) Any assumptions made",
        "additional_tasks": [
            "List any other tasks mentioned in the transcript that should be created separately",
            "E.g., 'Forward events from Adapty to RevenueCat until cutover'"
        ]
    }}
}}

REMEMBER: Your goal is to create a well-connected knowledge graph. Every task should have meaningful relationships whenever possible."""
        
        return prompt
    
    def _execute_claude_with_mcp(self, prompt: str) -> Dict[str, Any]:
        """Execute Claude with MCP access for intelligent processing"""
        try:
            # Use Claude with project context and MCP access
            # Use full path to claude command
            claude_path = "/home/mike/.nvm/versions/node/v24.2.0/bin/claude"
            
            # Add instruction to use MCP tools
            full_prompt = f"""{prompt}

Remember to:
1. Use mcp__agent-db__query_natural_language to search for relevant projects and areas
2. Use mcp__agent-db__execute_cypher for specific queries like:
   - MATCH (p:PROJECT) WHERE toLower(p.name) CONTAINS toLower('keyword') RETURN p
   - MATCH (a:AREA) WHERE toLower(a.name) CONTAINS toLower('keyword') RETURN a
   - MATCH (t:TASK)-[:BELONGS_TO]->(p:PROJECT) WHERE t.name CONTAINS 'similar' RETURN t, p
3. Return ONLY the JSON response, no explanations"""
            
            cmd = [
                claude_path, 
                "-p", full_prompt,
                "--dangerously-skip-permissions",
                "--output-format", "json"
            ]
            
            self.logger.info(f"Executing Claude with MCP access")
            self.logger.debug(f"Prompt length: {len(full_prompt)} characters")
            
            # Change to project directory to use its .mcp.json
            import os
            original_cwd = os.getcwd()
            project_dir = "/home/mike/development/task-management"
            
            try:
                os.chdir(project_dir)
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=None,  # No timeout - let Claude finish
                    env={**os.environ, "PYTHONPATH": f"{project_dir}/src:{os.environ.get('PYTHONPATH', '')}"}
                )
            finally:
                os.chdir(original_cwd)
            
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
                    
        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Claude execution timed out after 120 seconds")
            # Try to get partial output
            if hasattr(e, 'stdout') and e.stdout:
                self.logger.debug(f"Partial stdout: {e.stdout[:500]}")
            if hasattr(e, 'stderr') and e.stderr:
                self.logger.debug(f"Partial stderr: {e.stderr[:500]}")
            return {"success": False, "error": "Claude execution timed out after 120 seconds"}
        except Exception as e:
            self.logger.error(f"Unexpected error in Claude execution: {e}")
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