"""
Claude CLI utility functions for robust subprocess execution
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Dict, Tuple

# Always use the native Claude binary (newer version)
CLAUDE_NATIVE_BIN = "/home/mike/.claude/local/claude"
PROJECT_DIR = "/home/mike/development/task-management"


def get_claude_path() -> str:
    """
    Get the correct Claude binary path.
    Always returns the native binary, not the NVM one.
    
    Returns:
        Path to the Claude binary
    """
    return CLAUDE_NATIVE_BIN


def build_claude_env(base_env: Dict[str, str] | None = None) -> Dict[str, str]:
    """
    Build a robust environment for Claude subprocess execution.
    
    Ensures:
    - HOME is set so CLI can find ~/.claude/.credentials.json
    - PYTHONPATH includes project source
    - PATH includes native Claude binary directory
    - Removes ANTHROPIC_API_KEY to prevent API credit usage
    
    Args:
        base_env: Base environment to extend (defaults to os.environ)
        
    Returns:
        Environment dictionary for subprocess
    """
    env = dict(base_env or os.environ)
    
    # Critical: Set HOME so Claude can find credentials
    env.setdefault("HOME", str(Path.home()))
    
    # IMPORTANT: Remove ANTHROPIC_API_KEY to ensure OAuth is used instead of API credits
    # The API key causes "Credit balance too low" errors when credits are exhausted
    if "ANTHROPIC_API_KEY" in env:
        del env["ANTHROPIC_API_KEY"]
    
    # Pass through OAuth token if available (for headless operation)
    # This takes precedence over on-disk credentials
    if "CLAUDE_CODE_OAUTH_TOKEN" in os.environ:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = os.environ["CLAUDE_CODE_OAUTH_TOKEN"]
    
    # Add project source to Python path
    env["PYTHONPATH"] = f"{PROJECT_DIR}/src:{env.get('PYTHONPATH', '')}"
    
    # Ensure the native Claude binary directory is in PATH
    claude_bin_dir = str(Path(CLAUDE_NATIVE_BIN).parent)
    current_path = env.get("PATH", "")
    if claude_bin_dir not in current_path:
        env["PATH"] = f"{claude_bin_dir}:{current_path}"
    
    # Optional: Set config directory explicitly if needed
    # env.setdefault("CLAUDE_CONFIG_DIR", f"{Path.home()}/.claude")
    
    return env


def preflight_claude_ok(env: Dict[str, str] | None = None, timeout: int = 30) -> Tuple[bool, str]:
    """
    Run a quick preflight check to verify Claude authentication.
    
    This prevents long-running MCP operations from failing due to auth issues.
    
    Args:
        env: Environment for subprocess (defaults to build_claude_env())
        timeout: Maximum seconds to wait for response
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    if env is None:
        env = build_claude_env()
    
    cmd = [
        get_claude_path(),
        "-p", "Return only: OK",
        "--output-format", "json"
        # Removed --debug flag as it can corrupt JSON output
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            return True, "Claude authentication successful"
        else:
            # Extract error message from stderr or stdout
            error_msg = result.stderr or result.stdout or "Unknown error"
            
            # Check for credit balance issues (indicates API key usage instead of OAuth)
            if "credit balance" in error_msg.lower() or "credit" in error_msg.lower() and "low" in error_msg.lower():
                return False, "Authentication failed: API key detected with exhausted credits. OAuth should be used for Max plan."
            elif "404" in error_msg and "opusplan" in error_msg.lower():
                return False, "Authentication failed: Max plan not available (404 opusplan)"
            elif "credentials" in error_msg.lower():
                return False, f"Authentication failed: Credentials not found or invalid"
            else:
                return False, f"Authentication failed: {error_msg[:200]}"
                
    except subprocess.TimeoutExpired:
        return False, f"Preflight check timed out after {timeout} seconds"
    except Exception as exc:
        return False, f"Preflight check error: {str(exc)}"


def execute_claude_command(
    prompt: str,
    mcp_config: str = ".mcp.json",
    timeout: int | None = None,
    skip_preflight: bool = False
) -> Tuple[bool, str, str]:
    """
    Execute a Claude command with robust error handling.
    
    Args:
        prompt: The prompt to send to Claude
        mcp_config: Path to MCP config file (relative to PROJECT_DIR)
        timeout: Command timeout in seconds (None for no timeout)
        skip_preflight: Skip the preflight check (not recommended)
        
    Returns:
        Tuple of (success: bool, stdout: str, stderr: str)
    """
    env = build_claude_env()
    
    # Run preflight check unless explicitly skipped
    if not skip_preflight:
        ok, error_msg = preflight_claude_ok(env)
        if not ok:
            return False, "", error_msg
    
    cmd = [
        get_claude_path(),
        "-p", prompt,
        "--dangerously-skip-permissions",
        "--mcp-config", mcp_config,
        "--strict-mcp-config",  # Only use specified MCP servers
        # Removed --debug flag as it corrupts JSON output
        "--output-format", "json"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired as e:
        stderr = e.stderr if hasattr(e, 'stderr') and e.stderr else "Command timed out"
        return False, "", f"Timeout after {timeout}s: {stderr}"
    except Exception as exc:
        return False, "", f"Execution error: {str(exc)}"