# Review Workflow for Ambiguous Voice Notes

## Overview

When the AI encounters ambiguous voice notes with low confidence, instead of using a separate review database, we use the existing PARA system:

1. **Create a Note** in the Notes database with the ambiguous content
2. **Create a Task** in the Tasks database to review that note

## Implementation

### For Ambiguous Content

When confidence is low or content is unclear:

```python
# 1. Create note with special properties
note = {
    "title": "Review: [excerpt of transcript]",
    "content": full_transcript,
    "tags": ["needs-review", "voice-note"],
    "confidence": confidence_score,
    "source": "voice-recording"
}
note_url = create_notion_note(note)

# 2. Create review task
task = {
    "title": f"Review ambiguous voice note from {date}",
    "description": f"Review and categorize: {note_url}",
    "priority": "Medium",
    "tags": ["review", "voice-note"],
    "status": "To Do"
}
create_notion_task(task)
```

## Benefits

- **No extra database needed** - Uses existing Notes and Tasks
- **Integrated workflow** - Review tasks appear in your normal task flow
- **Linked content** - Easy to navigate from task to full note
- **PARA compatible** - Fits naturally into the existing system

## Review Process

1. Look for tasks tagged "review" in your Tasks database
2. Click the link to open the full note
3. Read the transcript and decide:
   - Convert to proper task(s)
   - Keep as note with better categorization
   - Create a project or area
   - Delete if not relevant
4. Mark the review task as complete

## Note Properties for Review Items

In the Notes database, review items should have:
- **Title**: "Review: [brief excerpt]"
- **Tags**: Include "needs-review" and "voice-note"
- **Metadata**: Original recording date, confidence score
- **Content**: Full transcript

## Task Properties for Review Items

In the Tasks database, review tasks should have:
- **Title**: "Review ambiguous voice note from [date]"
- **Description**: Link to the note in Notion
- **Priority**: Usually "Medium"
- **Tags**: "review", "voice-note"
- **Due Date**: Optional, based on urgency