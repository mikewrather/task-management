# Scripts Directory

Essential utility scripts for the Voice Task Management system, streamlined after removing Notion dependencies.

## 📁 Directory Structure

```
scripts/
├── analysis/               # System analysis and monitoring
├── debug/                  # Essential debugging utilities  
├── maintenance/           # Database and system maintenance
├── services/              # Core system services
└── setup/                 # System configuration
```

## 🔍 Debug Scripts

Essential debugging utilities:

- **`verify_neo4j_connection.py`** - Test Neo4j/GraphRAG database connectivity

## 📊 Analysis Scripts

Performance monitoring and log analysis:

- **`analyze-voice-runs.py`** - Voice processing statistics and performance analysis
- **`quick-summary.sh`** - Quick performance summary from logs

## 🛠️ Maintenance Scripts

Database and system maintenance utilities:

### Database Operations
- **`check_project_structure.py`** - Verify project follows Python best practices
- **`check_voice_tasks_in_graphrag.py`** - Verify voice tasks in GraphRAG database
- **`cleanup-processed-files.py`** - Clean up processed voice files
- **`cleanup_relationships.py`** - Clean up GraphRAG relationships and duplicates
- **`establish_project_area_relationships.py`** - Create project-area relationships in GraphRAG
- **`reprocess_voice_tasks_to_graphrag.py`** - Reprocess existing tasks to GraphRAG

### System Utilities
- **`fix_test_imports.py`** - Fix test import paths after refactoring
- **`notification-system.py`** - System notification management
- **`voice_logging.py`** - Voice processing logging utilities

## 🚀 Services Scripts

Core system service:

- **`voice-processing-service.py`** - Main voice processing daemon service

## 🔧 Setup Scripts

System configuration and setup:

- **`secure-credentials.sh`** - Secure credential management setup
- **`setup-claude-agent.sh`** - Claude agent configuration

## 📋 System Management Scripts

Voice processing system management:

- **`quick-dev-setup.sh`** - Quick development environment setup
- **`setup-voice-cron.sh`** - Setup voice processing cron job  
- **`voice-monitor-cron.sh`** - Voice processing monitoring via cron
- **`voice-status.sh`** - System status dashboard
- **`vtm-cron-wrapper.sh`** - Voice Task Manager cron wrapper

## 🔧 Usage Examples

### Debug Database Issues
```bash
# Check GraphRAG connectivity
python scripts/debug/verify_neo4j_connection.py
```

### Monitor System Performance  
```bash
# Analyze recent processing runs
python scripts/analysis/analyze-voice-runs.py

# Quick performance summary
bash scripts/analysis/quick-summary.sh

# Check system status
bash scripts/voice-status.sh
```

### Maintain Database Health
```bash
# Verify project structure
python scripts/maintenance/check_project_structure.py

# Check voice tasks in GraphRAG
python scripts/maintenance/check_voice_tasks_in_graphrag.py

# Clean up relationships
python scripts/maintenance/cleanup_relationships.py

# Establish missing relationships
python scripts/maintenance/establish_project_area_relationships.py
```

### Setup Development Environment
```bash
# Quick development setup
bash scripts/quick-dev-setup.sh

# Setup credentials securely  
bash scripts/setup/secure-credentials.sh
```

## 🚀 Quick Reference

### Common Issues

**Voice files not processing?**
```bash
bash scripts/voice-status.sh
python scripts/analysis/analyze-voice-runs.py
```

**GraphRAG relationships missing?**
```bash
python scripts/maintenance/establish_project_area_relationships.py
python scripts/debug/verify_neo4j_connection.py
```

**System performance issues?**
```bash
python scripts/analysis/analyze-voice-runs.py
bash scripts/analysis/quick-summary.sh
```

**Import/structure errors?**
```bash
python scripts/maintenance/fix_test_imports.py
python scripts/maintenance/check_project_structure.py
```

## 📝 Script Guidelines

Essential practices for new scripts:

1. **Organization** - Place in appropriate subdirectory based on function
2. **GraphRAG Focus** - Use only GraphRAG/Neo4j, no Notion dependencies  
3. **Documentation** - Include clear docstring with purpose and usage
4. **Error Handling** - Include proper exception handling and logging
5. **Package Imports** - Use absolute imports from `voice_task_manager`

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
        logger.info("Script completed successfully")
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## 🧹 Recent Cleanup (2025-08-07)

### Removed Obsolete Scripts ✅
- ✅ 4 Notion-based duplicate cleanup scripts 
- ✅ 2 Notion MCP inspector scripts
- ✅ 1 Notion-based test pipeline script
- ✅ 1 Notion-based automated processor
- ✅ 1 Completed UV migration script  
- ✅ 1 MCP server test script

### Current Status ✅
- ✅ **20 essential scripts** (down from 29)
- ✅ **Pure GraphRAG focus** - no Notion dependencies
- ✅ **Clear organization** by function and purpose
- ✅ **All scripts tested** and functional with current architecture

---

*Updated: 2025-08-07 - Essential scripts only, pure GraphRAG architecture*