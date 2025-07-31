# Voice Files Cleanup Guide

**Version**: 1.0  
**Date**: 2025-07-24  
**Integration**: Voice Task Management System

---

## 📋 **Overview**

The Voice Task Management System automatically processes voice recordings and creates Notion tasks, but the original audio files remain in Google Drive. This guide explains how to manage these processed files to maintain organized storage.

### **Why Cleanup Matters**
- **Storage Efficiency**: Processed files accumulate over time (5-10MB+ per month with regular use)
- **Organization**: Separate processed files from new recordings for clarity
- **Security**: Remove old voice files containing potentially sensitive information
- **Performance**: Reduce clutter in Google Drive folder for faster access

---

## 🔧 **Cleanup System Architecture**

### **Processing Tracking**
```
Voice File → Processing → Notion Task → Database Record
    ↓
Cleanup Tracking System
    ↓
Manual Cleanup Guidance
```

### **Key Components**
1. **SQLite Database**: Tracks all processed files with timestamps and metadata
2. **Cleanup Script**: `scripts/cleanup-processed-files.py` provides guidance and statistics
3. **Configuration**: Environment variables control cleanup behavior
4. **Future Integration**: Ready for Google Drive API automation

---

## 🛠️ **Using the Cleanup Tools**

### **1. Check Cleanup Status**
```bash
# View cleanup statistics and recommendations
./scripts/cleanup-processed-files.py --stats

# Expected output:
# 📊 CLEANUP STATISTICS
# Total processed files:       15
# Processed today:              3
# Processed this week:          8
# Files ready for cleanup:      7
```

### **2. List All Processed Files**
```bash
# Show detailed list of all processed files
./scripts/cleanup-processed-files.py --list

# Shows:
# - File IDs with direct Google Drive links
# - Processing timestamps
# - Transcript previews
# - Notion task URLs
```

### **3. Get Cleanup Instructions**
```bash
# Generate manual cleanup guide
./scripts/cleanup-processed-files.py --guide

# Provides:
# - Step-by-step cleanup instructions  
# - Direct links to files in Google Drive
# - Cleanup options (delete, rename, move)
# - Safety recommendations
```

---

## 📝 **Manual Cleanup Process**

Since the current system uses public folder access without Google Drive API authentication, cleanup is currently manual but well-guided:

### **Step 1: Review Files for Cleanup**
```bash
./scripts/cleanup-processed-files.py --guide
```

This shows files that are eligible for cleanup (typically 24+ hours old) with:
- Direct Google Drive links
- Transcript previews for verification
- Associated Notion task URLs

### **Step 2: Access Google Drive**
1. Open the provided Google Drive folder link
2. Locate files using the provided file IDs or transcript previews
3. Verify files are correctly processed by checking corresponding Notion tasks

### **Step 3: Choose Cleanup Method**

**Option A: Delete Files (Recommended)**
- Permanently removes files from Google Drive
- Saves the most storage space  
- Safe since transcripts are preserved in Notion
- Best for: Regular maintenance, storage constraints

**Option B: Rename Files**
- Add "PROCESSED_" prefix to filename
- Keeps files for reference while marking them as processed
- Best for: Verification needs, cautious approach

**Option C: Move to Subfolder** 
- Create a "processed" subfolder in Google Drive
- Move processed files to keep them organized
- Best for: Organization while retaining access

---

## ⚙️ **Configuration Options**

### **Environment Variables** (`.env` file)

```bash
# Enable cleanup tracking in logs
CLEANUP_PROCESSED_FILES=true

# Hours to wait before marking files for cleanup
CLEANUP_DELAY_HOURS=24

# For debugging cleanup process
DEBUG=true
```

### **Configuration Effects**

**CLEANUP_PROCESSED_FILES=false** (Default):
- No cleanup tracking in logs
- Cleanup script still works (reads database)
- Minimal performance impact

**CLEANUP_PROCESSED_FILES=true**:
- Cleanup intent logged for each processed file
- Enables future automation features
- Provides more detailed cleanup guidance

---

## 📊 **Cleanup Statistics & Monitoring**

### **Daily Monitoring**
```bash
# Quick stats check
./scripts/cleanup-processed-files.py

# Integration with main monitoring
./scripts/analyze-voice-runs.py --stats
```

### **Weekly Maintenance**
```bash
# Full cleanup review
./scripts/cleanup-processed-files.py --guide

# Check storage impact
./scripts/cleanup-processed-files.py --stats
```

### **Cleanup Recommendations**

**Files 1-7 days old**:
- Generally safe to keep for verification
- Good for checking transcription accuracy
- Useful if re-processing is needed

**Files 1+ weeks old**:
- Prime candidates for cleanup
- Transcripts safely stored in Notion
- Minimal risk of needing original audio

**Files 1+ months old**:
- Should be cleaned up for storage efficiency
- Very unlikely to need original audio
- High confidence in transcript accuracy

---

## 🔒 **Safety & Data Integrity**

### **Data Safety Guarantees**
- **Transcripts Preserved**: Full transcript text stored in Notion
- **Task Links**: Direct URLs to created tasks for verification
- **Processing History**: Complete SQLite database record
- **Reversible Operations**: Rename/move operations can be undone

### **Best Practices**
1. **Verify Before Cleanup**: Check Notion tasks exist and are accurate
2. **Start Conservative**: Use rename/move before deletion
3. **Keep Recent Files**: Don't cleanup files less than 24 hours old
4. **Backup Database**: The SQLite database contains processing history
5. **Test Process**: Try cleanup on one file before bulk operations

### **Recovery Options**
If cleanup is done accidentally:
- **Check Notion**: Transcripts are safely preserved
- **Review Database**: `data/processed_files.db` has processing history
- **Google Drive Trash**: Deleted files may be recoverable for 30 days

---

## 🐛 **Troubleshooting**

### **Common Issues**

**Cleanup script shows no files**:
```bash
# Check if database exists and has data
ls -la data/processed_files.db
sqlite3 data/processed_files.db "SELECT COUNT(*) FROM processed_files;"
```

**Can't find files in Google Drive**:
- Use direct file links provided by `--guide` option
- Files may be in different folders if moved manually
- Check Google Drive trash if files were accidentally deleted

**Cleanup recommendations seem wrong**:
- Check `CLEANUP_DELAY_HOURS` setting in `.env`
- Verify system time/timezone is correct
- Run with `DEBUG=true` for detailed output

### **Getting Help**
```bash
# Detailed cleanup analysis
DEBUG=true ./scripts/cleanup-processed-files.py --stats

# Check system integration
./scripts/analyze-voice-runs.py --stats

# Review processing logs
tail -100 logs/voice-automation.log | grep cleanup
```

---

## 📚 **Related Documentation**

- **[Scripts Directory](../scripts/README.md)** - Overview of all automation scripts
- **[Feature Specification](../FEATURE_SPECIFICATION.md)** - Complete system documentation
- **[Logging System](../LOGGING_SYSTEM.md)** - Detailed logging documentation
- **[Google Drive Setup](google-drive-setup.md)** - Drive integration configuration

---

**Last Updated**: 2025-07-24  
**Next Review**: After Google Drive API integration implementation

*This guide covers the current manual cleanup system for the voice task management project.*