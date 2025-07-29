# uv Migration Guide

This document explains the migration from pip to uv package management for the Voice Task Manager project.

## What is uv?

uv is a fast Python package installer and resolver, written in Rust. It's designed as a drop-in replacement for pip that offers:

- **10-100x faster** dependency resolution and installation
- **Better dependency conflict resolution**
- **Reproducible builds** with lock files
- **Single tool** for package management

## Migration Benefits

### Performance Improvements
- Dependency installation: ~10-100x faster than pip
- Virtual environment creation: Near-instantaneous
- Lock file generation: Comprehensive dependency resolution

### Developer Experience
- **Single command setup**: `uv sync` installs everything from lock file
- **Consistent environments**: Lock file ensures reproducible builds
- **Better error messages**: Clear conflict resolution guidance
- **Modern tooling**: Built for modern Python development workflows

## Quick Migration

### Automated Migration (Recommended)
```bash
# Run the automated migration script
./scripts/migrate-to-uv.sh
```

### Manual Migration
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate environment  
source .venv/bin/activate

# Install all dependencies
uv pip install -e ".[dev,mcp]"

# Generate lock file
uv lock
```

## Project Configuration

### pyproject.toml Structure
```toml
[project]
dependencies = [
    "requests>=2.32.0",
    "openai>=1.93.0", 
    "python-dotenv>=1.1.0",
    "click>=8.1.0",
    "rich>=13.0.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0", 
    "pytest-cov", 
    "black", 
    "ruff", 
    "mypy",
    "pytest-mock"
]
mcp = [
    "mcp[cli]>=1.12.0"
]
all = [
    "voice-task-manager[dev,mcp]"
]
```

### Dependency Groups
- **Core dependencies**: Required for basic functionality
- **dev**: Development tools (testing, linting, formatting)  
- **mcp**: Model Context Protocol server dependencies
- **all**: Installs all optional dependencies

## Common Commands

### Environment Management
```bash
# Create virtual environment
uv venv

# Activate environment (same as before)
source .venv/bin/activate

# Install project in development mode
uv pip install -e .

# Install with specific dependency groups
uv pip install -e ".[dev]"          # Development dependencies
uv pip install -e ".[mcp]"          # MCP dependencies  
uv pip install -e ".[dev,mcp]"      # All dependencies
uv pip install -e ".[all]"          # All dependencies (alternative)
```

### Lock File Management
```bash
# Generate lock file (captures exact versions)
uv lock

# Install from lock file (reproducible builds)
uv sync

# Update dependencies to latest compatible versions
uv lock --upgrade
```

### Package Operations
```bash
# Add new dependency
uv add requests

# Add development dependency
uv add --dev pytest

# Remove dependency
uv remove requests

# Show dependency tree
uv pip list
```

## File Structure Changes

### New Files
- `uv.lock` - Lock file for reproducible builds (commit to version control)
- `.venv/` - Virtual environment directory (uv default, added to .gitignore)

### Modified Files
- `pyproject.toml` - Added MCP dependency group
- `.gitignore` - Added .venv/ and Python-specific patterns
- `README.md` - Updated installation instructions

### Legacy Files (can be removed after migration)
- `requirements.txt` - Replaced by pyproject.toml dependencies
- `requirements-dev.txt` - Replaced by [project.optional-dependencies.dev]
- `mcp-requirements.txt` - Replaced by [project.optional-dependencies.mcp]
- `venv/` - Old virtual environment directory

## Migration Verification

### Test the Migration
```bash
# Activate new environment
source .venv/bin/activate

# Verify installation
python -c "import voice_task_manager; print('✅ Package imported successfully')"

# Run tests
python -m pytest tests/ -v

# Test CLI commands
vtm --help
```

### Performance Comparison
```bash
# Time pip installation (legacy)
time pip install -r requirements.txt

# Time uv installation (new)
time uv pip install -e ".[dev,mcp]"
```

## CI/CD Updates

### GitHub Actions Example
```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.10'

- name: Install uv
  run: curl -LsSf https://astral.sh/uv/install.sh | sh

- name: Install dependencies
  run: |
    uv venv
    source .venv/bin/activate
    uv pip install -e ".[dev,mcp]"

- name: Run tests
  run: |
    source .venv/bin/activate
    python -m pytest
```

## Troubleshooting

### Common Issues

**uv command not found**
```bash
# Add uv to PATH
export PATH="$HOME/.cargo/bin:$PATH"
# Or restart shell after installation
```

**Lock file conflicts**
```bash
# Regenerate lock file
rm uv.lock
uv lock
```

**Dependency conflicts**
```bash
# Use uv's resolver to show conflicts
uv pip install -e ".[dev,mcp]" --verbose
```

**Import errors after migration**
```bash
# Verify environment is activated
which python
# Should show .venv/bin/python

# Reinstall package
uv pip install -e ".[dev,mcp]" --force-reinstall
```

## Rollback Plan

If migration issues occur:

1. **Restore old environment**:
   ```bash
   rm -rf .venv
   mv venv_backup venv
   source venv/bin/activate
   ```

2. **Use legacy pip commands** (README still includes pip instructions)

3. **Report issues** and use pip while troubleshooting

## Best Practices

### Development Workflow
1. **Use lock files**: Always commit `uv.lock` to version control
2. **Sync environments**: Use `uv sync` to install from lock file
3. **Update dependencies**: Use `uv lock --upgrade` periodically
4. **Test migrations**: Verify tests pass after dependency changes

### Team Adoption
1. **Gradual rollout**: Update README to show both pip and uv options
2. **Documentation**: Provide clear migration instructions  
3. **Support period**: Maintain pip compatibility during transition
4. **Training**: Share uv benefits and commands with team

## Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [uv GitHub Repository](https://github.com/astral-sh/uv)
- [Python Packaging Guide](https://packaging.python.org/)
- [pyproject.toml Specification](https://pep517.readthedocs.io/)