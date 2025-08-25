#!/bin/bash

echo "Testing Claude from shell script..."
echo "=================================="

# Load .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "1. Environment check:"
echo "   CLAUDE_CODE_OAUTH_TOKEN is: ${CLAUDE_CODE_OAUTH_TOKEN:0:20}..."
echo ""

echo "2. Running Claude directly:"
claude -p "Return only: TEST" --output-format json | head -1

echo ""
echo "3. Running Claude with full path:"
/home/mike/.claude/local/claude -p "Return only: TEST" --output-format json | head -1

echo ""
echo "=================================="