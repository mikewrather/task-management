# Notion Voice Commands Reference Guide

## Quick Reference Card

### Most Common Commands

| Command Pattern | Example | Result |
|----------------|---------|---------|
| Add task... | "Add task to review code" | Creates task in Inbox |
| Remind me to... | "Remind me to call dentist tomorrow" | Creates task with date |
| Create project... | "Create project for app redesign" | New project in Projects |
| Take note... | "Take note about API limits" | Creates fleeting note |
| Show me... | "Show me my next actions" | Queries tasks by status |

## Task Management Commands

### Creating Tasks

**Basic Task Creation**
- "Add task [description]"
- "Create task [description]"
- "New task [description]"
- "Todo [description]"

**With Time**
- "Remind me to [task] [time]"
- "[Task] by [date]"
- "[Task] due [date]"
- "Schedule [task] for [date]"

**With Priority**
- "Urgent task [description]"
- "High priority [task]"
- "Low priority [task]"
- "[Task] when I have time"

**With Context**
- "Add task to call [person]" → Phone context
- "Email [person] about [topic]" → Email context
- "When I'm at home [task]" → Home context
- "Buy [item]" → Shopping context

### Examples:
```
"Add task to review pull requests"
"Remind me to submit report by Friday high priority"
"Urgent task fix production bug"
"Call John tomorrow about project when I'm at office"
"Email Sarah about meeting notes"
```

### Updating Tasks

**Status Changes**
- "Mark [task] as complete"
- "Complete [task]"
- "Done with [task]"
- "[Task] is waiting on [person/thing]"
- "Move [task] to someday"

**Property Updates**
- "Make [task] high priority"
- "Change [task] date to [new date]"
- "Add [context] to [task]"
- "Set [task] energy to low"

### Examples:
```
"Mark review code as complete"
"Deploy to production is waiting on approval"
"Make fix bug high priority"
"Change meeting date to next Monday"
```

### Querying Tasks

**By Status**
- "What are my next actions?"
- "Show me inbox items"
- "What am I waiting on?"
- "Someday tasks"

**By Time**
- "What's due today?"
- "Tasks for tomorrow"
- "This week's tasks"
- "Overdue tasks"

**By Property**
- "High priority tasks"
- "Low energy tasks"
- "Phone calls to make"
- "Tasks for [project name]"

### Examples:
```
"What are my next actions for the mobile project?"
"Show me high priority tasks due this week"
"What phone calls do I need to make?"
"Tasks I'm waiting on others for"
```

## Project Management Commands

### Creating Projects
- "Create new project [name]"
- "Start project [name]"
- "New project for [purpose]"
- "Set up project [name]"

### Project Updates
- "Add [task] to [project]"
- "Update [project] status to in progress"
- "Complete [project]"
- "Archive [project]"

### Project Queries
- "Show me active projects"
- "What's the status of [project]?"
- "Tasks for [project]"
- "Projects in [area]"

### Examples:
```
"Create new project website redesign"
"Add research hosting options to website project"
"What's the status of mobile app project?"
"Show me all projects in development area"
```

## Note Taking Commands

### Creating Notes

**Quick Capture**
- "Note [content]"
- "Quick thought [content]"
- "Remember [content]"
- "Jot down [content]"
- "Brain dump [content]"

**Meeting Notes**
- "Meeting notes [meeting name]"
- "Meeting with [person] about [topic]"
- "Team meeting notes"
- "Add to [meeting] notes"

**Learning Notes**
- "I learned [content]"
- "Article notes [topic]"
- "Book notes [book name]"
- "Video notes [topic]"

**Reference/Bookmarks**
- "Bookmark [url/description]"
- "Save link [url]"
- "Reference [description]"
- "Resource for [project/topic]"

### Examples:
```
"Quick thought we should use caching for API"
"Meeting with John discussed new features and timeline"
"I learned Python decorators can be stacked"
"Bookmark AWS Lambda best practices article"
```

