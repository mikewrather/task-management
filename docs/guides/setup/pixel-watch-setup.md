# Pixel Watch Voice Recording Setup Guide

## Quick Start: Easiest Method (Google Keep)

### On Your Pixel Watch:
1. **Install Google Keep** from Play Store on watch
2. Open Keep
3. Tap the microphone button
4. Speak your task/note
5. It auto-syncs when connected to phone

### On Your Phone:
1. Open Google Keep app
2. Your voice notes appear with transcription
3. Audio files are stored in Google Drive under "Keep" folder

### Automation Setup:
- Use IFTTT or Zapier to monitor Keep notes
- OR use the n8n workflow to process Keep exports

## Alternative Methods

### Method 1: Voice Recorder Apps with Auto-Upload

**Recommended App**: "Easy Voice Recorder Pro" ($3.99)
- Install on watch via Play Store
- Configure auto-upload to Google Drive
- Set upload folder in app settings
- Records save as .m4a files

### Method 2: Google Assistant + Routines

1. **Create Google Assistant Routine**:
   - Trigger: "Hey Google, task note"
   - Action: "Take a voice note"
   - Save to: Google Drive

2. **On Watch**:
   - Say "Hey Google, task note"
   - Speak your task
   - Auto-saves to Drive

### Method 3: Wear OS Voice Recorder + Tasker

**Requirements**:
- Tasker app on phone ($3.49)
- AutoWear plugin ($1.99)
- Join app (for cloud sync)

**Setup**:
1. Install apps on phone
2. Create Tasker profile:
   ```
   Event: AutoWear > App > Voice Recorder > Stopped
   Task: 
   1. List Files (Dir: /sdcard/Recordings)
   2. For Each (%file in %files)
   3. Upload to Drive
   4. Delete local file
   ```

## Voice Command Best Practices

### Clear Task Formats:
- "Complete task [name]"
- "New task: [description] for [project]"
- "Add note: [content]"
- "Tomorrow: [task description]"

### Examples:
- "Complete water the plants"
- "New task: Buy groceries for dinner party"
- "Add note: Consider new garden layout for spring"
- "Tomorrow: Call dentist for appointment"

### Avoid:
- Long pauses (creates multiple sentences)
- Background noise
- Unclear project references

## Troubleshooting

### Voice notes not syncing:
1. Check Wear OS app on phone
2. Ensure Bluetooth is connected
3. Force sync: Settings > System > Disconnect & Reset > Sync now

### Audio quality issues:
- Hold watch closer to mouth
- Speak clearly and at normal pace
- Avoid windy environments

### File format issues:
- Most apps save as .m4a (supported)
- If .opus format, may need conversion

## Testing Your Setup

1. **Record Test Note**:
   "New task: Test voice recording system"

2. **Verify Sync**:
   - Check Google Drive folder
   - File should appear within 1-2 minutes

3. **Run Pipeline Test**:
   ```bash
   python test-voice-pipeline.py process test-recording.m4a
   ```

## Tips for Daily Use

1. **Morning Routine**:
   - Review yesterday's captures
   - Process review queue in Notion

2. **Throughout Day**:
   - Quick captures for any thought
   - Don't worry about perfect phrasing

3. **Evening Review**:
   - Check all tasks were processed
   - Clear ambiguous items

## Battery Optimization

- Voice recording uses minimal battery
- Sync happens when charging
- Keep recordings under 2 minutes each

## Privacy Notes

- Recordings stored in your Google Drive
- Processed by OpenAI (Whisper + GPT-4)
- Consider sensitive information
- Set up private Notion workspace