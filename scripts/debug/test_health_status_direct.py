#!/usr/bin/env python3
"""Direct health status from MCP server"""

import sys
import json
import asyncio
from pathlib import Path

# Add project-agents to path
agents_path = Path("/home/mike/development/project-agents/src")
sys.path.insert(0, str(agents_path))

try:
    from project_agents.core.mcp_server import AgentDBMCPServer
    
    async def get_health():
        server = AgentDBMCPServer()
        await server._initialize_components()
        health = await server._get_health_status()
        return health
    
    result = asyncio.run(get_health())
    print(json.dumps(result))
    
except Exception as e:
    print(json.dumps({
        "error": str(e),
        "type": type(e).__name__
    }))