#!/bin/bash
# Simple cron script to remind about checking voice files

echo "=== Voice File Monitor $(date) ==="
echo ""
echo "🔍 Checking for new voice recordings..."
echo "📁 Google Drive Folder: https://drive.google.com/drive/folders/1vUNQV617t5mXHtyYrGro6Q3K-6JCmuUj"
echo ""
echo "📋 To process new audio files:"
echo "1. Check your Google Drive folder for new .m4a files"
echo "2. Right-click file > Share > Anyone with link"
echo "3. Copy file ID from URL (between /d/ and /view)"
echo "4. Run: npx wmill script run f/voice/process-and-delete-audio-with-logging -d '{\"file_url\": \"FILE_ID\"}'"
echo ""
echo "⏰ Next check in 5 minutes..."
echo ""

# Optional: Add this to your crontab to run every 5 minutes
# */5 * * * * /home/mike/development/task-management/scripts/voice-monitor-cron.sh >> /home/mike/development/task-management/logs/voice-monitor.log 2>&1