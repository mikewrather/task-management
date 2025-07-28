# Voice Recorder Pro Configuration for Pixel Watch

## App Options

### 1. Easy Voice Recorder Pro ($3.99)
**Best for**: Automatic cloud sync, high quality recordings
- Available on Wear OS Play Store
- Supports auto-upload to Google Drive
- Configurable audio quality
- Background recording support

### 2. Wear Voice Recorder (Free with ads)
**Alternative option**: Basic functionality
- Manual upload required
- Lower audio quality options
- Good for testing the workflow

## Setup Instructions

### Step 1: Install on Pixel Watch
1. Open Play Store on watch
2. Search for "Easy Voice Recorder Pro"
3. Purchase and install ($3.99)
4. Grant microphone permissions

### Step 2: Configure Cloud Sync
1. **On the Watch App**:
   - Open Easy Voice Recorder Pro
   - Swipe left for settings
   - Select "Cloud Upload"
   - Choose "Google Drive"
   - Sign in with your Google account

2. **Set Upload Folder**:
   - In settings, tap "Upload Folder"
   - Create new folder: "Voice Notes - Recorder"
   - Select this folder
   - Enable "Auto Upload on WiFi"

3. **Audio Settings**:
   - Format: M4A (AAC) - best compatibility
   - Quality: High (128 kbps)
   - Sample Rate: 44.1 kHz
   - Mono recording (saves space)

### Step 3: Google Drive Setup
1. **Create Folder Structure**:
   ```
   My Drive/
   ├── Voice Notes - Recorder/     (for audio files)
   ├── Voice Notes - Keep/         (for Keep exports)
   └── Voice Notes - Processed/    (archive)
   ```

2. **Get Folder IDs** (for n8n):
   - Open Google Drive web
   - Navigate to each folder
   - Copy ID from URL: `drive.google.com/drive/folders/{FOLDER_ID}`

### Step 4: Recording Workflow

1. **Quick Recording**:
   - Raise wrist or tap screen
   - Tap recorder complication or open app
   - Tap red record button
   - Speak clearly
   - Tap stop when done

2. **Voice Commands** (if enabled):
   - "Hey Google, open voice recorder"
   - Start recording manually

3. **Auto-sync**:
   - Files upload when watch connects to WiFi
   - Usually during charging
   - Force sync: Open app → Settings → Upload Now

## n8n Configuration

### Update Credentials
Add these to your n8n credentials:
```json
{
  "voiceRecorderFolderId": "your-recorder-folder-id",
  "keepFolderId": "your-keep-folder-id",
  "tasksDbId": "your-notion-tasks-db-id",
  "reviewDbId": "your-notion-review-db-id"
}
```

### Folder Monitoring
The dual-source workflow monitors both:
- Voice Recorder folder for .m4a files
- Keep folder for text/audio files

## Usage Tips

### Best Practices
1. **Keep recordings short** (under 2 minutes)
2. **Pause between thoughts** for better parsing
3. **State context clearly**: "For project X..."
4. **Use trigger words**: "new task", "complete", "note"

### Example Recordings
- "New task: Review quarterly reports by Friday, high priority"
- "Complete task: Send invoice to client"
- "Note for garden project: Research drought-resistant plants"
- "Reminder: Call dentist tomorrow morning"

### Troubleshooting

**Files not uploading**:
- Check WiFi connection on watch
- Verify Google account is signed in
- Check available Google Drive storage
- Try manual upload from app

**Poor transcription quality**:
- Speak closer to watch
- Reduce background noise
- Check audio quality settings
- Ensure language is set to English

**n8n not triggering**:
- Verify folder IDs are correct
- Check Google Drive API permissions
- Look for rate limiting (wait 1 min)
- Check n8n execution logs

## Privacy & Storage

### Data Flow
1. Audio recorded locally on watch
2. Uploaded to your Google Drive
3. Processed by OpenAI Whisper API
4. Analyzed by GPT-4
5. Stored in your Notion workspace

### Storage Management
- Audio files: ~1MB per minute
- Set up auto-archive after processing
- Keep 30 days of recordings
- Delete from Drive after archiving

### Security Notes
- All data stays in your accounts
- Use strong passwords
- Enable 2FA on all services
- Regular audit of access permissions