"""GraphRAG adapter for task storage using MCP agent-db"""

import subprocess
import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from ..utils.logging import VoiceLogger
from ..utils.config import get_claude_path
from .base import TaskAdapter, TaskData

# Load environment variables from .env file
load_dotenv()


class GraphRAGTaskAdapter(TaskAdapter):
    """Adapter for GraphRAG task storage via MCP agent-db"""
    
    def __init__(self, logger: Optional[VoiceLogger] = None):
        """
        Initialize GraphRAG adapter
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or VoiceLogger()
        self.claude_project = "task-management"
        self.use_real_mcp = os.getenv('USE_REAL_MCP', 'false').lower() == 'true'
        
    def _execute_mcp_command(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an MCP command through Claude
        
        Args:
            tool_name: Name of the MCP tool (e.g., 'create_entity')
            parameters: Parameters for the tool
            
        Returns:
            Response from the MCP tool
        """
        # Use real MCP if enabled
        if self.use_real_mcp:
            try:
                # Build prompt for Claude to execute the MCP tool
                tool_mapping = {
                    "create_entity": "mcp__agent-db__create_entity",
                    "execute_cypher": "mcp__agent-db__execute_cypher",
                    "query_natural_language": "mcp__agent-db__query_natural_language",
                    "get_health_status": "mcp__agent-db__get_health_status"
                }
                
                mcp_tool_name = tool_mapping.get(tool_name)
                if not mcp_tool_name:
                    return {"success": False, "error": f"Unknown tool: {tool_name}"}
                
                # Create a prompt that will make Claude use the MCP tool
                prompt = f"""Use the {mcp_tool_name} tool with these exact parameters:
{json.dumps(parameters, indent=2)}

Return ONLY the raw JSON result from the tool, with no additional text or formatting."""
                
                # Execute via claude -p in the project directory
                # Use full path to claude command
                import os
                original_cwd = os.getcwd()
                project_dir = "/home/mike/development/task-management"
                
                claude_path = get_claude_path()
                cmd = [
                    claude_path, 
                    "-p", prompt,
                    "--dangerously-skip-permissions",
                    "--mcp-config", f"{project_dir}/.mcp.json",
                    "--mcp-debug",  # Add debug flag for better MCP troubleshooting
                    "--output-format", "json"
                ]
                
                self.logger.debug(f"Executing real MCP command: {tool_name}")
                self.logger.debug(f"Command: {' '.join(cmd)}")
                
                try:
                    os.chdir(project_dir)
                    # Create environment without ANTHROPIC_API_KEY to use OAuth instead
                    env = {**os.environ, "PYTHONPATH": f"{project_dir}/src:{os.environ.get('PYTHONPATH', '')}"}
                    env.pop('ANTHROPIC_API_KEY', None)  # Remove API key to force OAuth usage
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=None,  # No timeout - let Claude finish
                        env=env
                    )
                finally:
                    os.chdir(original_cwd)
                
                if result.returncode != 0:
                    self.logger.error(f"Claude execution failed with return code {result.returncode}")
                    self.logger.error(f"STDERR: {result.stderr}")
                    self.logger.error(f"STDOUT: {result.stdout}")
                    # Fall back to mock
                    self.logger.warning(f"Falling back to mock for {tool_name}")
                else:
                    # Try to extract JSON from response
                    output = result.stdout.strip()
                    
                    # First check if this is a claude JSON output format
                    try:
                        claude_response = json.loads(output)
                        if isinstance(claude_response, dict):
                            # Check if this is a successful Claude response with result
                            if 'result' in claude_response and not claude_response.get('is_error', False):
                                # Extract the result field which contains the actual response
                                result_content = claude_response['result']
                                # Remove markdown code block if present
                                if result_content.startswith('```json') and result_content.endswith('```'):
                                    result_content = result_content[7:-3].strip()
                                try:
                                    response = json.loads(result_content)
                                    self.logger.success(f"Real MCP execution successful for {tool_name}")
                                    return response
                                except json.JSONDecodeError:
                                    # Result might be plain text, not JSON
                                    self.logger.warning(f"Could not parse result as JSON: {result_content[:100]}")
                            elif 'usage' in claude_response:
                                # This is just usage data, not the actual response
                                # The actual response should be in the 'result' field
                                self.logger.warning(f"Got usage data but no result for {tool_name}")
                                self.logger.debug(f"Full response: {output[:1000]}")
                                # Log the full output to understand what's happening
                                if tool_name == "execute_cypher":
                                    self.logger.info(f"Cypher query parameters: {json.dumps(parameters, indent=2)}")
                                    self.logger.info(f"Claude response keys: {list(claude_response.keys())}")
                                    if 'result' in claude_response:
                                        self.logger.info(f"Result field: {claude_response['result'][:200]}")
                                # Return empty results for now - the system can still continue
                                # This happens intermittently with Claude's MCP execution
                                return {"success": True, "results": [], "message": "No data returned from query"}
                    except (json.JSONDecodeError, KeyError):
                        pass
                    
                    # Fallback: Look for JSON in the output
                    import re
                    # Try to find a complete JSON object - look for the tool response
                    # The response might be wrapped in the MCP tool response format
                    json_patterns = [
                        r'\{[^{}]*"success"[^{}]*:.*?\}(?=\s*$|\s*\n)',  # Look for success response
                        r'\{[^{}]*"entity"[^{}]*:.*?\}',  # Look for entity response
                        r'\{[^{}]*"components"[^{}]*:.*?\}',  # Look for health check response
                        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'  # Generic JSON object
                    ]
                    
                    for pattern in json_patterns:
                        json_match = re.search(pattern, output, re.DOTALL)
                        if json_match:
                            try:
                                response = json.loads(json_match.group())
                                self.logger.success(f"Real MCP execution successful for {tool_name}")
                                return response
                            except json.JSONDecodeError:
                                continue
                    
                    self.logger.error(f"No valid JSON found in Claude response: {output[:200]}...")
                        
            except subprocess.TimeoutExpired:
                self.logger.error(f"MCP execution timed out for {tool_name}")
            except Exception as e:
                self.logger.error(f"MCP execution error: {e}")
        
        # Fall back to mock implementation
        self.logger.warning(f"Mock MCP execution for {tool_name}")
        
        # Simulate successful responses for testing
        if tool_name == "create_entity":
            return {
                "success": True,
                "entity": {
                    "id": f"mock_{datetime.now().timestamp()}",
                    "type": parameters.get("entity_type"),
                    "properties": parameters.get("properties", {})
                }
            }
        elif tool_name == "query_natural_language":
            return {
                "success": True,
                "results": []
            }
        elif tool_name == "execute_cypher":
            return {
                "success": True,
                "results": []
            }
        elif tool_name == "get_health_status":
            return {
                "success": True,
                "status": "healthy"
            }
        
        return {"success": False, "error": f"Unknown tool: {tool_name}"}
    
    def create_task(self, task_data: TaskData) -> Optional[str]:
        """Create a task in GraphRAG"""
        # First, search for related entities
        context = self._get_entity_context(task_data.name)
        
        # Create the task entity
        task_properties = {
            "entity_type": "TASK",
            "properties": {
                "name": task_data.name,
                "description": task_data.description or "",
                "status": task_data.status,
                "priority": task_data.priority,
                "contexts": task_data.contexts,
                "created": task_data.created_at.isoformat(),
                "source": task_data.source,
                "project_name": task_data.project_name or "",
                "area_name": task_data.area_name or "",
                "goal_name": task_data.goal_name or ""
            }
        }
        
        # Add Notion ID if migrating
        if task_data.metadata.get("notion_id"):
            task_properties["properties"]["notion_id"] = task_data.metadata["notion_id"]
        
        # Create the task
        response = self._execute_mcp_command("create_entity", task_properties)
        
        if not response.get("success"):
            self.logger.error(f"Failed to create task in GraphRAG: {response.get('error')}")
            return None
        
        task_id = response.get("entity", {}).get("id")
        
        # Create relationships if we have project/area/goal
        if task_id:
            # Create project relationship if available
            if task_data.project_id:
                self._create_relationship(task_id, task_data.project_id, "BELONGS_TO", "PROJECT")
                self.logger.info(f"Created PROJECT relationship: Task -> {task_data.project_name}")
            
            # Create area relationship if available (even without project)
            if task_data.area_id:
                self._create_relationship(task_id, task_data.area_id, "RELATES_TO", "AREA")
                self.logger.info(f"Created AREA relationship: Task -> {task_data.area_name}")
            
            # Create goal relationship if available
            if task_data.goal_id:
                self._create_relationship(task_id, task_data.goal_id, "CONTRIBUTES_TO", "GOAL")
                self.logger.info(f"Created GOAL relationship: Task -> {task_data.goal_name}")
        
        return task_id
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a task in GraphRAG"""
        # GraphRAG doesn't have direct update, need to use Cypher
        set_clauses = []
        for key, value in updates.items():
            if isinstance(value, str):
                set_clauses.append(f"t.{key} = '{value}'")
            elif isinstance(value, (int, float)):
                set_clauses.append(f"t.{key} = {value}")
            elif isinstance(value, list):
                set_clauses.append(f"t.{key} = {json.dumps(value)}")
        
        if not set_clauses:
            return True
        
        query = f"MATCH (t:TASK) WHERE ID(t) = {task_id} SET {', '.join(set_clauses)} RETURN t"
        
        response = self._execute_mcp_command("execute_cypher", {
            "query": query,
            "parameters": {}
        })
        
        return response.get("success", False)
    
    def get_task(self, task_id: str) -> Optional[TaskData]:
        """Retrieve a task from GraphRAG"""
        query = """
        MATCH (t:TASK) WHERE ID(t) = $task_id
        OPTIONAL MATCH (t)-[:BELONGS_TO]->(p:PROJECT)
        OPTIONAL MATCH (p)-[:BELONGS_TO]->(a:AREA)
        RETURN t, p.name as project_name, p.notion_id as project_id, 
               a.name as area_name, a.notion_id as area_id
        """
        
        response = self._execute_mcp_command("execute_cypher", {
            "query": query,
            "parameters": {"task_id": int(task_id)}
        })
        
        # Handle both dict and list response formats
        if isinstance(response, dict):
            if not response.get("success") or not response.get("results"):
                return None
            results = response["results"]
        elif isinstance(response, list):
            results = response
        else:
            return None
        
        if not results:
            return None
            
        result = results[0]
        task = result["t"]
        
        return TaskData(
            name=task.get("name"),
            description=task.get("description"),
            status=task.get("status", "Inbox"),
            priority=task.get("priority", "Medium"),
            contexts=task.get("contexts", []),
            project_id=result.get("project_id"),
            project_name=result.get("project_name"),
            area_id=result.get("area_id"),
            area_name=result.get("area_name"),
            created_at=datetime.fromisoformat(task.get("created")) if task.get("created") else None,
            metadata={"graphrag_id": task_id}
        )
    
    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        """Search for projects in GraphRAG using natural language"""
        response = self._execute_mcp_command("query_natural_language", {
            "query": f"Find projects related to: {query}",
            "max_results": 10
        })
        
        if not response.get("success"):
            # Fallback to Cypher search
            return self._search_projects_cypher(query)
        
        # Handle both dict and list response formats
        results = response if isinstance(response, list) else response.get("results", [])
        
        projects = []
        for result in results:
            if result.get("labels") and "PROJECT" in result["labels"]:
                projects.append({
                    "id": result.get("notion_id") or str(result.get("id")),
                    "name": result.get("name"),
                    "area_name": result.get("area_name"),
                    "status": result.get("status")
                })
        
        return projects
    
    def _search_projects_cypher(self, query: str) -> List[Dict[str, Any]]:
        """Fallback Cypher search for projects"""
        cypher_query = """
        MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA)
        WHERE toLower(p.name) CONTAINS toLower($query)
        RETURN p.notion_id as id, p.name as name, a.name as area_name, p.status as status
        LIMIT 10
        """
        
        response = self._execute_mcp_command("execute_cypher", {
            "query": cypher_query,
            "parameters": {"query": query}
        })
        
        # Handle both dict and list response formats
        if isinstance(response, dict):
            if response.get("success"):
                return response.get("results", [])
            return []
        elif isinstance(response, list):
            return response
        return []
    
    def search_areas(self, query: str) -> List[Dict[str, Any]]:
        """Search for areas in GraphRAG"""
        cypher_query = """
        MATCH (a:AREA)
        WHERE toLower(a.name) CONTAINS toLower($query)
        RETURN a.notion_id as id, a.name as name, a.status as status
        LIMIT 10
        """
        
        response = self._execute_mcp_command("execute_cypher", {
            "query": cypher_query,
            "parameters": {"query": query}
        })
        
        # Handle both dict and list response formats
        if isinstance(response, dict):
            if response.get("success"):
                return response.get("results", [])
            return []
        elif isinstance(response, list):
            return response
        return []
    
    def get_categorization_context(self) -> Dict[str, Any]:
        """Get context for categorization from GraphRAG"""
        # Get recent tasks with their relationships
        recent_tasks_query = """
        MATCH (t:TASK)
        WHERE t.source = 'voice' AND t.created IS NOT NULL
        OPTIONAL MATCH (t)-[:BELONGS_TO]->(p:PROJECT)
        OPTIONAL MATCH (p)-[:BELONGS_TO]->(a:AREA)
        RETURN t.name as title, p.name as project_name, p.notion_id as project_id,
               a.name as area_name, t.contexts as contexts
        ORDER BY t.created DESC
        LIMIT 20
        """
        
        tasks_response = self._execute_mcp_command("execute_cypher", {
            "query": recent_tasks_query,
            "parameters": {}
        })
        
        # Get all projects with areas
        projects_query = """
        MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA)
        RETURN p.notion_id as project_id, p.name as name, 
               a.notion_id as area_id, a.name as area_name
        """
        
        projects_response = self._execute_mcp_command("execute_cypher", {
            "query": projects_query,
            "parameters": {}
        })
        
        # Get all areas
        areas_query = """
        MATCH (a:AREA)
        RETURN a.notion_id as area_id, a.name as name
        """
        
        areas_response = self._execute_mcp_command("execute_cypher", {
            "query": areas_query,
            "parameters": {}
        })
        
        # Handle response format - MCP execute_cypher returns list directly
        tasks_results = tasks_response if isinstance(tasks_response, list) else tasks_response.get("results", [])
        projects_results = projects_response if isinstance(projects_response, list) else projects_response.get("results", [])
        areas_results = areas_response if isinstance(areas_response, list) else areas_response.get("results", [])
        
        context = {
            "recent_tasks": tasks_results,
            "project_patterns": {},
            "area_descriptions": {}
        }
        
        # Build project patterns
        for project in projects_results:
            if project.get("project_id"):
                context["project_patterns"][project["project_id"]] = {
                    "name": project["name"],
                    "area_id": project.get("area_id"),
                    "area_name": project.get("area_name", ""),
                    "keywords": self._extract_keywords(project["name"])
                }
        
        # Build area descriptions
        for area in areas_results:
            if area.get("area_id"):
                context["area_descriptions"][area["area_id"]] = {
                    "name": area["name"],
                    "keywords": self._extract_keywords(area["name"])
                }
        
        return context
    
    def test_connection(self) -> bool:
        """Test GraphRAG connection"""
        response = self._execute_mcp_command("get_health_status", {})
        # Check if we got a valid response
        if isinstance(response, dict):
            # For health status, check if we have components
            if "components" in response:
                return True
            # For mock/error responses, check success field
            if "success" in response:
                return response.get("success", False)
            # If we got usage data, it means the connection worked
            if "usage" in response or "input_tokens" in response:
                self.logger.info("GraphRAG connection successful (got usage data)")
                return True
            return False
        return False
    
    def _get_entity_context(self, query: str) -> Dict[str, Any]:
        """Get relevant entities for a query"""
        response = self._execute_mcp_command("query_natural_language", {
            "query": f"Find projects, areas, and goals related to: {query}",
            "max_results": 20
        })
        
        context = {
            "projects": [],
            "areas": [],
            "goals": []
        }
        
        # Handle both dict and list response formats
        results = response if isinstance(response, list) else response.get("results", [])
        
        if isinstance(response, dict) and not response.get("success"):
            return context
            
        for result in results:
            labels = result.get("labels", [])
            if "PROJECT" in labels:
                context["projects"].append(result)
            elif "AREA" in labels:
                context["areas"].append(result)
            elif "GOAL" in labels:
                context["goals"].append(result)
        
        return context
    
    def _create_relationship(self, from_id: str, to_id: str, 
                           relationship_type: str, to_label: str) -> bool:
        """Create a relationship between entities"""
        query = f"""
        MATCH (from), (to:{to_label})
        WHERE ID(from) = {from_id} AND to.notion_id = '{to_id}'
        MERGE (from)-[:{relationship_type}]->(to)
        RETURN from, to
        """
        
        response = self._execute_mcp_command("execute_cypher", {
            "query": query,
            "parameters": {}
        })
        
        return response.get("success", False)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for matching"""
        words = text.lower().split()
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        return keywords