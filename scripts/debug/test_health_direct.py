#!/usr/bin/env python3
import subprocess
import json
import os
import re

# Change to project directory where .mcp.json is located
original_cwd = os.getcwd()
project_dir = "/home/mike/development/task-management"
os.chdir(project_dir)

# Set PROJECT_AGENTS_DIR if not set
os.environ["PROJECT_AGENTS_DIR"] = os.environ.get("PROJECT_AGENTS_DIR", "/home/mike/development/agent-db")

# Use the exact same approach as GraphRAGTaskAdapter
claude_path = "/home/mike/.nvm/versions/node/v24.2.0/bin/claude"

# Create the exact prompt that GraphRAG adapter uses
tool_name = "get_health_status"
parameters = {}
mcp_tool_name = "mcp__agent-db__get_health_status"

prompt = f"""Use the {mcp_tool_name} tool with these exact parameters:
{json.dumps(parameters, indent=2)}

Return ONLY the raw JSON result from the tool, with no additional text or formatting."""

cmd = [
    claude_path, 
    "-p", prompt,
    "--dangerously-skip-permissions",
    "--output-format", "json"
]

try:
    # Execute with the same environment setup as GraphRAG adapter
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=None,  # No timeout - let Claude finish
        env={**os.environ, "PYTHONPATH": f"{project_dir}/src:{os.environ.get('PYTHONPATH', '')}"} 
    )
    
    if result.returncode != 0:
        print(f"Claude execution failed: {result.stderr}")
    else:
        # Try to extract JSON from response using GraphRAG's approach
        output = result.stdout.strip()
        
        # First check if this is a claude JSON output format
        try:
            claude_response = json.loads(output)
            if isinstance(claude_response, dict) and 'result' in claude_response:
                # Extract the result field which contains the actual response
                result_content = claude_response['result']
                # Remove markdown code block if present
                if result_content.startswith('```json') and result_content.endswith('```'):
                    result_content = result_content[7:-3].strip()
                response = json.loads(result_content)
                print(json.dumps(response, indent=2))
            else:
                print(f"Unexpected response format: {json.dumps(claude_response, indent=2)}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse initial JSON: {e}")
            
            # Fallback: Look for JSON in the output using GraphRAG patterns
            json_patterns = [
                r'\{[^{}]*"success"[^{}]*:.*?\}(?=\s*$|\s*\n)',  # Look for success response
                r'\{[^{}]*"components"[^{}]*:.*?\}',  # Look for health check response  
                r'```json\s*(\{.*?\})\s*```',  # JSON in code block
                r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})'  # Generic JSON object
            ]
            
            found = False
            for pattern in json_patterns:
                json_match = re.search(pattern, output, re.DOTALL)
                if json_match:
                    try:
                        json_str = json_match.group(1) if '```' in pattern else json_match.group()
                        response = json.loads(json_str)
                        print(json.dumps(response, indent=2))
                        found = True
                        break
                    except json.JSONDecodeError:
                        continue
            
            if not found:
                print(f"No valid JSON found in Claude response: {output[:200]}...")

finally:
    os.chdir(original_cwd)