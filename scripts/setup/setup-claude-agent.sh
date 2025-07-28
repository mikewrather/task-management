#!/bin/bash
# Script: setup-claude-agent.sh
# Purpose: Create and configure tmux session for Claude Code agent
# Created: 2025-01-22
# Dependencies: tmux, claude (CLI)

set -e

SESSION_NAME="claude-agent"
CLAUDE_CONFIG_DIR="$HOME/.config/claude"

echo "Setting up Claude agent in tmux session..."

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "Error: tmux is not installed. Please install it first."
    exit 1
fi

# Check if Claude CLI is installed
if ! command -v claude &> /dev/null; then
    echo "Error: Claude CLI is not installed."
    echo "Install with: npm install -g @anthropic-ai/claude-cli"
    exit 1
fi

# Check if session already exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Claude agent session already exists."
    echo "To attach: tmux attach -t $SESSION_NAME"
    echo "To kill and recreate: tmux kill-session -t $SESSION_NAME"
    exit 0
fi

# Create config directory if it doesn't exist
mkdir -p "$CLAUDE_CONFIG_DIR"

# Create new tmux session
echo "Creating tmux session: $SESSION_NAME"
tmux new-session -d -s "$SESSION_NAME" -n "claude-agent"

# Send initial commands to the session
tmux send-keys -t "$SESSION_NAME:claude-agent" "# Claude Code Agent Session" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "# This session maintains Claude authentication" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "cd $HOME/development/task-management" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "clear" C-m

# Create a startup script in the session
tmux send-keys -t "$SESSION_NAME:claude-agent" "cat > /tmp/claude-agent-startup.sh << 'EOF'" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "#!/bin/bash" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "echo 'Claude Code Agent - Voice Task Management'" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "echo '========================================='" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "echo ''" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "echo 'This session maintains Claude authentication for the voice workflow.'" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "echo ''" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "echo 'To authenticate Claude:'" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "echo '1. Run: claude login'" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "echo '2. Complete browser authentication'" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "echo '3. Verify with: claude --version'" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "echo ''" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "echo 'Config location: $CLAUDE_CONFIG_DIR'" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "echo ''" C-m
tmux send-keys -t "$SESSION_NAME:claude-agent" "EOF" C-m

tmux send-keys -t "$SESSION_NAME:claude-agent" "bash /tmp/claude-agent-startup.sh" C-m

echo ""
echo "✅ Claude agent tmux session created successfully!"
echo ""
echo "Next steps:"
echo "1. Attach to session: tmux attach -t $SESSION_NAME"
echo "2. Run: claude login"
echo "3. Complete authentication in browser"
echo "4. Detach from session: Ctrl+b, d"
echo ""
echo "The session will persist until system restart."
echo "Config will be stored in: $CLAUDE_CONFIG_DIR"