### Retrieving Notes
- "Show my notes about [topic]"
- "Recent notes"
- "Notes from [date/period]"
- "Meeting notes this week"
- "Notes in [area]"

### Examples:
```
"Show my notes about database optimization"
"Recent meeting notes"
"Notes from last month about architecture"
"All notes in development area"
```

## Advanced Commands

### Bulk Operations
- "Add three tasks: [task1], [task2], [task3]"
- "Create tasks for [list of items]"
- "Complete all tasks in [project]"

### Complex Queries
- "Next actions that are high priority"
- "Low energy tasks I can do at home"
- "Urgent tasks without dates"
- "Projects without any tasks"

### Planning Commands
- "Plan my day"
- "What should I work on next?"
- "Review weekly tasks"
- "Show me blocked items"

### Templates
- "Create weekly review tasks"
- "Set up new client project"
- "Add standard meeting tasks"

## Natural Language Patterns

### Time Recognition
- Today, tomorrow, yesterday
- This/next [weekday]
- In [X] days/weeks
- By/before/after [date]
- End of day/week/month
- Morning/afternoon/evening
- Specific times (3pm, 15:00)

### Priority Indicators
- **Urgent**: ASAP, urgent, immediately, critical
- **High**: Important, high priority, must do
- **Medium**: Normal, regular (default)
- **Low**: When possible, eventually, someday, maybe

### Context Clues
- **Phone**: Call, ring, phone, contact
- **Email**: Email, send, reply, message
- **Computer**: Code, develop, program, design
- **Home**: House, home, domestic, personal
- **Shopping**: Buy, purchase, order, shop

## Workflow Commands

### Daily Workflow
```
"Show me today's tasks"
"What are my morning tasks?"
"Add lunch break at noon"
"Review end of day tasks"
"Plan tomorrow"
```

### Weekly Review
```
"Show me this week's completed tasks"
"What's in my inbox?"
"Move old inbox items to someday"
"What are next week's priorities?"
"Archive completed projects"
```

### Processing Inbox
```
"Show inbox items"
"Convert [inbox item] to project"
"Make [inbox item] a next action"
"Delete [inbox item]"
"Assign [inbox item] to [project]"
```

## Tips for Effective Voice Commands

### Be Specific
❌ "Add that thing about the meeting"
✅ "Add task to send meeting notes to team"

### Include Key Information
❌ "Call John"
✅ "Call John tomorrow about budget approval"

### Use Natural Language
❌ "Task: Email; Priority: High; Date: Tomorrow"
✅ "High priority email client by tomorrow"

### Batch Similar Items
❌ Multiple separate commands for related tasks
✅ "Add three tasks for project setup: create repo, set up CI, add readme"

## Error Handling

### Ambiguous Commands
If Claude asks for clarification:
- Provide specific project/area names
- Clarify dates with day names
- Specify exact task names for updates

### Common Issues
1. **Duplicate Detection**
   - Claude will ask before creating similar tasks
   - Specify "new" to force creation

2. **Project/Area Assignment**
   - Mention project name in command
   - Or respond to Claude's clarification request

3. **Date Parsing**
   - Use clear date formats
   - Avoid ambiguous terms like "next" without context

## Command Shortcuts

### Quick Capture Mode
Start with action word for fastest processing:
- "Call..." → Phone task
- "Email..." → Email task
- "Buy..." → Shopping task
- "Code..." → Computer task
- "Meeting..." → Creates meeting note

### Batch Processing
- "Inbox review" → Shows all inbox items
- "Daily planning" → Shows today + next actions
- "Weekly cleanup" → Archives completed, shows inbox

### Smart Defaults
- No date specified → Goes to inbox
- No priority → Medium priority
- No project → Standalone task
- No area → Prompts if unclear

---

*This reference guide provides comprehensive voice command patterns for the Notion PARA system. Commands are processed naturally - exact wording is not required.*