# Notion PARA Workflow Documentation

## Overview

This document defines the workflow for interacting with the Notion PARA (Projects, Areas, Resources, Archive) system through Claude and MCP. It serves as the authoritative guide for task management, note-taking, and information organization.

## System Architecture

### Core Components

1. **Projects** - Time-bound initiatives with specific outcomes
2. **Areas** - Ongoing responsibilities requiring maintenance
3. **Resources** - Knowledge resources and reference materials
4. **Archive** - Past projects and reference materials

### Database Structure

#### Tasks Database (Primary)
**ID**: `183267fb-e1c1-4b3b-a42a-5ac1ab8353eb`

**Properties**:
- `Name` (title) - Task description
- `Status` (status) - GTD workflow states:
  - Inbox
  - Next Action
  - Waiting On
  - Someday
  - Completed
- `Project` (relation) - Link to Projects database
- `Date` (date) - Due date
- `Priority` (select) - Low, Medium, High, Urgent
- `Energy` (select) - Low, Medium, High, Extreme
- `Contexts` (multi_select) - Phone, Computer, Home, Email, etc.
- `Area` (relation) - Link to Areas database
- `Goal` (relation) - Link to Goals database

#### Projects Database
**ID**: `9abc79db-e5c2-4046-b812-585804df2e41`

**Properties**:
- `Name` (title)
- `Status` (status) - Inbox, Not Started, In Progress, On Hold, Completed
- `Priority` (select) - Urgent, High, Medium, Low
- `Timeline` (date)
- `Tasks` (relation)
- `Area` (relation)
- `Goal` (relation)

#### Areas Database
**ID**: `f71ab7c6-ac29-4b00-99a1-5eb44156a2bf`

**Properties**:
- `Name` (title)
- `Type` (select) - Business, Work, Personal
- Related databases: Tasks, Projects, Goals, Notes, Topics

## Workflow Instructions

### Processing Voice Commands

#### Quick Capture (Default Behavior)
When receiving voice input without specific context:
1. Create a new task in the Tasks database
2. Set Status to "Inbox"
3. Parse for natural language dates and priorities
4. Extract any mentioned contexts or areas

Example:
```
"Call dentist tomorrow about appointment"
→ Task: "Call dentist about appointment"
→ Date: Tomorrow
→ Context: Phone
→ Status: Inbox
```

#### Project Creation
Triggered by keywords: "new project", "start project", "create project"
```
"Create new project for website redesign"
→ Project: "Website redesign"
→ Status: Not Started
→ Area: (prompt for area if unclear)
```

#### Note Taking
Triggered by keywords: "note", "remember", "document", "write down"
```
"Note that the API key is stored in the env file"
→ Note: "API key location"
→ Content: "The API key is stored in the env file"
→ Type: Fleeting
```

### Processing Patterns

#### Time References
- "today" → Current date
- "tomorrow" → Current date + 1
- "next week" → Current date + 7
- "next [day]" → Next occurrence of that day
- "in X days" → Current date + X

#### Priority Indicators
- "urgent", "asap", "immediately" → Urgent
- "important", "high priority" → High
- "when I get time", "someday" → Low
- Default → Medium

#### Context Detection
- "call", "phone" → Phone
- "email", "send", "reply" → Email
- "buy", "shop", "order" → Online Shopping
- "at home", "house" → Home
- "code", "develop", "program" → Computer

### Advanced Operations

#### Weekly Review Process
1. Query all tasks with Status = "Inbox"
2. For each inbox item:
   - Assign to project or convert to project
   - Set appropriate status (Next Action, Waiting On, Someday)
   - Add contexts and energy levels
   - Set realistic dates

#### Project Planning
1. Create project in Projects database
2. Break down into tasks
3. Link tasks to project
4. Set task dependencies using Parent Task relation
5. Assign priorities and dates

#### Knowledge Management
For non-actionable information:
1. Determine type:
   - Fleeting Note - Quick thoughts, temporary
   - Literature Note - From books, articles
   - Permanent Note - Processed, refined ideas
   - Reference - External resources
2. Create in appropriate database
3. Link to relevant Areas, Topics, or Projects

## Voice Command Examples

### Task Creation
- "Add task to review pull requests" → Simple task
- "Remind me to call John tomorrow at 2pm high priority" → Task with date and priority
- "Create recurring task to check backups every Monday" → Recurring task

### Project Management
- "Show me all tasks for the mobile app project" → Query with filter
- "What's next on my website redesign?" → Project-specific next actions
- "Mark deploy to production as complete" → Status update

### Information Retrieval
- "What are my next actions?" → Status filter query
- "Show me all high energy tasks" → Energy filter query
- "What's due this week?" → Date range query

### Note Taking
- "Take a note about the meeting with Sarah" → Create meeting note
- "Add to my learning notes about Python decorators" → Append to existing note
- "Create a reference for the AWS documentation link" → Reference creation

## Integration with Claude

When processing requests through Claude with MCP:

1. **Always check current date first** - Use `date` command to establish temporal context
2. **Use specific database IDs** - Reference the IDs listed above
3. **Batch operations** - Use concurrent tool calls when possible
4. **Verify before creating** - Search for existing items before creating duplicates
5. **Maintain relations** - Always link tasks to projects/areas when clear

## Error Handling

- If project/area is unclear, ask for clarification
- If date parsing fails, default to no date (inbox processing will handle)
- If duplicate task detected, update existing rather than create new
- For ambiguous commands, show interpretation and confirm

## Future Enhancements

### Planned Features
1. **Smart Natural Language Processing**
   - Better context detection from conversation history
   - Learning user patterns and preferences
   - Automatic project/area assignment based on content

2. **Advanced Queries**
   - Complex filters combining multiple properties
   - Saved views and quick filters
   - Time-based analytics and reporting

3. **Automation**
   - Recurring task templates
   - Project templates with standard tasks
   - Automatic status transitions based on rules

4. **Integration Extensions**
   - Calendar sync for dated tasks
   - Email integration for task creation
   - Slack/Discord notifications for updates

## Maintenance

### Daily
- Process inbox items
- Review today's tasks
- Update task statuses

### Weekly
- Full inbox review
- Project status updates
- Archive completed items
- Review upcoming week

### Monthly
- Area health check
- Resource organization
- Archive old projects
- Goal progress review

---

*This document serves as the primary reference for the Notion PARA workflow. It should be updated as the system evolves and new patterns emerge.*