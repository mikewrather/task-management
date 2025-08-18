# Claude CLI Subprocess Authentication Problem

## Executive Summary

Subprocess calls to the Claude Code CLI intermittently fail with authentication/model-availability errors (e.g., 404 "model: opusplan"), degrading the system to a mock fallback and disabling intelligent MCP-powered features. The primary causes are:
- Inconsistent CLI binary resolution (`~/.claude/local/claude` vs NVM vs PATH)
- Missing or incorrect environment in automation (no `HOME`, minimal `PATH`), preventing the CLI from locating on-disk OAuth credentials/config
- Deprecated flags (`--mcp-debug`) and lack of quick preflight checks

This plan adopts robust, CLI-supported approaches:
- Standardize subprocess environment and CLI binary resolution
- Prefer long-lived Max-plan OAuth tokens via `claude setup-token` with `CLAUDE_CODE_OAUTH_TOKEN` in headless contexts; otherwise rely on on-disk OAuth creds under the correct config dir
- Use supported flags (`--debug`, `--mcp-config`, `--strict-mcp-config`, `--dangerously-skip-permissions` as appropriate)
- Add a fast preflight to fail early with actionable diagnostics

## The Problem: Authentication and Environment Mismatch

### What Happens

1. User authenticates Claude via browser OAuth flow
   - Has a Max plan session
   - Credentials stored on disk (Linux: typically `~/.claude/.credentials.json`; newer CLIs may honor XDG)
2. Voice daemon runs and tries to process voice files
   - Calls GraphRAG adapter / Claude processor
   - Spawns subprocess using a hardcoded CLI path (may differ from the binary used during login)
   - Cron/systemd-like environments often lack `HOME`/`PATH`, so the CLI cannot find credentials/config
3. Authentication/model availability fails
   - Errors like "model: opusplan" 404 mean the credential in use does not have Opus access (Pro token, API key without entitlement, or mis-scoped token)
   - Or the subprocess cannot locate saved OAuth credentials due to missing `HOME`/config dir
   - Result: MCP servers inaccessible; intelligent features disabled

### When This Happens

- Every subprocess call from GraphRAG adapter in a sparse environment
- Voice processing daemon runs (cron/systemd)
- Manual script execution that uses MCP tools but lacks proper env
- Testing that requires real MCP connections

### Impact

```yaml
With Authentication (Expected):
  - Tasks created with proper TASK_MANAGEMENT:TASK labels
  - Automatic project/area relationships
  - Embeddings generated for semantic search
  - Deduplication based on similarity
  - Access to existing knowledge graph

Without Authentication (Current):
  - No task creation in Neo4j
  - No intelligent categorization
  - No embeddings or deduplication
  - Empty query results
  - System essentially non-functional
```

## Root Cause Analysis

### Why Authentication Fails

Environment/config discovery issues:
- Claude CLI primarily reads credentials from disk on Linux (e.g., `~/.claude/.credentials.json`) or from XDG paths if configured; subprocesses must have the correct `HOME`/`PATH` (or `XDG_CONFIG_HOME`/`CLAUDE_CONFIG_DIR`) to find them
- Multiple installed `claude` binaries can read different config locations/versions

Incorrect or deprecated flags:
- `--mcp-debug` is deprecated; use `--debug` for MCP and auth troubleshooting

Credential scope problems:
- Using Pro-level credentials or API keys without Opus entitlement yields 404 for Opus; Max plan or a correct long-lived Claude Code token is required

### Example of Current Code Path That Fails

In `src/voice_task_manager/adapters/graphrag.py`:

```python
cmd = [
    claude_path,
    "-p", prompt,
    "--dangerously-skip-permissions",
    "--mcp-config", ".mcp.json",
    "--output-format", "json"
]

result = subprocess.run(
    cmd,
    env={**os.environ, "PYTHONPATH": "..."}
)
```

This will fail if:
- `HOME` does not point to the user that holds `~/.claude/`
- `PATH` does not include the installed `claude` binary path
- The credential in use is Pro/API-key scoped and lacks Opus access

