# Scripts Directory

This directory contains utility scripts organized by function for the Voice Task Management system.

## 📁 Directory Structure

```
scripts/
├── debug/                  # Debugging and verification utilities
├── analysis/              # Log and performance analysis tools
├── maintenance/           # System maintenance and cleanup scripts
└── legacy/                # Legacy scripts (to be migrated/removed)
```

## 🔍 Debug Scripts

Scripts for debugging and verifying system functionality:

### Database & Processing
- **`check_database.py`** - Verify SQLite database integrity and contents
- **`check_db_content.py`** - Detailed database content inspection
- **`check_file_tracking.py`** - Verify voice file processing status
- **`check_graphrag_db.py`** - Check Neo4j/GraphRAG database connectivity
- **`check_pending_files.py`** - List unprocessed voice files
- **`check_task_relationships.py`** - Verify task-project-area relationships

### Integration Testing
- **`test_claude_mcp.py`** - Test Claude MCP integration
- **`test_claude_subprocess.py`** - Test Claude subprocess execution
- **`test_graphrag_connection.py`** - Test GraphRAG/Neo4j connectivity
- **`test_notion_import.py`** - Verify Notion API imports
- **`test_task_adapter.py`** - Test task adapter implementations

### System Verification
- **`verify_env.py`** - Verify environment variables and configuration
- **`verify_imports.py`** - Check all package imports
- **`debug_claude_processing.py`** - Debug Claude AI processing pipeline

## 📊 Analysis Scripts

Tools for analyzing system performance and logs:

### Log Analysis
- **`analyze_logs.py`** - Comprehensive log analysis tool
- **`analyze_processing_errors.py`** - Error pattern analysis
- **`analyze_voice_runs.py`** - Voice processing run statistics

### Performance Analysis
- **`performance_test_graphrag.py`** - GraphRAG performance benchmarks
- **`analyze_adapter_performance.py`** - Adapter performance comparison

## 🛠️ Maintenance Scripts

System maintenance and cleanup utilities:

### Project Maintenance
- **`check_project_structure.py`** - Verify project follows Python best practices
- **`fix_test_imports.py`** - Fix test import paths after reorganization
- **`clean_pycache.py`** - Remove Python cache files

### Cleanup Utilities
- **`cleanup_debug_files.py`** - Remove temporary debug outputs
- **`delete_duplicate_notion_tasks.py`** - Remove duplicate Notion entries
- **`simple_delete_duplicates.py`** - Basic duplicate removal

## 🔧 Usage Examples

### Debug Database Issues
```bash
# Check database content
python scripts/debug/check_database.py

# Verify pending files
python scripts/debug/check_pending_files.py

# Check GraphRAG connectivity
python scripts/debug/check_graphrag_db.py
```

### Analyze System Performance
```bash
# Analyze recent processing runs
python scripts/analysis/analyze_voice_runs.py --recent 10

# Check for error patterns
python scripts/analysis/analyze_processing_errors.py

# Benchmark GraphRAG performance
python scripts/analysis/performance_test_graphrag.py
```

### Maintain System Health
```bash
# Verify project structure
python scripts/maintenance/check_project_structure.py

# Clean Python cache
python scripts/maintenance/clean_pycache.py

# Remove duplicate tasks
python scripts/maintenance/delete_duplicate_notion_tasks.py --dry-run
```

## 🚀 Quick Reference

### Common Debugging Tasks

**Voice file not processing?**
```bash
python scripts/debug/check_pending_files.py
python scripts/debug/check_file_tracking.py <file_id>
```

**Task relationships missing?**
```bash
python scripts/debug/check_task_relationships.py
python scripts/debug/check_graphrag_db.py
```

**Import errors?**
```bash
python scripts/debug/verify_imports.py
python scripts/maintenance/fix_test_imports.py
```

### Performance Issues

**Slow processing?**
```bash
python scripts/analysis/analyze_adapter_performance.py
python scripts/analysis/performance_test_graphrag.py
```

**High error rate?**
```bash
python scripts/analysis/analyze_processing_errors.py
python scripts/analysis/analyze_voice_runs.py --errors
```

## 📝 Script Guidelines

When creating new scripts:

1. **Organization** - Place in appropriate subdirectory
2. **Naming** - Use descriptive names with underscore separation
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

## 🔄 Migration Status

### Completed Migrations
- ✅ Moved all debug scripts to `debug/`
- ✅ Moved analysis scripts to `analysis/`
- ✅ Moved maintenance scripts to `maintenance/`
- ✅ Updated imports to use package structure

### Pending Migrations
- ⏳ Legacy shell scripts in `legacy/`
- ⏳ Consolidate duplicate functionality
- ⏳ Convert shell scripts to Python where appropriate

---

*Updated: 2025-07-31 - Reflects current organized script structure*