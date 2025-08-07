"""Claude-based intelligent voice task processor"""

import subprocess
import json
import os
from typing import Dict, Any, List, Optional, Tuple
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
    
    def process_transcript(self, transcript: str, voice_file_id: str) -> List[TaskData]:
        """
        Process voice transcript with intelligent categorization
        
        Args:
            transcript: Transcribed voice text
            voice_file_id: ID of the source voice file
            
        Returns:
            List of TaskData objects with proper categorization
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
                return []
            
            # Parse the tasks array from response
            tasks_data = result.get("tasks", [])
            overall_reasoning = result.get("overall_reasoning", "")
            
            if not tasks_data:
                # Fallback: create a single task if no tasks returned
                self.logger.warning("No tasks returned by Claude, creating fallback task")
                return [TaskData(
                    name=f"Voice Note: {transcript[:60]}...",
                    description=transcript,
                    status="Inbox",
                    priority="Medium",
                    contexts=["voice", "auto-processed"],
                    source="voice",
                    metadata={"voice_file_id": voice_file_id}
                )]
            
            # Create TaskData objects for each task
            created_tasks = []
            for i, task_info in enumerate(tasks_data):
                # Handle project creation if needed
                project_id = task_info.get("project_id")
                project_name = task_info.get("project_name")
                
                if task_info.get("create_project", False) and task_info.get("suggested_project"):
                    # Attempt to create the suggested project
                    project_id, project_name = self._create_project_if_needed(task_info.get("suggested_project"))
                    if project_id:
                        self.logger.success(f"Created new project: '{project_name}' (ID: {project_id})")
                    else:
                        self.logger.warning(f"Failed to create suggested project: '{task_info['suggested_project'].get('name')}'")
                
                task_data = TaskData(
                    name=task_info.get("name", f"Voice Task {i+1}: {transcript[:50]}..."),
                    description=task_info.get("description", transcript),
                    status=task_info.get("status", "Inbox"),
                    priority=task_info.get("priority", "Medium"),
                    contexts=task_info.get("contexts", ["voice", "auto-processed"]),
                    project_node_id=project_id,
                    project_name=project_name,
                    area_node_id=task_info.get("area_node_id"),
                    area_name=task_info.get("area_name"),
                    goal_node_id=task_info.get("goal_node_id"),
                    goal_name=task_info.get("goal_name"),
                    source="voice",
                    metadata={
                        "voice_file_id": voice_file_id,
                        "claude_confidence": task_info.get("confidence", 0),
                        "reasoning": task_info.get("reasoning", ""),
                        "task_number": i + 1,
                        "total_tasks": len(tasks_data),
                        "overall_reasoning": overall_reasoning,
                        "project_created": task_info.get("create_project", False)
                    }
                )
                
                created_tasks.append(task_data)
                
                self.logger.success(
                    f"Task {i+1}/{len(tasks_data)} categorized: '{task_data.name}' "
                    f"Project={task_data.project_name}, Area={task_data.area_name}"
                )
            
            if len(created_tasks) > 1:
                self.logger.info(f"✨ Created {len(created_tasks)} tasks from single voice note")
            
            return created_tasks
            
        except Exception as e:
            self.logger.error(f"Error in Claude processing: {e}")
            return []
    
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
            for proj_node_id, proj_info in context["project_patterns"].items():
                project_list.append(
                    f'- {proj_info["name"]} (Node ID: {proj_node_id}, Area: {proj_info["area_name"]})'
                )
            if project_list:
                projects_text = "Available projects:\\n" + "\\n".join(project_list[:20])  # Top 20
        
        # Format available areas
        areas_text = ""
        if context.get("area_descriptions"):
            area_list = []
            for area_node_id, area_info in context["area_descriptions"].items():
                area_list.append(f'- {area_info["name"]} (Node ID: {area_node_id})')
            if area_list:
                areas_text = "Available areas:\\n" + "\\n".join(area_list)
        
        prompt = f"""You are an intelligent task categorization system. Your job is to analyze a voice transcript and establish proper relationships with existing projects and areas in the GraphRAG database.

Voice transcript: "{transcript}"

{recent_tasks_text}

{projects_text}

{areas_text}

IMPORTANT: ANALYZE THE TRANSCRIPT STRUCTURE FIRST:

1. **Single vs Multiple Tasks**:
   - If the transcript contains multiple distinct tasks (e.g., "I need to do X. Also, Y. And don't forget Z"), you should extract ALL of them
   - Return an array of tasks, each with its own categorization
   - Each task should have a clear, actionable name
   - Examples:
     - Transcript: "I need to call the plumber and schedule dentist appointment"
     - Returns: Two tasks: "Call plumber" and "Schedule dentist appointment"

