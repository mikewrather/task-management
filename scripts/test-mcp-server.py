#!/home/mike/development/task-management/.venv/bin/python
"""
Test script for the enhanced MCP server functionality
"""

import asyncio
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, '.')

async def test_mcp_server():
    """Test the MCP server functionality"""
    print("🧪 Testing Enhanced MCP Server")
    print("=" * 50)
    
    try:
        # Import the MCP server
        from notion_mcp_server import mcp, server_info
        
        print("✅ MCP server imported successfully")
        print(f"📊 Server name: {mcp.name}")
        
        # Test server info function
        print("\n🔍 Testing server_info function...")
        info_result = await server_info()
        
        if info_result.get('success'):
            tools = info_result['data']['available_tools']
            print(f"✅ Server info retrieved successfully")
            print(f"🔧 Total tools available: {len(tools)}")
            
            print("\n📋 Available Tools:")
            for i, tool in enumerate(tools, 1):
                print(f"  {i:2d}. {tool['name']} - {tool['description']}")
            
            # Show new entity tools
            new_tools = [t for t in tools if t['name'] in ['list_goals', 'list_notes', 'list_events', 'list_references']]
            print(f"\n🆕 New entity tools added: {len(new_tools)}")
            for tool in new_tools:
                print(f"   • {tool['name']}")
            
            # Show CRUD tools
            crud_tools = [t for t in tools if 'delete' in t['name'] or 'create' in t['name'] or 'update' in t['name']]
            print(f"\n🛠️  CRUD operation tools: {len(crud_tools)}")
            for tool in crud_tools:
                print(f"   • {tool['name']}")
            
        else:
            print(f"❌ Server info failed: {info_result.get('error', {}).get('message', 'Unknown error')}")
        
        print(f"\n✅ MCP Server Test Complete")
        print(f"📍 Server path: {os.path.abspath('notion_mcp_server.py')}")
        print(f"🐍 Python environment: {sys.executable}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)