## Recommended Solution: Stable CLI Resolution + Supported Auth Paths

### Solution Overview

Use one of two supported, reliable authentication strategies, and ensure the subprocess environment/binary is consistent:
1) Interactive/dev: rely on on-disk OAuth credentials under the correct config directory (`~/.claude/` by default; XDG respected in newer versions). Ensure `HOME`/`PATH` are present so the subprocess can locate them
2) Headless/CI: generate a long-lived Claude Code token with `claude setup-token` and supply it via `CLAUDE_CODE_OAUTH_TOKEN` (preferred) or `ANTHROPIC_AUTH_TOKEN`. Avoid API keys unless you accept per-token charges and potential model limits

### Implementation Details

#### Step 1: Resolve CLI path and build a robust environment

```python
from pathlib import Path
import os, shutil

PROJECT_DIR = "/home/mike/development/task-management"
NVM_CLAUDE_BIN = "/home/mike/.nvm/versions/node/v24.2.0/bin/claude"
LOCAL_NATIVE_CLAUDE = str(Path.home() / ".claude" / "local" / "claude")

def resolve_claude_path() -> str:
    return shutil.which("claude") or (LOCAL_NATIVE_CLAUDE if Path(LOCAL_NATIVE_CLAUDE).exists() else NVM_CLAUDE_BIN)

def build_claude_env() -> dict:
    env = {**os.environ}
    env.setdefault("HOME", str(Path.home()))
    # Optional: XDG/CLAUDE_CONFIG_DIR if using custom config location
    nvm_bin_dir = str(Path(NVM_CLAUDE_BIN).parent)
    if nvm_bin_dir not in env.get("PATH", "") and Path(nvm_bin_dir).exists():
        env["PATH"] = f"{nvm_bin_dir}:{env.get('PATH','')}"
    env["PYTHONPATH"] = f"{PROJECT_DIR}/src:{env.get('PYTHONPATH','')}"
    return env
```

#### Step 2: Supply credentials via supported mechanisms

Headless/CI (recommended):
```bash
# One-time on dev machine
claude setup-token
# Copy the long-lived token and set in CI environment
export CLAUDE_CODE_OAUTH_TOKEN="Claude-..."
```

Interactive/dev: ensure you have logged in (`claude login`) and that subprocesses inherit `HOME`/config paths.

#### Step 3: Add a fast preflight and use current flags

```python
import subprocess

def preflight_claude_ok() -> tuple[bool, str]:
    cmd = [resolve_claude_path(), "-p", "Return only: OK", "--output-format", "json", "--debug"]
    try:
        r = subprocess.run(cmd, cwd=PROJECT_DIR, env=build_claude_env(), capture_output=True, text=True, timeout=30)
        return (r.returncode == 0, r.stderr or r.stdout)
    except Exception as e:
        return False, str(e)
```

Use `--debug` instead of deprecated `--mcp-debug`, and consider `--strict-mcp-config` to avoid unexpected servers.

### Why This Solution Works

1. Aligned with CLI behavior: The CLI reads disk creds under the correct config dir, or accepts supported env tokens (`CLAUDE_CODE_OAUTH_TOKEN`, `ANTHROPIC_AUTH_TOKEN`) and API keys (`ANTHROPIC_API_KEY`)
2. Max plan preserved: Using OAuth login or `setup-token` avoids API credit consumption and enables Opus on Max plans
3. Robust automation: Explicit `HOME`/`PATH`, consistent binary, and preflight prevent silent failures in cron/systemd contexts
4. Clear diagnostics: `--debug` and early checks surface auth/model issues before long MCP runs

## Implementation Plan

