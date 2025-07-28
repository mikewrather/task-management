#!/bin/bash
# Voice Processing Status Dashboard
# Shows current status, recent activity, and monitoring commands

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/logs/cron-voice.log"
DB_FILE="$PROJECT_ROOT/data/processed_files.db"

echo "🎤 Voice Processing Status Dashboard"
echo "=================================="
echo ""

# Cron status
echo "📅 Cron Status:"
if crontab -l 2>/dev/null | grep -q "voice-cron-wrapper"; then
    echo "   ✅ Cron job active (runs every 5 minutes)"
    NEXT_RUN=$(date -d "$(date '+%Y-%m-%d %H:%M') + 5 minutes - $(date '+%M') % 5 minutes" '+%H:%M')
    echo "   ⏰ Next run: ~$NEXT_RUN"
else
    echo "   ❌ Cron job not found"
fi
echo ""

# Recent activity from logs
echo "📝 Recent Activity (last 10 entries):"
if [ -f "$LOG_FILE" ]; then
    # Show last few log entries with better formatting
    tail -n 20 "$LOG_FILE" | grep -E "(Starting|Found|processed|created)" | tail -n 5 | while read line; do
        echo "   $line"
    done
    echo ""
    
    # Show processing summary from logs
    LAST_RUN=$(tail -n 50 "$LOG_FILE" | grep "Starting automated" | tail -n 1 | cut -d']' -f1 | tr -d '[')
    if [ ! -z "$LAST_RUN" ]; then
        echo "🕒 Last scan: $LAST_RUN"
    fi
else
    echo "   📭 No log file found - system hasn't run yet"
fi
echo ""

# Database statistics
echo "📊 Processing Statistics:"
if [ -f "$DB_FILE" ]; then
    cd "$PROJECT_ROOT"
    source venv/bin/activate 2>/dev/null
    python3 -c "
import sqlite3
from datetime import datetime, timedelta
conn = sqlite3.connect('$DB_FILE')

# Total processed
total = conn.execute('SELECT COUNT(*) FROM processed_files').fetchone()[0]
print(f'   📈 Total files processed: {total}')

# Today's count
today = datetime.now().strftime('%Y-%m-%d')
today_count = conn.execute('SELECT COUNT(*) FROM processed_files WHERE DATE(processed_at) = ?', (today,)).fetchone()[0]
print(f'   📅 Today: {today_count}')

# This week
week_ago = datetime.now() - timedelta(days=7)
week_count = conn.execute('SELECT COUNT(*) FROM processed_files WHERE processed_at > ?', (week_ago,)).fetchone()[0]
print(f'   📈 This week: {week_count}')

# Most recent
recent = conn.execute('SELECT processed_at, transcript FROM processed_files ORDER BY processed_at DESC LIMIT 1').fetchone()
if recent:
    timestamp, transcript = recent
    short_transcript = transcript[:60] + '...' if len(transcript) > 60 else transcript
    dt = datetime.fromisoformat(timestamp)
    print(f'   🕐 Most recent: {dt.strftime(\"%m/%d %H:%M\")} - \"{short_transcript}\"')

conn.close()
"
else
    echo "   📭 No database found - no files processed yet"
fi
echo ""

# System health
echo "🔧 System Health:"

if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "   ✅ Environment file exists"
else
    echo "   ⚠️ .env file missing"
fi

if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "   ✅ Virtual environment ready"
else
    echo "   ⚠️ Virtual environment missing"
fi
echo ""

# Quick commands
echo "🛠️ Quick Commands:"
echo "   📝 View live logs:     tail -f $LOG_FILE"
echo "   🧪 Test manually:     $PROJECT_ROOT/scripts/voice-cron-wrapper.sh"
echo "   📊 Show notifications: python3 $PROJECT_ROOT/scripts/notification-system.py summary"
echo "   🔧 Edit cron:         crontab -e"
echo "   📋 View tasks:        open https://www.notion.so/183267fb-e1c1-4b3b-a42a-5ac1ab8353eb"
echo ""

# Live tail option
echo "💡 Want to monitor live? Run: tail -f $LOG_FILE"