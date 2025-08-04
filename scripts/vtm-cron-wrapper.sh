#!/bin/bash
# Cron wrapper for voice processing automation (modern vtm package)
# This ensures proper environment and path setup

# Set working directory
cd "/home/mike/development/task-management"

# Set full PATH for cron environment
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/home/mike/.local/bin:$PATH"

# Activate virtual environment  
source "/home/mike/development/task-management/venv/bin/activate"

# Ensure Python can find our package
export PYTHONPATH="/home/mike/development/task-management/src:$PYTHONPATH"

# Set up desktop notification environment for cron
export USER="mike"
export HOME="/home/mike"
export DISPLAY=":0"

# Try to get the D-Bus session address for notifications
if [ -f "/tmp/dbus-session-${USER}" ]; then
    export DBUS_SESSION_BUS_ADDRESS=$(cat "/tmp/dbus-session-${USER}")
elif [ -n "$(pgrep -U ${USER} dbus-daemon)" ]; then
    export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u ${USER})/bus"
fi

# Claude authentication setup
# For Max plan users, Claude uses OAuth credentials stored in ~/.claude/.credentials.json
# Ensure HOME is set so Claude can find the credentials
export HOME="/home/mike"

# Optional: Set Anthropic API key if using API authentication instead of Max plan
# This allows claude -p commands to work without interactive login
if [ -f "/home/mike/development/task-management/.env" ]; then
    ANTHROPIC_API_KEY=$(grep '^ANTHROPIC_API_KEY=' /home/mike/development/task-management/.env | cut -d '=' -f2- | tr -d '"' | tr -d "'")
    if [ -n "$ANTHROPIC_API_KEY" ]; then
        export ANTHROPIC_API_KEY
    fi
fi

# Run the automation using new vtm package
vtm process >> "/home/mike/development/task-management/logs/cron-voice.log" 2>&1

# Add separator to log
echo "----------------------------------------" >> "/home/mike/development/task-management/logs/cron-voice.log"