### Phase 1: Stabilize subprocess execution (1-2 hours)
1. Consolidate CLI resolution (PATH → `~/.claude/local/claude` → NVM) and remove hardcoded paths
2. Build a robust `env` for subprocess: set `HOME`, ensure `PATH` contains the chosen binary dir, set `PYTHONPATH`; optionally set `XDG_CONFIG_HOME` or `CLAUDE_CONFIG_DIR`
3. Replace `--mcp-debug` with `--debug`; add `--strict-mcp-config`
4. Add `preflight_claude_ok()` before heavy MCP calls; fail fast with actionable logs

### Phase 2: Headless credentials (1-2 hours)
1. Document and (optionally) adopt `claude setup-token` for CI; inject via `CLAUDE_CODE_OAUTH_TOKEN`
2. Add detection/logging of auth method in use (disk creds vs env token)

### Phase 3: Hardening (future)
1. Add health metrics and structured stderr logging for Claude runs
2. Provide a CLI self-check command in the app (prints resolved binary, config dir, auth preflight result)
3. Consider SDK migration only if needed

## Success Criteria

- [ ] Preflight passes in automation (non-interactive environment)
- [ ] MCP tools (agent-db) accessible with `--strict-mcp-config`
- [ ] No 404 "opusplan" errors when using Max plan
- [ ] Max plan usage confirmed; no API-key charges
- [ ] Single consistent CLI path used across runs

## Files to Modify

1. Primary Changes:
   - `src/voice_task_manager/adapters/graphrag.py` - Standardize CLI resolution/env, add preflight, update flags
   - `src/voice_task_manager/processors/claude_processor.py` - Same as above
   - `src/voice_task_manager/services/session_manager.py` - Add execution readiness helper; improve diagnostics

2. Testing:
   - `scripts/debug/test_mcp_connection.py` - Verify preflight and MCP access
   - `tests/unit/adapters/test_graphrag.py` - Unit tests for preflight failure handling

3. Documentation:
   - `CLAUDE.md` - Add headless token guidance (`setup-token`, `CLAUDE_CODE_OAUTH_TOKEN`)
   - `docs/operations` - Note environment requirements for cron/systemd

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Wrong binary/config dir | Auth not found | Resolve binary deterministically; set `HOME`/`CLAUDE_CONFIG_DIR` |
| Token expires | Auth fails | Use `setup-token` (long-lived); add preflight and clear error logs |
| Pro vs Max mismatch | 404 on Opus | Ensure Max plan creds; regenerate token with latest CLI |
| Deprecated flags | Reduced visibility | Use `--debug`; remove `--mcp-debug` |
| Secrets exposure | Security issue | Never log token values; inject via env, not code |

## Repository-specific updates (actionable)

The following concrete edits will update our current implementation to the stable approach above.

### 1) Add a shared CLI utility

- New file: `src/voice_task_manager/utils/claude_cli.py`
- Purpose: Resolve the `claude` binary deterministically, build a robust environment for subprocesses, and provide a quick auth preflight.

```python
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Dict, Tuple

PROJECT_DIR = "/home/mike/development/task-management"
NVM_CLAUDE_BIN = "/home/mike/.nvm/versions/node/v24.2.0/bin/claude"
LOCAL_NATIVE_CLAUDE = str(Path.home() / ".claude" / "local" / "claude")

def resolve_claude_path() -> str:
    path_bin = shutil.which("claude")
    if path_bin:
        return path_bin
    if Path(LOCAL_NATIVE_CLAUDE).exists():
        return LOCAL_NATIVE_CLAUDE
    return NVM_CLAUDE_BIN

def build_claude_env(base_env: Dict[str, str] | None = None) -> Dict[str, str]:
    env = dict(base_env or os.environ)
    env.setdefault("HOME", str(Path.home()))
    # If using XDG or custom config dir, set one of the following explicitly:
    # env.setdefault("XDG_CONFIG_HOME", f"{Path.home()}/.config")
    # env.setdefault("CLAUDE_CONFIG_DIR", f"{Path.home()}/.claude")
    nvm_bin = str(Path(NVM_CLAUDE_BIN).parent)
    if nvm_bin and nvm_bin not in env.get("PATH", "") and Path(nvm_bin).exists():
        env["PATH"] = f"{nvm_bin}:{env.get('PATH','')}"
    env["PYTHONPATH"] = f"{PROJECT_DIR}/src:{env.get('PYTHONPATH','')}"
    return env

def preflight_claude_ok(env: Dict[str, str] | None = None) -> Tuple[bool, str]:
    import subprocess
    cmd = [resolve_claude_path(), "-p", "Return only: OK", "--output-format", "json", "--debug"]
    try:
        r = subprocess.run(cmd, cwd=PROJECT_DIR, env=env or build_claude_env(), capture_output=True, text=True, timeout=30)
        return (r.returncode == 0, r.stderr or r.stdout)
    except Exception as exc:
        return False, str(exc)
```

