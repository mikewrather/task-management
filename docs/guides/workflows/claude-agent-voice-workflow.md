# Claude Code as Intelligent Agent in Voice Workflow

## The Vision: Claude as Decision-Making Agent

Instead of rigid GPT-4 prompts, Claude Code becomes an intelligent agent that can:
1. **Understand context deeply** - Access to your entire codebase, project docs
2. **Make nuanced decisions** - Handle ambiguous voice commands intelligently  
3. **Execute complex tasks** - Actually create files, run commands, update systems
4. **Learn and adapt** - Update its own decision logic based on patterns

## Architecture

```
Voice Recording → Windmill Workflow
                    ↓
                Transcribe (Whisper)
                    ↓
                Claude Agent (via tmux)
                    ↓
        ┌───────────┴───────────┐
        │                       │
    Simple Tasks           Complex Tasks
    (Direct API)          (Claude executes)
```

## Implementation in Windmill

### 1. Main Workflow Script
```typescript
// f/voice_tasks/process_voice_recording
export async function main(
  audioFileId: string,
  googleDriveToken: wmill.Resource<"gdrive">,
  openaiKey: wmill.Resource<"openai">,
  notionToken: wmill.Resource<"notion">
) {
  // Step 1: Download and transcribe
  const audio = await hub.scripts.google_drive.download(audioFileId, googleDriveToken)
  const transcript = await hub.scripts.openai.whisper_transcribe(audio, openaiKey)
  
  // Step 2: Let Claude analyze and decide
  const claudeAnalysis = await wmill.runScript("f/voice_tasks/claude_analyze", {
    transcript: transcript.text,
    timestamp: new Date().toISOString()
  })
  
  // Step 3: Execute based on Claude's decision
  if (claudeAnalysis.requiresClaudeExecution) {
    // Complex task - Claude handles it
    return await wmill.runScript("f/voice_tasks/claude_execute_complex", {
      task: claudeAnalysis.complexTask,
      context: claudeAnalysis.context
    })
  } else {
    // Simple tasks - use APIs directly
    return await processSimpleTasks(claudeAnalysis.simpleTasks, notionToken)
  }
}
```

### 2. Claude Analysis Script
```typescript
// f/voice_tasks/claude_analyze
import { $ } from 'zx'

export async function main(transcript: string, timestamp: string) {
  const claudePrompt = `
You are analyzing a voice transcript for task management. 

IMPORTANT: Determine if this requires complex execution (you need to write code, create files, run multiple commands) or if it's simple (just API calls to Notion).

Transcript: "${transcript}"
Timestamp: ${timestamp}

Analyze and output JSON with this structure:
{
  "requiresClaudeExecution": boolean,
  "reason": "why this needs Claude execution or not",
  "simpleTasks": [
    {"type": "create_task", "title": "...", "project": "..."},
    {"type": "complete_task", "taskId": "..."},
    {"type": "add_note", "content": "...", "project": "..."}
  ],
  "complexTask": {
    "description": "what needs to be done",
    "estimatedSteps": ["step1", "step2"],
    "context": {}
  }
}

Examples of complex tasks that need Claude execution:
- "Set up a new Python project for the voice recognition system"
- "Debug why the notification system isn't working"
- "Create a data pipeline for analyzing last week's metrics"
- "Write tests for the authentication module"

Examples of simple tasks (API only):
- "Mark the login bug as complete"
- "Create a task to review pull requests"
- "Add a note about the meeting with Sarah"
`

  const result = await $`claude --model opus-4 << 'EOF'
${claudePrompt}
EOF`

  return JSON.parse(result.stdout)
}
```

### 3. Claude Complex Execution
```typescript
// f/voice_tasks/claude_execute_complex
export async function main(
  task: { description: string, estimatedSteps: string[], context: any }
) {
  const executionPrompt = `
Execute this task: ${task.description}

Context: ${JSON.stringify(task.context)}
Estimated steps: ${task.estimatedSteps.join(', ')}

Guidelines:
1. Break down the task into concrete actions
2. Execute each step, verifying success
3. Create any necessary files, run commands, etc.
4. Update Notion with progress/completion
5. Return a summary of what was accomplished

Write "EXECUTION_COMPLETE" to /tmp/claude-task-complete.json with results when done.
`

  // Clear previous results
  await $`rm -f /tmp/claude-task-complete.json`
  
  // Send to Claude
  await $`tmux send-keys -t claude-worker "${executionPrompt}" Enter`
  
  // Wait for completion (with timeout)
  let attempts = 0
  while (attempts < 120) { // 10 minute timeout
    await new Promise(resolve => setTimeout(resolve, 5000))
    
    try {
      const result = await $`cat /tmp/claude-task-complete.json`
      return JSON.parse(result.stdout)
    } catch (e) {
      // Not ready yet
    }
    attempts++
  }
  
  throw new Error("Claude execution timeout")
}
```

## Example Voice Commands & Claude's Role

### Simple (API-only)
- "Mark the database migration task as complete"
- "Create a task to update the README"
- "Add a note about the performance issue we discussed"

### Complex (Claude executes)
- "Set up a new Next.js project for the admin dashboard"
  - Claude: Creates project, installs deps, sets up structure
- "Debug why the cron job failed last night"
  - Claude: Checks logs, identifies issue, potentially fixes
- "Create integration tests for the new API endpoints"
  - Claude: Writes test files, runs them, ensures they pass

## Benefits of Claude as Agent

1. **Contextual Understanding**: Claude can access your entire codebase and understand project-specific context
2. **Adaptive Execution**: Can handle unexpected scenarios and make decisions
3. **Progressive Enhancement**: Start simple, Claude learns patterns over time
4. **Actual Implementation**: Not just task creation but actual code/fixes

## Session Management

```bash
# Setup script
#!/bin/bash
# init-claude-agent.sh

# Create tmux session
tmux new-session -d -s claude-agent

# Navigate to project
tmux send-keys -t claude-agent "cd /home/mike/development/task-management" Enter

# Authenticate Claude
tmux send-keys -t claude-agent "claude --model opus-4" Enter
echo "Please attach to tmux and complete browser auth"

# Once authenticated, Claude is ready to receive tasks
```

## Why This Approach?

1. **Best of both worlds**: Simple tasks use efficient APIs, complex tasks get Claude's intelligence
2. **Learning system**: Claude can update its own classification logic
3. **Real execution**: Not just planning but actual implementation
4. **Scalable complexity**: Can handle everything from "add task" to "refactor authentication system"