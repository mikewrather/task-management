#!/bin/bash
set -e

echo "🚀 Quick Development Setup for Voice Task Manager"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "✅ Using uv version: $(uv --version)"

# Create and activate environment
echo "🏗️   Setting up development environment..."
uv venv
source .venv/bin/activate

# Install all dependencies (dev, mcp, and main)
echo "📦 Installing all dependencies..."
uv pip install -e ".[dev,mcp]"

# Copy environment template
if [ ! -f .env ]; then
    echo "⚙️  Setting up environment configuration..."
    cp .env.example .env
    echo "📝 Please edit .env with your API keys and database IDs"
fi

# Verify installation
echo "🧪 Verifying installation..."
python -c "import voice_task_manager; print('✅ Package imported successfully')"
vtm --help > /dev/null && echo "✅ CLI commands working"

echo ""
echo "🎉 Development environment ready!"
echo ""
echo "📋 Next steps:"
echo "  • Activate environment: source .venv/bin/activate"
echo "  • Edit .env with your API keys"
echo "  • Run tests: python -m pytest tests/"
echo "  • Try CLI: vtm --help"
echo ""
echo "💡 Pro tips:"
echo "  • Use 'uv sync' to install from lock file"
echo "  • Use 'uv lock --upgrade' to update dependencies"
echo "  • Use 'uv add <package>' to add new dependencies"