### 2) Update `src/voice_task_manager/adapters/graphrag.py`

- Import and use the utility functions.
- Replace hardcoded CLI path; use `cwd=project_dir` rather than `os.chdir`.
- Build env via `build_claude_env()`.
- Run `preflight_claude_ok()` and fall back to mock on failure.
- Replace `--mcp-debug` with `--debug` and add `--strict-mcp-config`.

Example inside `_execute_mcp_command` where we construct and run the process:

```python
from ..utils.claude_cli import resolve_claude_path, build_claude_env, preflight_claude_ok

project_dir = "/home/mike/development/task-management"
env = build_claude_env()
ok, err = preflight_claude_ok(env)
if not ok:
    self.logger.error(f"Claude preflight failed: {err}")
    self.logger.warning(f"Falling back to mock for {tool_name}")
    # ... return mock response early ...

cmd = [
    resolve_claude_path(),
    "-p", prompt,
    "--dangerously-skip-permissions",
    "--mcp-config", f"{project_dir}/.mcp.json",
    "--strict-mcp-config",
    "--debug",
    "--output-format", "json",
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=None, cwd=project_dir, env=env)
```

### 3) Update `src/voice_task_manager/processors/claude_processor.py`

- Apply the same subprocess treatment in `_execute_claude_with_mcp`:
  - Use `resolve_claude_path()` and `build_claude_env()`.
  - Preflight before heavy run; bail out with a clear error JSON.
  - Add `--strict-mcp-config` and `--debug`; keep `--dangerously-skip-permissions`.
  - Use `cwd=project_dir` instead of `os.chdir`.

### 4) Update `src/voice_task_manager/services/session_manager.py`

- Add a small helper that surfaces execution readiness for diagnostics:

```python
from ..utils.claude_cli import preflight_claude_ok, build_claude_env

def get_execution_readiness(self) -> tuple[bool, str]:
    try:
        return preflight_claude_ok(build_claude_env())
    except Exception as exc:
        return False, str(exc)
```

- Optionally update `test_claude_execution()` to use `resolve_claude_path()` and `build_claude_env()`.

### 5) Headless token support (optional but recommended for CI)

- Generate a long-lived token on a dev machine:

```bash
claude setup-token
```

- Inject into CI/service environment:

```bash
export CLAUDE_CODE_OAUTH_TOKEN="Claude-..."
```

- Do not hardcode tokens in code or logs. Prefer env files or systemd `Environment=` entries.

### 6) Test plan

1. Run the new preflight via a small script or call path; confirm success and no 404.
2. Execute `scripts/debug/test_mcp_connection.py`; ensure MCP health passes.
3. Run a voice processing path end-to-end and verify embeddings/relationships are created.
4. Validate that logs no longer show `opusplan`/404 errors and that a single CLI path is used.

## Conclusion

Stabilizing Claude CLI subprocess authentication is primarily an environment and configuration task: unify the CLI binary, ensure the subprocess has a valid `HOME`/config path, adopt supported tokens for headless runs (`claude setup-token` → `CLAUDE_CODE_OAUTH_TOKEN`), switch to current flags, and add a quick preflight. This preserves Max plan benefits, avoids API costs, and restores reliable MCP-powered task intelligence.
