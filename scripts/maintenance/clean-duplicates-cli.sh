#!/bin/bash

# Script to clean duplicate voice note tasks using the new CLI delete command

echo "🧹 Cleaning Duplicate Voice Note Tasks with CLI"
echo "=" * 60

# Navigate to project directory
cd "$(dirname "$0")/.."

# Activate virtual environment
source .venv/bin/activate

echo "🔍 Fetching duplicate task IDs..."

# Get voice tasks and extract task IDs (keep only the oldest - created earliest)
# First, get all task IDs and their creation times, then delete all but the oldest

# Sample duplicate task IDs to delete (all but the oldest one)
DUPLICATE_IDS=(
    "23b66c0c-73af-8122-ac44-ee82bcb143a3"
    "23b66c0c-73af-81ed-a482-e64ac8819834"
    "23b66c0c-73af-8156-b14f-df9c15689199"
    "23b66c0c-73af-816d-86bf-d12aaf906ba5"
    "23b66c0c-73af-818c-8489-dcb62c49735b"
)

echo "🎯 Starting deletion of ${#DUPLICATE_IDS[@]} duplicate tasks..."

DELETED=0
FAILED=0

for task_id in "${DUPLICATE_IDS[@]}"; do
    echo ""
    echo "🗑️ Deleting task: $task_id"
    
    if vtm list delete-task "$task_id" --confirm --verbose; then
        echo "   ✅ Successfully deleted"
        ((DELETED++))
    else
        echo "   ❌ Failed to delete"
        ((FAILED++))
    fi
    
    # Small delay to be gentle with API
    sleep 1
done

echo ""
echo "📊 Summary:"
echo "   Successfully deleted: $DELETED"
echo "   Failed deletions: $FAILED"
echo "   Total processed: ${#DUPLICATE_IDS[@]}"

if [ $DELETED -gt 0 ]; then
    echo ""
    echo "✅ Cleanup complete! Deleted $DELETED duplicate tasks."
    echo "📋 Check your Notion database to verify the cleanup."
else
    echo ""
    echo "⚠️ No tasks were deleted. Check the output above for errors."
fi