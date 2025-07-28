# Complete Voice Task Management Flow

## Overview

This guide documents the full end-to-end voice task management flow, from recording on your smartwatch to tasks appearing in Notion.

## Current Status (2025-07-03)

The system is fully operational using a **temporary public access pattern** for Google Drive files. This approach:
- Keeps files public for only seconds during processing
- Avoids complex authentication setup
- Works reliably with current APIs

## Prerequisites

- ✅ Windmill running at http://localhost:8000
- ✅ Google Drive folder shared publicly
- ✅ All API keys configured in Windmill resources
- ✅ Voice scripts deployed to Windmill

## Step-by-Step Flow

### 1. Record Voice Note

- Use Voice Recorder Pro on your Pixel Watch
- Recording automatically syncs to Google Drive folder
- Folder ID: `1vUNQV617t5mXHtyYrGro6Q3K-6JCmuUj`

### 2. Process Audio File

There are two methods:

#### Method A: Command Line (Recommended)

1. Go to your [Google Drive folder](https://drive.google.com/drive/folders/1vUNQV617t5mXHtyYrGro6Q3K-6JCmuUj)
2. Right-click the audio file → Share → Anyone with link
3. Copy the file ID from the URL (between `/d/` and `/view`)
4. Run:
   ```bash
   npx wmill script run f/voice/process-and-delete-audio -d '{"file_url": "FILE_ID"}'
   ```

#### Method B: Windmill UI

1. Navigate to http://localhost:8000
2. Go to Scripts → f/voice/process-and-delete-audio
3. Click "Run"
4. Enter the file ID
5. Check "Delete after processing" if desired
6. Click "Run Script"

### 3. What Happens Next

The script will:
1. **Download** the audio file from Google Drive
2. **Transcribe** using OpenAI Whisper API
3. **Analyze** with Claude to extract tasks and context
4. **Create tasks** in your Notion Tasks database
5. **Create notes** in your Notion Notes database (if needed)
6. **Link** review tasks to notes for contextualization
7. **Delete** the audio file (if requested)

### 4. Review Results

- Check your [Notion Tasks database](https://www.notion.so/183267fb-e1c1-4b3b-a42a-5ac1ab8353eb)
- New tasks appear with:
  - Status: "Inbox"
  - Appropriate contexts/tags
  - Links to related notes for review tasks

## Monitoring & Automation

### Manual Monitoring
Check for new files:
```bash
npx wmill script run f/voice/monitor-drive-folder -d '{"folder_id": "1vUNQV617t5mXHtyYrGro6Q3K-6JCmuUj"}'
```

### Future Automation
A scheduled workflow (`scheduled-voice-processor`) is prepared but requires:
- Proper Google Drive API authentication
- Automatic file deletion implementation

## Example Commands

### Test with sample file:
```bash
# Replace FILE_ID with actual ID from Drive
npx wmill script run f/voice/process-and-delete-audio -d '{"file_url": "1K7BurGdaPaO-O4uM2hEItj_L-_Jc3lgM", "delete_after_processing": true}'
```

### Check Notion database schema:
```bash
npx wmill script run f/voice/check-notion-database-schema -d '{"database_id": "183267fb-e1c1-4b3b-a42a-5ac1ab8353eb"}'
```

### Debug resources:
```bash
npx wmill script run f/voice/debug-resources -d '{}'
```

## Troubleshooting

### Common Issues

1. **"File not accessible"**
   - Ensure file is shared publicly
   - Check the file ID is correct
   - Try accessing the share link in browser first

2. **"Invalid audio format"**
   - Supported formats: .mp4, .m4a, .mp3, .wav
   - Voice Recorder Pro uses .m4a by default

3. **"Task creation failed"**
   - Check Notion API key is valid
   - Verify database IDs in Windmill resources
   - Ensure database has correct properties (Status, Title, Contexts)

### Resource Configuration

All resources are in Windmill under `u/mikewrather/`:
- `problem_free_openai` - OpenAI API key
- `notionhq` - Notion API key  
- `notion_tasks_db` - Tasks database ID
- `notion_notes_db` - Notes database ID
- `google_drive_folder_id` - Drive folder ID
- `google_drive_service_account` - Service account (future use)

## Next Steps

1. **Immediate**: Use the command-line flow for processing voice notes
2. **Short-term**: Set up a simple cron job to check folder periodically
3. **Long-term**: Implement proper Google Drive API authentication for full automation

## Security Notes

- Audio files are public for only seconds during processing
- Delete files immediately after processing for privacy
- Consider implementing JWT authentication for production use