"""GraphRAG adapter for task storage using MCP agent-db"""

import subprocess
import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..utils.logging import VoiceLogger
from .base import TaskAdapter, TaskData


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
        
    def _execute_mcp_command(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an MCP command through Claude
        
        Args:
            tool_name: Name of the MCP tool (e.g., 'create_entity')
            parameters: Parameters for the tool
            
        Returns:
            Response from the MCP tool
        """
        # For now, we'll create a simple mock implementation
        # In production, this would use the actual MCP client
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
                "source": task_data.source
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
        if task_data.project_id and task_id:
            self._create_relationship(task_id, task_data.project_id, "BELONGS_TO", "PROJECT")
        
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
        
        if not response.get("success") or not response.get("results"):
            return None
        
        result = response["results"][0]
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
        
        projects = []
        for result in response.get("results", []):
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
        
        if response.get("success"):
            return response.get("results", [])
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
        
        if response.get("success"):
            return response.get("results", [])
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
        
        context = {
            "recent_tasks": tasks_response.get("results", []),
            "project_patterns": {},
            "area_descriptions": {}
        }
        
        # Build project patterns
        for project in projects_response.get("results", []):
            context["project_patterns"][project["project_id"]] = {
                "name": project["name"],
                "area_id": project["area_id"],
                "area_name": project["area_name"],
                "keywords": self._extract_keywords(project["name"])
            }
        
        # Build area descriptions
        for area in areas_response.get("results", []):
            context["area_descriptions"][area["area_id"]] = {
                "name": area["name"],
                "keywords": self._extract_keywords(area["name"])
            }
        
        return context
    
    def test_connection(self) -> bool:
        """Test GraphRAG connection"""
        response = self._execute_mcp_command("get_health_status", {})
        return response.get("success", False)
    
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
        
        if response.get("success"):
            for result in response.get("results", []):
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