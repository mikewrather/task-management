# Voice Task Management - Documentation Hub

## 🎯 Current System (Python Package)

The voice task management system is a fully automated Python package that converts voice recordings into organized Notion tasks. The system processes voice files every 5 minutes via cron automation.

### Quick Start
1. Voice recordings sync from Apple Watch to Google Drive
2. Automated processing every 5 minutes via cron job
3. Tasks automatically created in Notion with proper categorization
4. Desktop notifications on completion

---

## 📚 Documentation Categories

### 🔧 [Specifications](specifications/)
Technical specifications, feature plans, and system requirements.
- **[Feature Specification](specifications/FEATURE_SPECIFICATION.md)** - Complete system capabilities and requirements

### 📖 [User Guides](guides/)
Step-by-step instructions for setup, configuration, and daily usage.
- **[Workflows](guides/workflows/)** - Daily usage patterns and automation
- **[Integrations](guides/integrations/)** - Google Drive, Notion, and third-party services

### 🏗️ [Architecture](architecture/)
System design, technical architecture, and implementation details.
- **[System Design](architecture/system-design.md)** - Technical architecture overview
- **[Project Design](architecture/project-design.md)** - Repository structure and organization
- **[MCP Server Design](architecture/mcp-server-design.md)** - Model Context Protocol server architecture
- **[MCP Tool Definitions](architecture/mcp-tool-definitions.md)** - Detailed tool schemas and specifications

### 📋 [Reference](reference/)
API documentation, command references, and technical specifications.
- **[Voice Commands Reference](reference/VOICE_COMMANDS_REFERENCE.md)** - Complete command syntax
- **[MCP Server Reference](reference/mcp-server-reference.md)** - Quick reference for MCP tools and usage
- **[API Reference](reference/api_reference.md)** - Integration APIs and endpoints
- **[Performance Analysis](reference/performance_analysis.md)** - System metrics and benchmarks

### ⚙️ [Operations](operations/)
System administration, monitoring, and maintenance documentation.
- **[Project Structure](operations/PROJECT_STRUCTURE.md)** - Repository organization
- **[Logging System](operations/LOGGING_SYSTEM.md)** - Monitoring and troubleshooting
- **[Script Audit](operations/SCRIPT_AUDIT_AND_NEXT_STEPS.md)** - Maintenance planning

### 📦 [Archive](archive/)
Historical documentation preserved for reference.

---

## 🚀 Quick Navigation

### For New Users
1. **[Feature Specification](specifications/FEATURE_SPECIFICATION.md)** - Understand system capabilities
2. **[User Guide](guides/user_guide.md)** - Get started with daily usage
3. **[Setup Guides](guides/setup/)** - Configure your environment

### For Developers
1. **[System Design](architecture/system-design.md)** - Technical architecture
2. **[API Reference](reference/api_reference.md)** - Integration development
3. **[Project Structure](operations/PROJECT_STRUCTURE.md)** - Repository organization

### For Troubleshooting
1. **[Logging System](operations/LOGGING_SYSTEM.md)** - Monitoring and diagnostics
2. **[Performance Analysis](reference/performance_analysis.md)** - System metrics
3. **[Operations Documentation](operations/)** - Maintenance procedures

---

## 📊 System Status

| Component | Status | Documentation |
|-----------|--------|---------------|
| **Voice Processing** | ✅ Production | [Feature Specification](specifications/FEATURE_SPECIFICATION.md) |
| **Cron Automation** | ✅ Running | [User Guide](guides/user_guide.md) |
| **Notion Integration** | ✅ Active | [Integrations](guides/integrations/) |
| **CLI Commands** | ✅ Available | [Voice Commands Reference](reference/VOICE_COMMANDS_REFERENCE.md) |
| **Desktop Notifications** | ✅ Working | [Workflows](guides/workflows/) |

### Performance Metrics
- **Processing Speed**: 308-716ms per query
- **Automation Frequency**: Every 5 minutes
- **Success Rate**: 100% (8/8 files processed successfully)
- **Monthly Cost**: ~$5 (OpenAI Whisper API)

---

## 🔄 Recent Updates

### Phase 1: Notion Chat Feature (Completed)
- ✅ CLI query infrastructure with intelligent parameter validation
- ✅ `vtm list tasks`, `vtm list projects`, `vtm list areas` commands
- ✅ Multiple output formats (JSON, table, rich console)
- ✅ Comprehensive test coverage (21/21 tests passing)

### MCP Server Integration (Completed)
- ✅ Model Context Protocol server exposing CLI tools to AI agents
- ✅ FastMCP-based implementation with structured output support
- ✅ Four tools: `list_tasks`, `list_projects`, `list_areas`, `server_info`
- ✅ Claude Desktop integration and MCP Inspector testing
- ✅ Comprehensive documentation and setup guides

### System Ready For
- **AI Agent Integration**: Direct access to Notion data via MCP protocol
- **Advanced Querying**: Complex filters and search capabilities through AI
- **Enhanced Automation**: Smart categorization and context analysis

*Last Updated: 2025-07-26*