2. **Task Extraction Guidelines**:
   - Extract EVERY distinct action from the transcript
   - Create succinct, actionable task names (verb + object)
   - Each task gets its own project/area assignment
   - Tasks can share the same project/area if appropriate
   - Put context specific to each task in its description

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

5. **Project Creation When None Found**:
   - If you find a suitable area but NO matching project for a task, consider creating one
   - Only suggest project creation when:
     * The task clearly represents a cohesive project scope (e.g., "API integration", "feature development")
     * An area exists that would logically contain this project
     * The task is substantial enough to warrant its own project (not just a single quick action)
   - Generate a meaningful project name and description based on the task context
   - Set `create_project: true` and provide `suggested_project` details in the response

6. **Extract Context and Priority**:
   - Contexts: location (@home, @office), tool (@computer, @phone), time (@evening)
   - Priority: Listen for urgency words ("urgent", "ASAP", "important", "quick")

SEARCH STRATEGY:
- First search: Full transcript
- Second search: Key nouns/verbs from transcript
- Third search: Look for similar tasks and their relationships

EXAMPLES OF GOOD TASK EXTRACTION:

Transcript: "I just thought of a couple things for sleep worlds. I need to figure out if I can get the emulator set up for android to automate the testing of the adapty migration. Also, I need to make sure that I'm forwarding events from adapty to revenuecat until we cut over"
Returns TWO tasks:
Task 1: "Set up Android emulator for Adapty migration testing"
Description: "Configure Android emulator to automate testing of the Adapty migration in Sleep Worlds"
Project: "Adapty Migration" 
Area: "Sleep Worlds"

Task 2: "Forward events from Adapty to RevenueCat until cutover"
Description: "Ensure event forwarding is configured between Adapty and RevenueCat during migration period"
Project: "Adapty Migration"
Area: "Sleep Worlds"

Transcript: "For the house, I need to call the plumber about the kitchen sink and also get quotes for the new fence"
Returns TWO tasks:
Task 1: "Call plumber about kitchen sink"
Description: "Kitchen sink issue needs plumber attention"
Project: "Home Maintenance"
Area: "House"

Task 2: "Get quotes for new fence"
Description: "Research and collect quotes for fence replacement/installation"
Project: "Home Improvement" 
Area: "House"

Return a JSON response:
{{
    "success": true,
    "tasks": [
        {{
            "name": "Clear, actionable task name for first task",
            "description": "Detailed description for this specific task",
            "status": "Inbox",
            "priority": "Low|Medium|High|Urgent",
            "contexts": ["voice", "auto-processed", "@location", "@tool"],
            "project_node_id": "node_id if found",
            "project_name": "Project name if found",
            "area_node_id": "node_id if found", 
            "area_name": "Area name if found",
            "create_project": false,
            "suggested_project": {{"name": "Project Name", "description": "Project Description", "area_node_id": "area_node_id"}},
            "confidence": 0.0-1.0,
            "reasoning": "Why this categorization was chosen for this task"
        }},
        {{
            "name": "Clear, actionable task name for second task (if exists)",
            "description": "Detailed description for this specific task",
            "status": "Inbox",
            "priority": "Low|Medium|High|Urgent",
            "contexts": ["voice", "auto-processed", "@location", "@tool"],
            "project_node_id": "node_id if found",
            "project_name": "Project name if found", 
            "area_node_id": "node_id if found",
            "area_name": "Area name if found",
            "create_project": false,
            "suggested_project": {{"name": "Project Name", "description": "Project Description", "area_node_id": "area_node_id"}},
            "confidence": 0.0-1.0,
            "reasoning": "Why this categorization was chosen for this task"
        }}
        // ... more tasks as needed
    ],
    "overall_reasoning": "Explain: 1) What searches you performed, 2) How many tasks were found, 3) Any shared context between tasks, 4) Any assumptions made"
}}

IMPORTANT: 
- Always return an array in "tasks", even if there's only one task
- Each task should be independently actionable
- Tasks can share projects/areas when appropriate
- Extract ALL distinct tasks from the transcript

