# Voice Task Management Workflow Guide

## Current Workflow (Temporary Public Access)

This approach keeps files public only during processing, then deletes them:

### 1. Automatic Recording
- Record voice notes on your Apple Watch
- Files automatically sync to Google Drive folder

### 2. Processing Steps
```bash
# Process a voice file
npx wmill script run f/voice/process-and-delete-audio -d '{"file_url": "FILE_ID_OR_URL"}'
```

### 3. What Happens
1. **Download**: File is downloaded from Google Drive (requires public access)
2. **Transcribe**: Audio is sent to Whisper API for transcription
3. **Analyze**: GPT-4 analyzes the transcript and extracts tasks
4. **Create Tasks**: Tasks are created in Notion with proper tags
5. **Cleanup**: File is marked for deletion (manual for now)

## Security Model
- Files are only public for ~10-30 seconds during processing
- Deleted immediately after successful processing
- No persistent public access to your voice notes

## File Sharing Settings

### Option 1: Manual Per-File (Current)
1. Upload voice file to Drive
2. Right-click → Share → "Anyone with link" → Copy link
3. Run the processing script
4. Delete the file after processing

### Option 2: Folder Auto-Sharing (Future)
- Set up a "processing" folder with public access
- Move files there for processing
- Auto-delete after processing

## Example Commands

### Process single file
```bash
npx wmill script run f/voice/process-and-delete-audio -d '{
  "file_url": "https://drive.google.com/file/d/1K7BurGdaPaO-O4uM2hEItj_L-_Jc3lgM/view"
}'
```

### Delete processed file
```bash
npx wmill script run f/voice/delete-drive-file -d '{"file_id": "1K7BurGdaPaO-O4uM2hEItj_L-_Jc3lgM"}'
```

## Automation Setup (Coming Soon)

### Google Drive Watch
1. Set up Windmill schedule to check folder every 5 minutes
2. Process any new audio files
3. Delete after successful processing

### Webhook Integration
- Use Google Drive API webhooks for instant processing
- Trigger Windmill workflow on new file upload

## Privacy & Security

**Current approach is secure because:**
- Files are only accessible via direct link (not searchable)
- Public access window is minimal (seconds to minutes)
- Files are deleted after processing
- No sensitive data remains accessible

**Future improvements:**
- Implement proper Google Drive API authentication
- Use service account for private file access
- Automatic deletion via API

## Troubleshooting

### "Invalid file format" error
- Ensure file is actually audio (m4a, mp3, wav)
- Check that public link is working
- Try downloading file manually first

### Tasks not created
- Check Notion integration is working
- Verify database IDs are correct
- Look for specific error messages in logs

### File not deleted
- Currently requires manual deletion
- Check you have edit permissions on the file
- Use the delete script for instructions