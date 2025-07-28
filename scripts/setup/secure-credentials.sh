#!/bin/bash
# Script: secure-credentials.sh
# Purpose: Set up secure credential management for scripts
# Context: Created to avoid exposing credentials in conversations
# Created: 2025-01-19
# Author: Security-focused setup
# Usage: source ./scripts/setup/secure-credentials.sh
# Dependencies: None

echo "🔒 Secure Credential Setup"
echo "========================="

# Create secure credentials file if it doesn't exist
CREDS_FILE="$HOME/.env.task-management"

if [ ! -f "$CREDS_FILE" ]; then
    echo "Creating secure credentials file..."
    cat > "$CREDS_FILE" << 'EOF'
# Task Management Credentials
# NEVER commit this file to git
# NEVER share these values in chat

# n8n Credentials
N8N_USERNAME=""
N8N_PASSWORD=""
N8N_CLOUD_API_KEY=""

# Google Drive Folder IDs
VOICE_RECORDER_FOLDER_ID=""
KEEP_FOLDER_ID=""

# OpenAI
OPENAI_API_KEY=""

# Notion
NOTION_API_TOKEN=""
NOTION_REVIEW_DB_ID=""
EOF
    chmod 600 "$CREDS_FILE"
    echo "✅ Created $CREDS_FILE with secure permissions (600)"
    echo ""
    echo "📝 Next steps:"
    echo "1. Edit $CREDS_FILE and add your credentials"
    echo "2. Source it: source $CREDS_FILE"
    echo "3. Add to .bashrc: echo 'source $CREDS_FILE' >> ~/.bashrc"
else
    echo "✅ Credentials file already exists: $CREDS_FILE"
fi

# Create .gitignore entry
if ! grep -q ".env.task-management" .gitignore 2>/dev/null; then
    echo ".env.task-management" >> .gitignore
    echo "✅ Added credentials file to .gitignore"
fi

echo ""
echo "🔐 Security Tips:"
echo "- Never share credentials in chat"
echo "- Use 'read -s' for password prompts"
echo "- Enable 2FA on all services"
echo "- Rotate credentials regularly"