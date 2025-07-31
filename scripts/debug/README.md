# Debug Scripts

This directory contains debugging and testing utilities for the Voice Task Manager system. These scripts are used for troubleshooting GraphRAG/MCP connections and testing individual components.

## ⚠️ Important Notes

- These scripts are for debugging purposes only
- Do not use in production
- Always use the main `vtm` CLI for normal operations
- Most scripts require proper `.env` configuration

## Script Categories

### Health Checks
- `check_health_status.py` - Check GraphRAG database health
- `test_health_*.py` - Various health check implementations

### MCP Testing
- `debug_mcp_raw.py` - Test raw MCP communication
- `direct_mcp_query.py` - Direct MCP query execution
- `test_mcp_*.py` - MCP-specific tests

### GraphRAG Queries
- `execute_cypher_*.py` - Various Cypher query executions
- `get_areas_*.py` - Area retrieval tests
- `get_projects_*.py` - Project retrieval tests
- `query_*.py` - Various query implementations

### Direct Database Access
- `neo4j_direct_query.py` - Direct Neo4j queries
- `direct_graphrag_query.py` - Direct GraphRAG access

## Usage Examples

```bash
# Check database health
python scripts/debug/check_health_status.py

# Test area retrieval
python scripts/debug/get_areas_direct.py

# Execute a Cypher query
python scripts/debug/execute_cypher_query.py
```

## Cleanup

These scripts should be reviewed periodically and removed if no longer needed. Consider converting frequently-used debug scripts into proper CLI commands or tests.