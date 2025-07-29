#!/bin/bash
set -e

echo "🎬 MCP Inspector Demo for Notion Task Management Server"
echo "=" * 60

cd "$(dirname "$0")/.."

echo "📋 What you'll see in the MCP Inspector Dashboard:"
echo ""
echo "🎛️ **MCP Inspector Interface** (http://localhost:6274)"
echo "   ├── Resources Tab (view available resources)"
echo "   ├── Prompts Tab (test prompt templates)"  
echo "   └── Tools Tab ⭐ (MAIN TESTING AREA)"
echo ""
echo "🔧 **Your 9 Available Tools:**"
echo "   📊 Core List Tools:"
echo "      1. list_tasks - Test with: status='In Progress', area='Work'" 
echo "      2. list_projects - Test with: status='Active', priority='High'"
echo "      3. list_areas - Test with: status='Active'"
echo ""
echo "   🆕 New Entity Tools:"
echo "      4. list_goals - Test with: goal_type='Personal', status='Active'"
echo "      5. list_notes - Test with: note_type='Meeting', status='Published'"
echo "      6. list_events - Test with: event_type='Meeting', date_range='this-week'"
echo "      7. list_references - Test with: reference_type='Article', rating=4"
echo ""
echo "   🛠️  CRUD Operations:"
echo "      8. delete_task - Test with: task_id='test123', confirm=true"
echo ""
echo "   ℹ️  Server Info:"
echo "      9. server_info - No parameters needed"
echo ""
echo "🎯 **Testing Instructions:**"
echo "   1. Click on each tool name in the Tools tab"
echo "   2. Fill in the parameter forms with example values above"
echo "   3. Click 'Run tool' to see live results"
echo "   4. Check JSON responses for proper formatting"
echo "   5. Test error handling with invalid parameters"
echo ""
echo "🚀 **Ready to start MCP Inspector?**"
echo "   Choose your preferred method:"
echo ""
echo "   Option 1 (MCP CLI - Recommended):"
echo "   → mcp dev notion_mcp_server.py"
echo ""
echo "   Option 2 (npx - Direct):"
echo "   → npx @modelcontextprotocol/inspector .venv/bin/python notion_mcp_server.py"
echo ""
echo "   Option 3 (Our Script):"
echo "   → ./scripts/start-mcp-inspector.sh"
echo ""

read -p "Press Enter to start MCP Inspector with mcp dev (Option 1)..."

echo ""
echo "🚀 Starting MCP Inspector..."
echo "🌐 Dashboard will open at: http://localhost:6274"
echo "⚠️  Press Ctrl+C to stop"
echo ""

# Start with MCP CLI
source .venv/bin/activate
mcp dev notion_mcp_server.py