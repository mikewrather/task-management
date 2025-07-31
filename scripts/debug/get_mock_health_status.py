#!/usr/bin/env python3
import json

# Return the mock health status that GraphRAG adapter would return
# when real MCP is not available or fails
mock_response = {
    "success": True,
    "status": "healthy"
}

print(json.dumps(mock_response, indent=2))