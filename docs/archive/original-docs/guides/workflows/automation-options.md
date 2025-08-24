# Voice File Monitoring Automation Options

## Current Limitation

The system **should** be automatically watching the Google Drive folder, but there's a technical constraint: **Google Drive API authentication complexity**. Here are your options:

## Option 1: Simple Cron Monitoring (Recommended)

Add this to your crontab to get reminders every 5 minutes:

```bash
# Edit your crontab
crontab -e

# Add this line to check every 5 minutes
*/5 * * * * /home/mike/development/task-management/scripts/voice-monitor-cron.sh

# Or for hourly checks
0 * * * * /home/mike/development/task-management/scripts/voice-monitor-cron.sh
```

This will:
- ✅ Remind you to check for new files
- ✅ Show the exact commands to run
- ✅ Work immediately without complex setup

## Option 2: Browser Bookmark Automation

Create browser bookmarks for quick access:

1. **Check Folder**: `https://drive.google.com/drive/folders/1vUNQV617t5mXHtyYrGro6Q3K-6JCmuUj`
2. **Process File**: `http://localhost:8000/scripts/run/f/voice/process-and-delete-audio-with-logging`

Workflow:
1. Click bookmark 1 to check for new files
2. If files found, make public and copy ID
3. Click bookmark 2 and paste file ID

## Option 3: Desktop Notification Script

```bash
# Create a desktop notification every 5 minutes
watch -n 300 'notify-send "Voice Monitor" "Check Google Drive for new voice recordings\nhttps://drive.google.com/drive/folders/1vUNQV617t5mXHtyYrGro6Q3K-6JCmuUj"'
```

## Option 4: Slack/Discord Bot (Future)

Set up a bot that:
- Monitors Google Drive folder
- Posts notifications when new files detected
- Provides one-click processing links

## Option 5: Full Google Drive API Authentication (Complex)

To get true automatic monitoring, you'd need:

1. **OAuth 2.0 Flow**: Interactive authentication
2. **Refresh Token Management**: Handle token expiry
3. **File Watching**: Google Drive API webhooks or polling
4. **Duplicate Detection**: Track processed files

This requires significant additional setup but would enable:
- ✅ Fully automatic processing
- ✅ No manual steps required
- ✅ Real-time file detection

## Why Not Automatic Yet?

The current "temporary public access" pattern was chosen because:
- **Quick to implement** and test the core functionality
- **Avoids complex OAuth setup** during initial development
- **Works reliably** without authentication edge cases
- **Secure enough** for short-term public access (seconds)

## Recommendation

**Start with Option 1 (Cron)** for daily use, then consider Option 5 for full automation once you're comfortable with the workflow.

The core voice-to-task pipeline works perfectly - it's just the "discovery" of new files that needs attention!

## Current Command

When you have a new file:
```bash
npx wmill script run f/voice/process-and-delete-audio-with-logging -d '{"file_url": "YOUR_FILE_ID"}'
```

## Next Steps

1. **Immediate**: Set up cron monitoring
2. **Short-term**: Create browser bookmarks
3. **Long-term**: Implement full Google Drive API auth