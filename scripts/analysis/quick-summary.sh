#!/bin/bash
# Quick voice processing summary - perfect for adding to your shell prompt or terminal startup

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Quick status check
if [ -f "$PROJECT_ROOT/data/processed_files.db" ]; then
    cd "$PROJECT_ROOT"
    source venv/bin/activate 2>/dev/null
    STATS=$(python3 -c "
import sqlite3
from datetime import datetime
conn = sqlite3.connect('data/processed_files.db')
total = conn.execute('SELECT COUNT(*) FROM processed_files').fetchone()[0]
today = datetime.now().strftime('%Y-%m-%d')
today_count = conn.execute('SELECT COUNT(*) FROM processed_files WHERE DATE(processed_at) = ?', (today,)).fetchone()[0]
print(f'{total},{today_count}')
conn.close()
" 2>/dev/null)
    
    if [ ! -z "$STATS" ]; then
        TOTAL=$(echo $STATS | cut -d',' -f1)
        TODAY=$(echo $STATS | cut -d',' -f2)
        
        if [ "$TODAY" -gt 0 ]; then
            echo "🎤 Voice: $TODAY processed today ($TOTAL total)"
        else
            echo "🎤 Voice: Ready ($TOTAL total processed)"
        fi
    else
        echo "🎤 Voice: System ready"
    fi
else
    echo "🎤 Voice: System ready (no files processed yet)"
fi