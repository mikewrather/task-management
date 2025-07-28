# Google Drive Setup - Complete Guide

This guide consolidates all Google Drive setup information for the voice task management system.

## Current Configuration

- **Service Account Email**: voice-task-automation@mw-proj-453419.iam.gserviceaccount.com
- **Project ID**: mw-proj-453419
- **Drive Folder ID**: 1vUNQV617t5mXHtyYrGro6Q3K-6JCmuUj
- **Folder Status**: Shared with service account ✓

## Setup Status
- [x] Service account created in Google Cloud Console
- [x] Service account key downloaded (stored as mw-proj-453419-10023e82b017.json)
- [x] Key file added to .gitignore
- [x] Google Drive folder shared with service account
- [x] Windmill resource created as `google_drive_service_account`

## Current Workflow (Temporary Public Access)

Due to API authentication complexity, we use a temporary public access pattern:

1. **Record**: Voice note on Apple Watch syncs to Google Drive
2. **Share**: Temporarily make file public (manual or automated)
3. **Process**: Run `npx wmill script run f/voice/process-and-delete-audio -d '{"file_url": "FILE_ID"}'`
4. **Delete**: Remove file after processing (manual currently)

This keeps files public for only seconds during processing.


## Full API Setup Guide (For Future Implementation)

## Setting up Google Drive API Access

### 1. Enable Google Drive API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Go to "APIs & Services" → "Enable APIs and services"
4. Search for "Google Drive API" and enable it

### 2. Create Service Account (Recommended for Automation)
1. In Google Cloud Console, go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in:
   - Service account name: `voice-task-automation`
   - Service account ID: (auto-generated)
   - Description: "Service account for voice task management"
4. Click "Create and Continue"
5. Skip the optional steps and click "Done"

### 3. Create and Download Service Account Key
1. Click on the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose JSON format
5. Download the key file (keep it secure!)

### 4. Share Google Drive Folder with Service Account
1. Open the JSON key file and find the `client_email` field
2. Copy the email (looks like: `voice-task-automation@your-project.iam.gserviceaccount.com`)
3. Go to your Google Drive folder
4. Click Share
5. Add the service account email as a viewer/editor
6. Click "Send"

### 5. Configure in Windmill
1. Create a new Google Drive resource in Windmill
2. Add the service account credentials:
   ```json
   {
     "type": "service_account",
     "project_id": "your-project-id",
     "private_key_id": "...",
     "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
     "client_email": "voice-task-automation@your-project.iam.gserviceaccount.com",
     "client_id": "...",
     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
     "token_uri": "https://oauth2.googleapis.com/token",
     "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
     "client_x509_cert_url": "..."
   }
   ```

## Alternative: OAuth2 with User Account
If you prefer using your personal Google account:

1. In Google Cloud Console, create OAuth2 credentials
2. Set up redirect URI for Windmill
3. Use OAuth2 flow to authorize access

## Environment Variables for Local Testing
```bash
# .env file
GOOGLE_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}'
GOOGLE_DRIVE_FOLDER_ID='1vUNQV617t5mXHtyYrGro6Q3K-6JCmuUj'
```

## Test the Setup
Once configured, you should be able to:
- List files in the folder
- Download audio files
- Process them through the voice pipeline

## Security Notes
- Never commit service account keys to git
- Store credentials securely in Windmill resources
- Use least-privilege access (viewer for read-only)
- Rotate keys periodically