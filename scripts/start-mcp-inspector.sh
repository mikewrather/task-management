#!/bin/bash
set -e

echo "🎛️ Starting MCP Inspector for Notion Task Management Server"
echo "=" * 60

# Ensure we're in the project directory
cd "$(dirname "$0")/.."

# Check if our MCP server file exists
if [ ! -f "notion_mcp_server.py" ]; then
    echo "❌ notion_mcp_server.py not found in $(pwd)"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ .venv directory not found. Run migration script first."
    exit 1
fi

echo "✅ Project directory: $(pwd)"
echo "✅ MCP server file: $(ls -la notion_mcp_server.py | awk '{print $5 " bytes"}')"
echo "✅ Python environment: $(realpath .venv/bin/python)"

# Test our MCP server quickly
echo ""
echo "🧪 Testing MCP server functionality..."
source .venv/bin/activate
python scripts/test-mcp-server.py
if [ $? -ne 0 ]; then
    echo "❌ MCP server test failed. Fix server issues before starting inspector."
    exit 1
fi

echo ""
echo "🚀 Starting MCP Inspector..."
echo "📍 Server path: $(realpath notion_mcp_server.py)"
echo "🌐 Inspector will open at: http://localhost:6274"
echo "🔗 Proxy server at: http://localhost:6277"
echo ""
echo "💡 In the Inspector dashboard:"
echo "   • Test all 9 MCP tools interactively"
echo "   • View real-time server responses"
echo "   • Debug tool parameters and responses"
echo "   • Export client configurations"
echo ""
echo "⚠️  Press Ctrl+C to stop the inspector"
echo ""

# Run MCP Inspector with our server
# Using npx to run the official inspector
npx @modelcontextprotocol/inspector "$(realpath .venv/bin/python)" "$(realpath notion_mcp_server.py)"