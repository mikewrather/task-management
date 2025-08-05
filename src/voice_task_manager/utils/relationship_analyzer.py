"""
Relationship Analyzer for Voice Task Management System

This module provides utilities for analyzing and cleaning up relationships between tasks,
projects, areas, and goals in the GraphRAG storage system.

Features:
- Duplicate task detection using fuzzy matching
- Orphaned task identification (tasks without proper relationships)
- Relationship inference based on task content and context
- Semantic similarity analysis using embeddings

Usage:
    from voice_task_manager.utils.relationship_analyzer import RelationshipAnalyzer
    
    analyzer = RelationshipAnalyzer()
    orphans = analyzer.find_orphaned_tasks()
    duplicates = analyzer.find_duplicate_tasks()
    analyzer.suggest_relationships(orphan_tasks)
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import difflib
import re

from ..utils.logging import VoiceLogger


@dataclass
class TaskRelationship:
    """Represents a task and its relationships"""
    task_id: str
    task_name: str
    description: str
    current_project_id: Optional[str] = None
    current_project_name: Optional[str] = None
    current_area_id: Optional[str] = None
    current_area_name: Optional[str] = None
    current_goal_id: Optional[str] = None
    current_goal_name: Optional[str] = None
    suggested_project_id: Optional[str] = None
    suggested_project_name: Optional[str] = None
    suggested_area_id: Optional[str] = None
    suggested_area_name: Optional[str] = None
    confidence: float = 0.0
    reasoning: str = ""


@dataclass
class DuplicateTaskPair:
    """Represents a pair of potentially duplicate tasks"""
    task1_id: str
    task1_name: str
    task2_id: str
    task2_name: str
    similarity_score: float
    similarity_type: str  # "exact", "fuzzy", "semantic"
    recommendation: str  # "merge", "keep_both", "review"


class RelationshipAnalyzer:
    """Analyzes and suggests improvements for task relationships"""
    
    def __init__(self, logger: Optional[VoiceLogger] = None):
        """
        Initialize the relationship analyzer
        
        Args:
            logger: Logger instance for tracking operations
        """
        self.logger = logger or VoiceLogger()
        self.graphrag_adapter = None
        self.notion_adapter = None
        
        # Initialize adapters if available
        try:
            from ..adapters.graphrag import GraphRAGTaskAdapter
            self.graphrag_adapter = GraphRAGTaskAdapter(logger=self.logger)
        except Exception as e:
            self.logger.warning(f"GraphRAG adapter not available: {e}")
        
        try:
            # Notion adapter removed - using pure GraphRAG now
            self.notion_adapter = None
        except Exception as e:
            self.logger.warning(f"Notion adapter not available: {e}")
    
    def find_orphaned_tasks(self, min_confidence: float = 0.7) -> List[TaskRelationship]:
        """
        Find tasks that lack proper relationships to projects, areas, or goals
        
        Args:
            min_confidence: Minimum confidence threshold for relationship suggestions
            
        Returns:
            List of TaskRelationship objects for orphaned tasks
        """
        self.logger.info("Starting orphaned task analysis...")
        orphaned_tasks = []
        
        # Get all tasks from available adapters
        all_tasks = self._get_all_tasks()
        
        for task in all_tasks:
            # Check if task is orphaned (missing key relationships)
            is_orphaned = (
                not task.get("project_id") or 
                not task.get("area_id")
            )
            
            if is_orphaned:
                # Analyze task for relationship suggestions
                relationship = self._analyze_task_relationships(task, min_confidence)
                if relationship:
                    orphaned_tasks.append(relationship)
        
        self.logger.info(f"Found {len(orphaned_tasks)} orphaned tasks")
        return orphaned_tasks
    
    def find_duplicate_tasks(self, similarity_threshold: float = 0.8) -> List[DuplicateTaskPair]:
        """
        Find potentially duplicate tasks using various similarity metrics
        
        Args:
            similarity_threshold: Minimum similarity score to consider as duplicate
            
        Returns:
            List of DuplicateTaskPair objects
        """
        self.logger.info("Starting duplicate task analysis...")
        duplicates = []
        
        # Get all tasks
        all_tasks = self._get_all_tasks()
        
        # Compare each task with every other task
        for i, task1 in enumerate(all_tasks):
            for j, task2 in enumerate(all_tasks[i+1:], i+1):
                similarity = self._calculate_task_similarity(task1, task2)
                
                if similarity["score"] >= similarity_threshold:
                    duplicate_pair = DuplicateTaskPair(
                        task1_id=task1.get("id", ""),
                        task1_name=task1.get("name", ""),
                        task2_id=task2.get("id", ""),
                        task2_name=task2.get("name", ""),
                        similarity_score=similarity["score"],
                        similarity_type=similarity["type"],
                        recommendation=self._get_duplicate_recommendation(similarity["score"])
                    )
                    duplicates.append(duplicate_pair)
        
        self.logger.info(f"Found {len(duplicates)} potential duplicate pairs")
        return duplicates
    
    def suggest_relationships(self, tasks: List[Dict[str, Any]]) -> List[TaskRelationship]:
        """
        Suggest relationships for a list of tasks
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            List of TaskRelationship objects with suggestions
        """
        suggestions = []
        
        for task in tasks:
            relationship = self._analyze_task_relationships(task)
            if relationship:
                suggestions.append(relationship)
        
        return suggestions
    
    def _get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks from available adapters"""
        all_tasks = []
        
        # Get tasks from GraphRAG
        if self.graphrag_adapter:
            try:
                graphrag_tasks = self._get_graphrag_tasks()
                all_tasks.extend(graphrag_tasks)
            except Exception as e:
                self.logger.error(f"Error getting GraphRAG tasks: {e}")
        
        # Get tasks from Notion (if needed)
        if self.notion_adapter:
            try:
                notion_tasks = self._get_notion_tasks()
                all_tasks.extend(notion_tasks)
            except Exception as e:
                self.logger.error(f"Error getting Notion tasks: {e}")
        
        return all_tasks
    
    def _get_graphrag_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks from GraphRAG"""
        if not self.graphrag_adapter:
            return []
        
        query = """
        MATCH (t:TASK)
        OPTIONAL MATCH (t)-[:BELONGS_TO]->(p:PROJECT)
        OPTIONAL MATCH (t)-[:BELONGS_TO]->(a:AREA)
        OPTIONAL MATCH (t)-[:CONTRIBUTES_TO]->(g:GOAL)
        RETURN t, p, a, g
        """
        
        response = self.graphrag_adapter._execute_mcp_command("execute_cypher", {
            "query": query,
            "parameters": {}
        })
        
        tasks = []
        if response and response.get("success"):
            for record in response.get("results", []):
                task_data = record.get("t", {})
                project_data = record.get("p", {})
                area_data = record.get("a", {})
                goal_data = record.get("g", {})
                
                task = {
                    "id": str(task_data.get("notion_id", task_data.get("id", ""))),
                    "name": task_data.get("name", ""),
                    "description": task_data.get("description", ""),
                    "project_id": project_data.get("notion_id") if project_data else None,
                    "project_name": project_data.get("name") if project_data else None,
                    "area_id": area_data.get("notion_id") if area_data else None,
                    "area_name": area_data.get("name") if area_data else None,
                    "goal_id": goal_data.get("notion_id") if goal_data else None,
                    "goal_name": goal_data.get("name") if goal_data else None,
                    "source": "graphrag"
                }
                tasks.append(task)
        
        return tasks
    
    def _get_notion_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks from Notion (placeholder for future implementation)"""
        return []  # TODO: Implement when Notion querying is available
    
    def _analyze_task_relationships(self, task: Dict[str, Any], min_confidence: float = 0.5) -> Optional[TaskRelationship]:
        """
        Analyze a task and suggest relationships
        
        Args:
            task: Task dictionary
            min_confidence: Minimum confidence for suggestions
            
        Returns:
            TaskRelationship object with suggestions or None
        """
        task_name = task.get("name", "")
        task_description = task.get("description", "")
        task_content = f"{task_name} {task_description}".lower()
        
        # Extract keywords for matching
        keywords = self._extract_keywords(task_content)
        
        # Search for related projects and areas
        suggested_project = self._find_best_project_match(keywords, task_content)
        suggested_area = self._find_best_area_match(keywords, task_content)
        
        # Calculate confidence based on keyword matches and context
        confidence = self._calculate_relationship_confidence(
            task_content, suggested_project, suggested_area
        )
        
        if confidence >= min_confidence:
            return TaskRelationship(
                task_id=task.get("id", ""),
                task_name=task_name,
                description=task_description,
                current_project_id=task.get("project_id"),
                current_project_name=task.get("project_name"),
                current_area_id=task.get("area_id"),
                current_area_name=task.get("area_name"),
                current_goal_id=task.get("goal_id"),
                current_goal_name=task.get("goal_name"),
                suggested_project_id=suggested_project.get("id") if suggested_project else None,
                suggested_project_name=suggested_project.get("name") if suggested_project else None,
                suggested_area_id=suggested_area.get("id") if suggested_area else None,
                suggested_area_name=suggested_area.get("name") if suggested_area else None,
                confidence=confidence,
                reasoning=self._generate_relationship_reasoning(task_content, suggested_project, suggested_area)
            )
        
        return None
    
    def _find_best_project_match(self, keywords: List[str], task_content: str) -> Optional[Dict[str, Any]]:
        """Find the best matching project for a task"""
        if not self.graphrag_adapter:
            return None
        
        # Search for projects using natural language query
        search_query = " ".join(keywords[:5])  # Use top 5 keywords
        
        response = self.graphrag_adapter._execute_mcp_command("query_natural_language", {
            "query": f"Find projects related to: {search_query}",
            "max_results": 10
        })
        
        if not response or not isinstance(response, list):
            return None
        
        best_match = None
        best_score = 0.0
        
        for result in response:
            if "PROJECT" in result.get("labels", []):
                project_name = result.get("name", "").lower()
                project_description = result.get("description", "").lower()
                
                # Calculate similarity based on keyword overlap and semantic similarity
                score = self._calculate_semantic_similarity(
                    task_content, 
                    f"{project_name} {project_description}"
                )
                
                if score > best_score:
                    best_score = score
                    best_match = {
                        "id": result.get("notion_id", result.get("id")),
                        "name": result.get("name"),
                        "description": result.get("description", ""),
                        "score": score
                    }
        
        return best_match if best_score > 0.3 else None
    
    def _find_best_area_match(self, keywords: List[str], task_content: str) -> Optional[Dict[str, Any]]:
        """Find the best matching area for a task"""
        if not self.graphrag_adapter:
            return None
        
        # Search for areas using natural language query
        search_query = " ".join(keywords[:5])
        
        response = self.graphrag_adapter._execute_mcp_command("query_natural_language", {
            "query": f"Find areas related to: {search_query}",
            "max_results": 10
        })
        
        if not response or not isinstance(response, list):
            return None
        
        best_match = None
        best_score = 0.0
        
        for result in response:
            if "AREA" in result.get("labels", []):
                area_name = result.get("name", "").lower()
                
                # Calculate similarity
                score = self._calculate_semantic_similarity(task_content, area_name)
                
                if score > best_score:
                    best_score = score
                    best_match = {
                        "id": result.get("notion_id", result.get("id")),
                        "name": result.get("name"),
                        "score": score
                    }
        
        return best_match if best_score > 0.2 else None
    
    def _calculate_task_similarity(self, task1: Dict[str, Any], task2: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate similarity between two tasks"""
        name1 = task1.get("name", "").lower()
        name2 = task2.get("name", "").lower()
        desc1 = task1.get("description", "").lower()
        desc2 = task2.get("description", "").lower()
        
        # Exact match
        if name1 == name2:
            return {"score": 1.0, "type": "exact"}
        
        # Fuzzy string matching
        name_similarity = difflib.SequenceMatcher(None, name1, name2).ratio()
        desc_similarity = difflib.SequenceMatcher(None, desc1, desc2).ratio()
        
        # Combined similarity
        combined_score = (name_similarity * 0.7 + desc_similarity * 0.3)
        
        if combined_score >= 0.9:
            return {"score": combined_score, "type": "fuzzy"}
        
        # Semantic similarity (simplified - could use embeddings)
        semantic_score = self._calculate_semantic_similarity(
            f"{name1} {desc1}", 
            f"{name2} {desc2}"
        )
        
        return {"score": semantic_score, "type": "semantic"}
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts (simplified implementation)"""
        # Simple keyword-based similarity (could be enhanced with embeddings)
        words1 = set(self._extract_keywords(text1))
        words2 = set(self._extract_keywords(text2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Simple keyword extraction (could be enhanced with NLP)
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'this', 'that', 'these', 'those', 'need', 'make', 'sure', 'get', 'set', 'up'
        }
        
        # Clean and tokenize
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Filter stopwords and short words
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        
        return keywords
    
    def _calculate_relationship_confidence(self, task_content: str, suggested_project: Optional[Dict], suggested_area: Optional[Dict]) -> float:
        """Calculate confidence score for relationship suggestions"""
        confidence = 0.0
        
        if suggested_project:
            confidence += suggested_project.get("score", 0.0) * 0.6
        
        if suggested_area:
            confidence += suggested_area.get("score", 0.0) * 0.4
        
        return min(confidence, 1.0)
    
    def _generate_relationship_reasoning(self, task_content: str, suggested_project: Optional[Dict], suggested_area: Optional[Dict]) -> str:
        """Generate human-readable reasoning for relationship suggestions"""
        reasons = []
        
        if suggested_project:
            reasons.append(f"Project '{suggested_project['name']}' matches with {suggested_project.get('score', 0):.2f} confidence")
        
        if suggested_area:
            reasons.append(f"Area '{suggested_area['name']}' matches with {suggested_area.get('score', 0):.2f} confidence")
        
        if not reasons:
            reasons.append("No strong relationships found")
        
        return "; ".join(reasons)
    
    def _get_duplicate_recommendation(self, similarity_score: float) -> str:
        """Get recommendation for handling duplicate tasks"""
        if similarity_score >= 0.95:
            return "merge"
        elif similarity_score >= 0.8:
            return "review"
        else:
            return "keep_both"