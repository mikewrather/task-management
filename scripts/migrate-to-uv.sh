#!/bin/bash
set -e

echo "🚀 Migrating Voice Task Manager from pip to uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "✅ uv version: $(uv --version)"

# Backup current virtual environment
if [ -d "venv" ]; then
    echo "💾 Backing up current venv to venv_backup..."
    mv venv venv_backup
fi

# Create new virtual environment with uv
echo "🏗️  Creating new virtual environment with uv..."
uv venv

# Activate the new environment and install dependencies
echo "📦 Installing dependencies with uv..."
source .venv/bin/activate

# Install the project with all dependencies
uv pip install -e ".[dev,mcp]"

# Generate lock file for reproducible builds
echo "🔒 Generating uv.lock file..."
uv lock

# Run tests to verify everything works
echo "🧪 Running tests to verify migration..."
python -m pytest tests/ -v

echo "✅ Migration to uv completed successfully!"
echo ""
echo "📋 Next steps:"
echo "  • Activate environment: source .venv/bin/activate"
echo "  • Install dependencies: uv pip install -e \".[dev,mcp]\""
echo "  • Sync with lock file: uv sync"
echo "  • Add .venv/ to .gitignore if not already present"
echo "  • Commit uv.lock to version control for reproducible builds"
echo ""
echo "🗑️  To clean up:"
echo "  • Remove old venv backup: rm -rf venv_backup"
echo "  • Remove old requirements files after verifying everything works"