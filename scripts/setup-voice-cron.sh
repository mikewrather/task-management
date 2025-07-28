#!/bin/bash
# Setup automated voice processing cron job

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="$PROJECT_ROOT/scripts/automated-voice-processor.py"
VENV_PATH="$PROJECT_ROOT/venv"
LOG_PATH="$PROJECT_ROOT/logs/cron-voice.log"

echo "🔧 Setting up voice processing automation..."
echo "📁 Project root: $PROJECT_ROOT"
echo "🐍 Script: $SCRIPT_PATH"
echo "📝 Logs: $LOG_PATH"

# Ensure directories exist
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/data"

# Make script executable
chmod +x "$SCRIPT_PATH"

# Create wrapper script for cron (cron has limited environment)
WRAPPER_SCRIPT="$PROJECT_ROOT/scripts/voice-cron-wrapper.sh"
cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash
# Cron wrapper for voice processing automation
# This ensures proper environment and path setup

# Set working directory
cd "$PROJECT_ROOT"

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Export path to ensure commands are found
export PATH="\$PATH:/usr/local/bin:/usr/bin:/bin"

# Run the automation script
python "$SCRIPT_PATH" >> "$LOG_PATH" 2>&1

# Add separator to log
echo "----------------------------------------" >> "$LOG_PATH"
EOF

chmod +x "$WRAPPER_SCRIPT"

echo "✅ Created wrapper script: $WRAPPER_SCRIPT"

# Generate crontab entry
CRON_ENTRY="# Voice processing automation - check every 5 minutes
*/5 * * * * $WRAPPER_SCRIPT"

echo ""
echo "📋 Cron entry to add:"
echo "$CRON_ENTRY"
echo ""

# Offer to install automatically
read -p "🤖 Would you like to install this cron job automatically? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📥 Adding cron job..."
    
    # Create temporary cron file
    TEMP_CRON=$(mktemp)
    
    # Get existing crontab (if any) and add new entry
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") > "$TEMP_CRON"
    
    # Install new crontab
    crontab "$TEMP_CRON"
    rm "$TEMP_CRON"
    
    echo "✅ Cron job installed successfully!"
    echo ""
    echo "📊 View current crontab: crontab -l"
    echo "📝 View logs: tail -f $LOG_PATH"
    echo "🔧 Edit crontab: crontab -e"
    
else
    echo "📋 Manual installation:"
    echo "1. Run: crontab -e"
    echo "2. Add this line:"
    echo "   $CRON_ENTRY"
    echo ""
fi

echo ""
echo "🎯 Automation setup complete!"
echo ""
echo "📋 Summary:"
echo "  • Checks Google Drive every 5 minutes"
echo "  • Processes new audio files automatically"
echo "  • Creates tasks in Notion"
echo "  • Tracks processed files to avoid duplicates"
echo "  • Logs everything to: $LOG_PATH"
echo ""
echo "🔍 Test manually: $WRAPPER_SCRIPT"
echo "📝 Check logs: tail -f $LOG_PATH"
echo "📊 View cron jobs: crontab -l"

# Create a quick test command
echo ""
echo "🧪 Quick test command:"
echo "source $VENV_PATH/bin/activate && python $SCRIPT_PATH"