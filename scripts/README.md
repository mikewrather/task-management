# Scripts Directory

This directory contains utility scripts organized by function for the Voice Task Management system.

## 📁 Directory Structure

```
scripts/
├── analysis/               # Log and performance analysis tools
├── debug/                  # Debugging and verification utilities
├── maintenance/           # System maintenance and cleanup scripts
├── services/              # System service implementations
├── setup/                 # System setup and configuration
└── testing/               # Testing and validation scripts
```

## 🔍 Debug Scripts

Minimal debugging utilities after cleanup:

- **`verify_neo4j_connection.py`** - Test Neo4j/GraphRAG database connectivity

## 📊 Analysis Scripts

Tools for analyzing system performance and logs:

- **`analyze-voice-runs.py`** - Voice processing run statistics and analysis
- **`quick-summary.sh`** - Quick performance summary from logs

## 🛠️ Maintenance Scripts

System maintenance and cleanup utilities:

### Database Maintenance
- **`check_project_structure.py`** - Verify project follows Python best practices
- **`check_voice_tasks_in_graphrag.py`** - Verify voice tasks in GraphRAG database
- **`cleanup-processed-files.py`** - Clean up processed voice files
- **`cleanup_relationships.py`** - Clean up GraphRAG relationships
- **`establish_project_area_relationships.py`** - Create project-area relationships
- **`reprocess_voice_tasks_to_graphrag.py`** - Reprocess tasks to GraphRAG

### Duplicate Management
- **`clean-duplicates-cli.sh`** - Command-line duplicate cleanup
- **`delete-duplicate-voice-tasks.py`** - Remove duplicate voice tasks
- **`direct-delete-duplicates.py`** - Direct duplicate removal
- **`simple-delete-duplicates.py`** - Simple duplicate cleanup

### System Management
- **`automated-voice-processor.py`** - Automated voice processing service
- **`fix_test_imports.py`** - Fix test import paths
- **`notification-system.py`** - System notification management
- **`voice_logging.py`** - Voice processing logging utilities

## 🚀 Services Scripts

System service implementations:

- **`voice-processing-service.py`** - Main voice processing service daemon

## 🔧 Setup Scripts

System setup and configuration:

- **`secure-credentials.sh`** - Secure credential management
- **`setup-claude-agent.sh`** - Claude agent setup

## 🧪 Testing Scripts

Testing and validation utilities:

- **`test-voice-pipeline.py`** - Test voice processing pipeline

## 📋 Root Level Utilities

Utility scripts in the scripts root:

### Development Setup
- **`migrate-to-uv.sh`** - Migrate project to UV package manager
- **`quick-dev-setup.sh`** - Quick development environment setup

### MCP and Testing
- **`demo-mcp-inspector.sh`** - Launch MCP Inspector demo
- **`start-mcp-inspector.sh`** - Start MCP Inspector
- **`test-mcp-server.py`** - Test MCP server functionality

### Voice Processing Management
- **`setup-voice-cron.sh`** - Setup voice processing cron job
- **`voice-monitor-cron.sh`** - Voice monitoring cron script
- **`voice-status.sh`** - Check voice processing status
- **`vtm-cron-wrapper.sh`** - VTM cron wrapper script

## 🔧 Usage Examples

### Debug Database Issues
```bash
# Check GraphRAG connectivity
python scripts/debug/verify_neo4j_connection.py
```

### Analyze System Performance
```bash
# Analyze recent processing runs
python scripts/analysis/analyze-voice-runs.py

# Quick summary
bash scripts/analysis/quick-summary.sh
```

### Maintain System Health
```bash
# Verify project structure
python scripts/maintenance/check_project_structure.py

# Check voice tasks in GraphRAG
python scripts/maintenance/check_voice_tasks_in_graphrag.py

# Clean up relationships
python scripts/maintenance/cleanup_relationships.py
```

### Setup Development Environment
```bash
# Quick development setup
bash scripts/quick-dev-setup.sh

# Migrate to UV
bash scripts/migrate-to-uv.sh
```

## 🚀 Quick Reference

### Common Debugging Tasks

**Voice file not processing?**
```bash
bash scripts/voice-status.sh
python scripts/analysis/analyze-voice-runs.py
```

**Task relationships missing?**
```bash
python scripts/maintenance/establish_project_area_relationships.py
python scripts/debug/verify_neo4j_connection.py
```

**Import errors?**
```bash
python scripts/maintenance/fix_test_imports.py
```

### Performance Issues

**High error rate?**
```bash
python scripts/analysis/analyze-voice-runs.py
bash scripts/analysis/quick-summary.sh
```

### Duplicate Management

**Remove duplicates?**
```bash
python scripts/maintenance/simple-delete-duplicates.py --dry-run
bash scripts/maintenance/clean-duplicates-cli.sh
```

## 📝 Script Guidelines

When creating new scripts:

1. **Organization** - Place in appropriate subdirectory
2. **Naming** - Use descriptive names with underscore/hyphen separation
3. **Documentation** - Include docstring with purpose and usage
4. **Imports** - Use absolute imports from `voice_task_manager`
5. **Error Handling** - Include proper exception handling
6. **Logging** - Use the project's logging configuration

Example template:
```python
#!/usr/bin/env python3
"""
Script purpose and description.

Usage:
    python scripts/category/script_name.py [options]
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from voice_task_manager.utils.logging import setup_logging

logger = setup_logging()

def main():
    """Main script logic."""
    try:
        # Script implementation
        pass
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## 🔄 Current Status

### Recently Cleaned Up ✅
- ✅ Removed temporary debug scripts and import utilities
- ✅ Removed redundant duplicate cleanup scripts
- ✅ Streamlined to essential production and maintenance scripts
- ✅ Updated documentation to match actual current structure

### Current Organization ✅
- ✅ All scripts properly organized in subdirectories
- ✅ Clear separation between analysis, maintenance, and setup
- ✅ No scripts in project root (all in scripts/)
- ✅ Consistent naming and structure

---

*Updated: 2025-08-07 - Reflects current cleaned script structure after major cleanup*