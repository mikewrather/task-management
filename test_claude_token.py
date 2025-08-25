#!/usr/bin/env python3
"""
Test script to verify Claude Max token configuration
"""

import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_token_setup():
    """Test if Claude CLI works with the token"""
    
    # Check if token is set
    token = os.getenv("CLAUDE_CODE_OAUTH_TOKEN")
    if not token or token == "YOUR_CLAUDE_MAX_TOKEN_HERE":
        print("❌ ERROR: CLAUDE_CODE_OAUTH_TOKEN not set in .env file")
        print("Please add your long-lived token from 'claude setup-token' to the .env file")
        return False
    
    print(f"✅ Token found (length: {len(token)} chars)")
    
    # Get Claude path
    claude_path = os.getenv("CLAUDE_CLI_PATH", "/home/mike/.claude/local/claude")
    if not Path(claude_path).exists():
        print(f"❌ ERROR: Claude CLI not found at {claude_path}")
        return False
    
    print(f"✅ Claude CLI found at: {claude_path}")
    
    # Test Claude execution with token
    print("\n🧪 Testing Claude CLI with token...")
    cmd = [
        claude_path,
        "-p", "Return only the text: SUCCESS",
        "--output-format", "json"
    ]
    
    env = {
        **os.environ,
        "CLAUDE_CODE_OAUTH_TOKEN": token,
        "HOME": str(Path.home())
    }
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )
        
        if result.returncode == 0:
            import json
            try:
                response = json.loads(result.stdout)
                if response.get("is_error"):
                    print(f"❌ Claude returned error: {response.get('result')}")
                    return False
                else:
                    print(f"✅ Claude execution successful!")
                    print(f"   Result: {response.get('result', 'No result')}")
                    return True
            except json.JSONDecodeError:
                print(f"❌ Could not parse Claude response: {result.stdout[:200]}")
                return False
        else:
            print(f"❌ Claude execution failed with code {result.returncode}")
            print(f"   Error: {result.stderr or result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Claude execution timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_mcp_with_token():
    """Test MCP execution with token"""
    print("\n🧪 Testing MCP execution with token...")
    
    from voice_task_manager.adapters.graphrag import GraphRAGTaskAdapter
    from voice_task_manager.utils.logging import VoiceLogger
    
    os.environ["USE_REAL_MCP"] = "true"
    
    adapter = GraphRAGTaskAdapter(VoiceLogger())
    result = adapter.test_connection()
    
    if result:
        print("✅ MCP execution successful with token!")
    else:
        print("❌ MCP execution failed")
    
    return result

if __name__ == "__main__":
    print("=" * 50)
    print("Claude Max Token Configuration Test")
    print("=" * 50)
    
    # Test basic token setup
    if test_token_setup():
        # If basic test passes, test MCP
        test_mcp_with_token()
        print("\n✅ All tests passed! Your Claude Max token is configured correctly.")
        print("\nYou can now use the voice task management system with full Claude Max access.")
    else:
        print("\n❌ Configuration incomplete. Please:")
        print("1. Run 'claude setup-token' in your terminal")
        print("2. Copy the long-lived token it provides")
        print("3. Replace 'YOUR_CLAUDE_MAX_TOKEN_HERE' in .env with your actual token")
        print("4. Run this test again")