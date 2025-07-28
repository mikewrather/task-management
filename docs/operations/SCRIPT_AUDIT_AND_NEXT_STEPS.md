# Script Audit and Next Steps

## Script Categorization

### 🌪️ Production Windmill Scripts (Deploy & Keep)
**Purpose**: Core voice processing functionality in production

- `windmill/scripts/f/voice/process-and-delete-audio-with-logging.ts` ✅ **PRODUCTION**
  - Complete voice pipeline with detailed logging
  - Uses correct Notion property names
  - **Status**: Working and tested

- `windmill/scripts/f/voice/scan-and-process-voice-files.ts` ✅ **PRODUCTION**  
  - Automatic folder scanning and batch processing
  - **Status**: Created but needs deployment

- `windmill/scripts/f/voice/create-test-voice-task.ts` ✅ **PRODUCTION**
  - Simple task creation for testing
  - **Status**: Working with correct property names

### 🧪 Development/Test Scripts (Local Only - Can Delete)
**Purpose**: Development iterations and testing - no longer needed

- `test-folder-scan.sh` ❌ **DELETE** - Local test, proven concept works
- `test-notion.sh` ❌ **DELETE** - Local test, proven working  
- `test-voice-flow-direct.sh` ❌ **DELETE** - Local test, proven working
- All `windmill/scripts/f/voice/test-*.ts` ❌ **DELETE** - Development iterations
- All `windmill/scripts/f/voice/debug-*.ts` ❌ **DELETE** - Debug scripts

### 🛠️ Utility Scripts (Keep & Organize)
**Purpose**: Project maintenance and organization

- `scripts/organize-*.sh` ✅ **KEEP** - Organization utilities
- `scripts/voice-monitor-cron.sh` ✅ **KEEP** - Cron monitoring option
- `archives/setup-scripts/*.sh` ✅ **KEEP** - Historical reference

### 🔄 Legacy/Duplicate Scripts (Archive or Delete)
**Purpose**: Old versions that have been superseded

- `windmill/scripts/f/voice/process-and-delete-audio.ts` ❌ **DELETE** - Old version without logging
- `windmill/scripts/f/voice/process-drive-audio*.ts` ❌ **DELETE** - Multiple old iterations
- `windmill/scripts/f/voice/analyze_transcript.ts` ❌ **DELETE** - Standalone component, now integrated
- `windmill/scripts/f/voice/transcribe_whisper.ts` ❌ **DELETE** - Standalone component, now integrated

## Next Steps for Enhancement

### 1. 🎯 Improve Context Analysis (HIGH PRIORITY)

**Issue**: Voice note "I need to make sure that all of the trees in the backyard are being watered adequately" should have derived better context.

**Goal**: Use existing Notion data to intelligently categorize tasks.

**Implementation Plan**:
1. **Query Existing Notion Data**:
   ```typescript
   // Fetch existing projects and areas from Notion
   const projects = await queryNotionDatabase(projectsDbId);
   const areas = await queryNotionDatabase(areasDbId);
   ```

2. **Semantic Matching**:
   ```typescript
   // Use Claude to match transcript to existing categories
   const analysis = await analyzeWithContext(transcript, {
     existingProjects: projects.map(p => p.title),
     existingAreas: areas.map(a => a.title),
     existingContexts: existingTasks.flatMap(t => t.contexts)
   });
   ```

3. **Smart Assignment**:
   - "trees in backyard" → Area: "Home Maintenance" 
   - "watering" → Project: "Garden Care"
   - Auto-suggest new areas/projects if no match

### 2. 🔔 Proper Google Drive Event Subscription (HIGH PRIORITY)

**Issue**: Currently using folder scraping. Should use proper Google Drive API with webhooks.

**Goal**: Real-time file detection without polling.

**Implementation Plan**:
1. **OAuth 2.0 Setup**:
   ```bash
   # Set up proper Google Drive API credentials
   # Configure OAuth flow for persistent authentication
   ```

2. **Webhook Subscription**:
   ```typescript
   // Subscribe to Drive folder changes
   await drive.files.watch({
     fileId: folderId,
     requestBody: {
       type: 'webhook',
       address: 'https://your-webhook-endpoint.com/drive-events'
     }
   });
   ```

3. **Event Processing**:
   ```typescript
   // Process webhook events for new .m4a files
   // Automatically trigger voice processing pipeline
   ```

### 3. 🧹 Repository Cleanup (IMMEDIATE)

**Actions to take**:

1. **Delete test scripts**:
   ```bash
   rm test-*.sh
   rm windmill/scripts/f/voice/test-*.ts
   rm windmill/scripts/f/voice/debug-*.ts
   ```

2. **Remove duplicate/old scripts**:
   ```bash
   rm windmill/scripts/f/voice/process-drive-audio*.ts
   rm windmill/scripts/f/voice/analyze_transcript.ts
   rm windmill/scripts/f/voice/transcribe_whisper.ts
   ```

3. **Keep only production scripts**:
   - `process-and-delete-audio-with-logging.ts`
   - `scan-and-process-voice-files.ts`
   - `create-test-voice-task.ts`

## Current System Status

### ✅ What Works
- **Voice → Text**: OpenAI Whisper transcription (perfect accuracy)
- **Text → Tasks**: Notion API integration with correct property names
- **End-to-End Flow**: Complete pipeline from audio file to Notion task
- **Logging**: Detailed step-by-step logging for debugging

### 🔧 What Needs Improvement
- **Context Intelligence**: Better area/project assignment using existing Notion data
- **Automation**: Real-time file detection instead of manual/polling
- **Cleanup**: Remove development artifacts and test scripts

### 📋 Recommended Next Actions

1. **IMMEDIATE**: Clean up repository (delete test scripts)
2. **SHORT-TERM**: Implement context analysis using existing Notion data  
3. **MEDIUM-TERM**: Set up Google Drive webhook integration
4. **LONG-TERM**: Add Claude-powered task categorization and smart context assignment

## Final Production Architecture

```
Voice Recording (Watch)
        ↓
Google Drive (with webhooks)
        ↓
Windmill Webhook Handler
        ↓
Voice Processing Pipeline
    ├── Transcribe (Whisper)
    ├── Analyze Context (Claude + Notion data)
    ├── Smart Categorization
    └── Create Tasks (Notion API)
```

This will provide a fully automated, intelligent voice-to-task system with proper context awareness.