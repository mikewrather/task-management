# Claude Authentication Solution Documentation

## Problem Summary

The Voice Task Management system was failing to authenticate with Claude CLI when executing MCP (Model Context Protocol) tools, despite having a valid Claude Max OAuth token generated via `claude setup-token`.

## Root Causes Identified

### 1. Wrong Claude CLI Path
- **Issue**: System was using hardcoded path `/home/mike/.nvm/versions/node/v24.2.0/bin/claude` which didn't exist
- **Actual Location**: `/home/mike/.claude/local/claude`

### 2. Environment Variable Conflict
- **Critical Issue**: `ANTHROPIC_API_KEY` environment variable was set in the shell environment
- **Effect**: Claude CLI prioritized the API key over the OAuth token, causing "Credit balance is too low" errors
- **Source**: API key was previously exported in shell configuration but later commented out

### 3. Missing dotenv Loading
- **Issue**: `.env` file containing `CLAUDE_CODE_OAUTH_TOKEN` wasn't being loaded in all modules
- **Effect**: OAuth token wasn't available to subprocess calls

## Solution Implementation

### 1. Centralized Claude Path Configuration
Created `get_claude_path()` function in `src/voice_task_manager/utils/config.py`:

```python
def get_claude_path() -> str:
    """Get the Claude CLI executable path."""
    # Check environment variable first
    if claude_path := os.getenv("CLAUDE_CLI_PATH"):
        if Path(claude_path).exists():
            return claude_path
    
    # Try common installation locations
    paths_to_try = [
        "/home/mike/.claude/local/claude",
        "/home/mike/.nvm/versions/node/v24.2.0/bin/claude",
        Path.home() / ".claude" / "local" / "claude",
        Path.home() / ".local" / "bin" / "claude",
    ]
    
    for path in paths_to_try:
        path = Path(path)
        if path.exists() and path.is_file():
            return str(path)
    
    raise FileNotFoundError("Claude CLI not found...")
```

### 2. Remove API Key from Subprocess Environment
In all modules executing Claude CLI (`graphrag.py`, `claude_processor.py`, `session_manager.py`):

```python
# Create environment without ANTHROPIC_API_KEY to use OAuth instead
env = {**os.environ, "PYTHONPATH": f"{project_dir}/src:{os.environ.get('PYTHONPATH', '')}"}
env.pop('ANTHROPIC_API_KEY', None)  # Remove API key to force OAuth usage

result = subprocess.run(cmd, env=env, ...)
```

### 3. Add dotenv Loading
Added to all relevant modules:

```python
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
```

### 4. Environment Configuration
In `.env` file:

```bash
# Claude CLI configuration
CLAUDE_CLI_PATH=/home/mike/.claude/local/claude
CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-[long-token-string]

# Ensure USE_REAL_MCP is set for production
USE_REAL_MCP=true
```

## How OAuth Authentication Works

1. **Token Generation**: Run `claude setup-token` to generate a long-lived OAuth token
2. **Token Storage**: Store token in `CLAUDE_CODE_OAUTH_TOKEN` environment variable
3. **Token Usage**: Claude CLI checks for this variable when `ANTHROPIC_API_KEY` is not present
4. **Priority**: Claude CLI prioritizes `ANTHROPIC_API_KEY` over `CLAUDE_CODE_OAUTH_TOKEN`

## Critical Implementation Details

### Environment Variable Priority
Claude CLI authentication priority order:
1. `ANTHROPIC_API_KEY` (if present, overrides everything)
2. `CLAUDE_CODE_OAUTH_TOKEN` (OAuth token from setup-token)
3. Interactive login (if neither is present)

### Subprocess Environment Management
When calling Claude from Python subprocess:
- Must explicitly remove `ANTHROPIC_API_KEY` from environment
- Must preserve other environment variables for proper operation
- Must load `.env` file to access `CLAUDE_CODE_OAUTH_TOKEN`

### Timeout Considerations
- MCP operations via Claude can take 30-60 seconds
- Use `timeout=None` for subprocess calls to avoid premature termination

## Testing the Solution

### Test Script
Created `test_claude_token.py` to verify configuration:

```python
def test_token_setup():
    """Test if Claude CLI works with the token"""
    token = os.getenv("CLAUDE_CODE_OAUTH_TOKEN")
    if not token:
        print("❌ ERROR: CLAUDE_CODE_OAUTH_TOKEN not set")
        return False
    
    claude_path = get_claude_path()
    cmd = [claude_path, "-p", "Return only: SUCCESS", "--output-format", "json"]
    
    env = {**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": token}
    env.pop('ANTHROPIC_API_KEY', None)  # Critical: Remove API key
    
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
    return result.returncode == 0
```

### Verification Steps
1. Check token is set: `echo $CLAUDE_CODE_OAUTH_TOKEN`
2. Verify no API key: `echo $ANTHROPIC_API_KEY` (should be empty)
3. Test Claude directly: `claude -p "test"`
4. Run test script: `python test_claude_token.py`
5. Test full pipeline: `vtm process`

## Troubleshooting Guide

### Issue: "Credit balance is too low"
- **Cause**: API key is overriding OAuth token
- **Fix**: Ensure `ANTHROPIC_API_KEY` is not set in environment
- **Check**: `unset ANTHROPIC_API_KEY` or remove from shell config

### Issue: "Claude CLI not found"
- **Cause**: Wrong path to Claude executable
- **Fix**: Set `CLAUDE_CLI_PATH` in `.env` to correct location
- **Find Claude**: `which claude` or `find ~ -name claude -type f 2>/dev/null`

### Issue: "No CLAUDE_CODE_OAUTH_TOKEN"
- **Cause**: Token not generated or not loaded from `.env`
- **Fix**: Run `claude setup-token` and add token to `.env`
- **Verify**: Token should start with `sk-ant-oat01-`

### Issue: Intermittent MCP Responses
- **Symptom**: Claude sometimes returns only usage data, not actual results
- **Workaround**: Handle usage-only responses gracefully
- **Code**: Return empty results when only usage data received

## Lessons Learned

1. **Environment Variable Conflicts**: Always check for conflicting authentication methods
2. **Explicit Environment Control**: When using subprocess, explicitly manage environment variables
3. **dotenv Loading**: Ensure `.env` is loaded in all entry points
4. **Centralized Configuration**: Use centralized functions for system paths and configuration
5. **Comprehensive Testing**: Test authentication at multiple levels (direct CLI, subprocess, full pipeline)

## Files Modified

- `src/voice_task_manager/utils/config.py` - Added `get_claude_path()`
- `src/voice_task_manager/adapters/graphrag.py` - Added dotenv, removed API key from env
- `src/voice_task_manager/processors/claude_processor.py` - Added dotenv, removed API key from env
- `src/voice_task_manager/services/session_manager.py` - Added dotenv, removed API key from env
- `src/voice_task_manager/cli.py` - Added dotenv loading at entry point
- `.env` - Added Claude configuration variables
- Created test scripts: `test_claude_token.py`, `test_claude_env.py`, `test_claude_shell.sh`

## Future Improvements

1. **Token Refresh**: Implement automatic token refresh if OAuth tokens expire
2. **Error Messages**: Provide clearer error messages when authentication fails
3. **Configuration Validation**: Add startup validation for Claude authentication
4. **Fallback Mechanism**: Implement graceful fallback when MCP execution fails
5. **Performance**: Investigate ways to reduce 30-60s MCP initialization overhead