#!/usr/bin/env python3
"""Direct test of agent-db health status"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project-agents to path
agents_path = Path("/home/mike/development/project-agents/src")
sys.path.insert(0, str(agents_path))

# Mock environment variables if needed
os.environ.setdefault('NEO4J_URI', 'bolt://localhost:7687')
os.environ.setdefault('NEO4J_USER', 'neo4j')
os.environ.setdefault('NEO4J_PASSWORD', 'agent-db-password')
os.environ.setdefault('HF_MODEL', 'BAAI/bge-m3')

async def test_health():
    try:
        from project_agents.core.mcp_server import AgentDBMCPServer
        
        # Create server instance
        server = AgentDBMCPServer()
        
        # Initialize components
        await server.initialize()
        
        # Get health status
        health = await server._get_health_status()
        
        # Print only the JSON result
        print(json.dumps(health, indent=2))
        
    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "type": type(e).__name__,
            "mcp_server": False
        }, indent=2))

if __name__ == "__main__":
    asyncio.run(test_health())