REMEMBER: Your goal is to create a well-connected knowledge graph. Every task should have meaningful relationships whenever possible."""
        
        return prompt
    
    def _execute_claude_with_mcp(self, prompt: str) -> Dict[str, Any]:
        """Execute Claude with MCP access for intelligent processing"""
        # Define project_dir at the start to avoid scope issues
        import os
        original_cwd = os.getcwd()
        project_dir = "/home/mike/development/task-management"
        
        try:
            # Use Claude with project context and MCP access
            # Use full path to claude command
            claude_path = "/home/mike/.claude/local/claude"
            
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
                "--mcp-config", f"{project_dir}/.mcp.json",
                "--output-format", "json"
            ]
            
            self.logger.info(f"Executing Claude with MCP access")
            self.logger.debug(f"Prompt length: {len(full_prompt)} characters")
            
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
                error_msg = f"Claude execution failed: {result.stderr}"
                self.logger.claude_response(
                    prompt=full_prompt,
                    raw_output=result.stderr or "",
                    error=error_msg
                )
                return {"success": False, "error": error_msg}
            
            # Parse JSON from Claude's response
            output = result.stdout.strip()
            
            # Debug: Log basic Claude response info
            if result.stderr:
                self.logger.debug(f"Claude stderr: {result.stderr[:500]}")
            
            # Extract JSON (Claude might include tool use output)
            import re
            parsed_result = None
            parse_error = None
            
            # First, check if this is a Claude Code execution result format
            try:
                parsed_output = json.loads(output)
                if isinstance(parsed_output, dict) and "result" in parsed_output:
                    # Extract the actual result from Claude Code wrapper
                    inner_result = parsed_output["result"]
                    if isinstance(inner_result, str):
                        # Try to parse the inner result as JSON
                        try:
                            parsed_result = json.loads(inner_result)
                        except json.JSONDecodeError:
                            # Check if it's wrapped in markdown code blocks
                            json_block_match = re.search(r'```json\s*(.*?)\s*```', inner_result, re.DOTALL)
                            if json_block_match:
                                try:
                                    parsed_result = json.loads(json_block_match.group(1))
                                except json.JSONDecodeError:
                                    pass
                            # If inner result isn't JSON, fall through to regex extraction
                            pass
                    elif isinstance(inner_result, dict):
                        parsed_result = inner_result
            except json.JSONDecodeError:
                pass
            
            # If we didn't get a result yet, try other parsing methods
            if parsed_result is None:
                # Look for JSON with either "success" or "tasks" key
                json_match = re.search(r'\{.*(?:"success"|"tasks").*\}', output, re.DOTALL)
                if json_match:
                    try:
                        parsed_result = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        parse_error = f"Invalid JSON in match: {json_match.group()[:200]}"
                        
                # Fallback: try to parse the whole output
                if parsed_result is None:
                    try:
                        parsed_result = json.loads(output)
                    except:
                        # Try to extract JSON from Claude's response format
                        try:
                            # Claude might wrap in ```json blocks
                            json_block_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
                            if json_block_match:
                                parsed_result = json.loads(json_block_match.group(1))
                        except:
                            pass
            
            # Log the Claude response for debugging
            if parsed_result is not None:
                self.logger.claude_response(
                    prompt=full_prompt,
                    raw_output=output,
                    parsed_result=parsed_result
                )
                return parsed_result
            else:
                error_msg = parse_error or f"Failed to parse Claude response: {output[:500]}"
                self.logger.claude_response(
                    prompt=full_prompt,
                    raw_output=output,
                    error=error_msg
                )
                return {"success": False, "error": f"Invalid JSON response: {output[:200]}"}
                    
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
            List of TaskData objects (flattened from all transcripts)
        """
        all_tasks = []
        
        for item in transcripts:
            tasks = self.process_transcript(
                item['transcript'], 
                item.get('file_id', 'unknown')
            )
            all_tasks.extend(tasks)
        
        self.logger.info(f"Batch processing complete: {len(all_tasks)} total tasks from {len(transcripts)} transcripts")
        return all_tasks
    
    def _create_project_if_needed(self, suggested_project: Dict[str, Any]) -> Tuple[Optional[int], Optional[str]]:
        """
        Create a project if it doesn't exist and is deemed necessary
        
        Args:
            suggested_project: Dict with name, description, area_node_id
            
        Returns:
            Tuple of (project_node_id, project_name) if successful, (None, None) if failed
        """
        project_name = suggested_project.get("name")
        project_description = suggested_project.get("description", "")
        area_node_id = suggested_project.get("area_node_id")
        
        if not project_name:
            return None, None
        
        self.logger.info(f"Creating new project: '{project_name}' in area node ID: {area_node_id}")
        
        try:
            # Create project in GraphRAG only
            project_node_id = self.adapter.create_project(project_name, project_description, area_node_id)
            
            if project_node_id:
                return project_node_id, project_name
            else:
                return None, None
                
        except Exception as e:
            self.logger.error(f"Error creating project '{project_name}': {e}")
            return None, None
    
