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

# Run the automation using new vtm package
vtm process >> "/home/mike/development/task-management/logs/cron-voice.log" 2>&1

# Add separator to log
echo "----------------------------------------" >> "/home/mike/development/task-management/logs/cron-voice.log"
