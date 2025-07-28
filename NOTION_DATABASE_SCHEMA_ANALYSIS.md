# Notion Database Schema Analysis
*Generated: 2025-07-25*

## Overview

This document provides a comprehensive analysis of the current Notion database structure for the voice task management system, including actual field values and schema details discovered through direct API inspection.

## Database Structure Summary

The system uses 4 main Notion databases implementing the PARA methodology:

1. **Tasks Database** - Primary task management (GTD workflow)
2. **Notes Database** - Knowledge capture and reference materials  
3. **Projects Database** - Time-bound initiatives
4. **Areas Database** - Ongoing responsibilities

## Detailed Schema Analysis

### 1. Tasks Database
**ID**: `183267fb-e1c1-4b3b-a42a-5ac1ab8353eb`
**Title**: "Tasks"
**URL**: https://www.notion.so/183267fbe1c14b3ba42a5ac1ab8353eb

#### Properties (22 total):

**Core Task Properties:**
- **Name** (title) - Task description
- **Description** (rich_text) - Detailed task information
- **Status** (status) - GTD workflow states with 3 groups:
  - **To-do Group**: Inbox, Waiting On, Someday, Next Action
  - **In progress Group**: (0 options currently)
  - **Complete Group**: Completed
- **Date** (date) - Due date
- **Priority** (select) - Options: Low, Medium, High, Urgent, normal
- **Energy** (select) - Options: Low, Medium, High, Extreme
- **Contexts** (multi_select) - Available options:
  - Phone, Computer, Home, Online Shopping, Email
  - Digital Marketing, Mobile Development, Infrastructure
  - voice-created, needs-review, voice, test, auto-processed
- **Owner** (people) - Task assignee

**Relationship Properties:**
- **Project** (relation) → Projects Database (9abc79db-e5c2-4046-b812-585804df2e41)
- **Area** (relation) → Areas Database (f71ab7c6-ac29-4b00-99a1-5eb44156a2bf)
- **Goal** (relation) → Goals Database (07654b24-ee44-473b-a43c-6ac78e49f717)
- **Parent Task** (relation) → Self-reference for task hierarchy
- **Sub-task** (relation) → Self-reference for subtasks
- **Event** (relation) → Events Database (0e341d66-cecf-4521-a875-7af1585dda42)
- **Notes** (relation) → Notes Database (eb339471-752a-4090-b93e-39079a661098)

**Computed Properties:**
- **Goal Area** (rollup) - From Goal relation
- **Parent Date** (rollup) - From Parent Task relation  
- **Project Goal** (rollup) - From Project relation
- **Project Area** (rollup) - From Project relation

**System Properties:**
- **URL** (url) - External links
- **Created** (created_time) - Auto-generated
- **Edited** (last_edited_time) - Auto-generated

#### Current Data:
- **Recent Activity**: 5 voice-created tasks from 2025-07-25
- **Common Status**: Inbox (new voice tasks)
- **Common Contexts**: voice, auto-processed

### 2. Notes Database 
**ID**: `eb339471-752a-4090-b93e-39079a661098`
**Title**: "Notes" (but shows Tasks structure - likely shared with Tasks)

**Note**: This appears to reference the same structure as the Tasks database, suggesting they may be the same database or there's a configuration issue. No recent data found.

### 3. Projects Database
**ID**: `9abc79db-e5c2-4046-b812-585804df2e41`  
**Title**: "Projects"

#### Properties (20 total):

**Core Project Properties:**
- **Name** (title) - Project name
- **Status** (status) - 3 groups:
  - **To-do Group**: Inbox, Not Started
  - **In progress Group**: On Hold, In Progress  
  - **Complete Group**: Completed
- **Priority** (select) - Options: Urgent, High, Medium, Low
- **Timeline** (date) - Project timeline
- **Start Date** (date) - Project start
- **End Date** (formula) - Calculated field

**Relationship Properties:**
- **Area** (relation) → Areas Database
- **Goal** (relation) → Goals Database
- **Tasks** (relation) → Tasks Database
- **Notes** (relation) → Notes Database
- **Meetings** (relation) → Events Database
- **Parent Project** (relation) → Self-reference for project hierarchy
- **Sub-Projects** (relation) → Self-reference for subprojects
- **Related Projects** (relation) → Cross-project relationships
- **References** (relation) → References Database

**Computed Properties:**
- **Goal Area** (rollup) - From Goal relation
- **Progress** (rollup) - Calculated from tasks

**System Properties:**
- **Archive** (checkbox) - Archive status
- **Created** (created_time)
- **Edited** (last_edited_time)

#### Current Data:
- **Active Projects**: Front yard landscaping, SPAs signing, Facebook Events Verification
- **In Progress**: Remote Logging Setup, GCLID Android Debugging
- **Common Status**: Inbox, In Progress

### 4. Areas Database
**ID**: `f71ab7c6-ac29-4b00-99a1-5eb44156a2bf`
**Title**: "Areas"

#### Properties (20 total):

**Core Area Properties:**
- **Name** (title) - Area name  
- **Status** (status) - Same structure as Projects
- **Priority** (select) - Options: Urgent, High, Medium, Low
- **Timeline** (date) - Area maintenance schedule
- **Start Date** (date) - Area establishment date

**Relationship Properties:**
- **Goal** (relation) → Goals Database
- **Tasks** (relation) → Tasks Database  
- **Notes** (relation) → Notes Database
- **Sub-Projects** (relation) → Projects Database
- **Meetings** (relation) → Events Database
- **Related Projects** (relation) → Projects Database
- **References** (relation) → References Database
- **Parent Project** (relation) → Projects Database

**Computed Properties:**
- **Goal Area** (rollup)
- **Progress** (rollup)
- **End Date** (formula)

**System Properties:**
- **Archive** (checkbox)
- **Created** (created_time)
- **Edited** (last_edited_time)

#### Current Data:
- **Active Areas**: [Sleep Worlds] Android, Sleep Worlds, Google, Cycling, Music
- **Common Status**: Inbox

## Field Value Analysis

### Status Values (Standardized across databases):
**GTD Workflow Implementation:**
- **Inbox** - New, unprocessed items
- **Next Action** - Ready to work on
- **Waiting On** - Blocked by external dependencies  
- **Someday** - Future consideration
- **Completed** - Finished items

**Project/Area Specific:**
- **Not Started** - Approved but not begun
- **In Progress** - Currently active
- **On Hold** - Temporarily paused

### Priority Values:
- **Urgent** - Immediate attention required
- **High** - Important, soon
- **Medium** - Normal priority (default)
- **Low** - When time allows

### Energy Values:
- **Extreme** - High focus, complex work
- **High** - Significant concentration needed
- **Medium** - Moderate effort
- **Low** - Light, routine tasks

### Context Values:
**Location-based:**
- Home, Computer, Phone

**Action-based:**  
- Email, Online Shopping

**Domain-based:**
- Digital Marketing, Mobile Development, Infrastructure

**System-generated:**
- voice, voice-created, auto-processed, needs-review, test

## Voice Integration Patterns

### Current Voice Task Creation:
- **Default Status**: Inbox
- **Default Contexts**: ['voice', 'auto-processed']
- **Title Pattern**: "Voice Note: [first 60 chars]..."
- **Content**: Full transcript as page content

### Processing Flow:
1. Voice recording → Google Drive
2. Transcription via Whisper API
3. Task creation in Tasks database
4. Status set to "Inbox" for manual review
5. Contexts tagged with "voice" and "auto-processed"

## Integration Notes

### Database Relationships:
- Tasks can belong to Projects and Areas
- Projects belong to Areas  
- All entities can link to Goals
- Cross-references between Projects
- Task hierarchy via Parent/Sub-task relations

### Current Usage Patterns:
- **Heavy Task Usage**: Primary database for voice input
- **Light Project/Area Usage**: Setup but minimal data
- **Notes Database**: Appears inactive or misconfigured

### API Configuration:
```
NOTION_TASKS_DB=183267fb-e1c1-4b3b-a42a-5ac1ab8353eb
NOTION_NOTES_DB=eb339471-752a-4090-b93e-39079a661098  
NOTION_PROJECTS_DB=9abc79db-e5c2-4046-b812-585804df2e41
NOTION_AREAS_DB=f71ab7c6-ac29-4b00-99a1-5eb44156a2bf
```

## Recommendations for Planning

### Valid Field Values to Use:
1. **Status Options**: Inbox, Next Action, Waiting On, Someday, Completed, Not Started, In Progress, On Hold
2. **Priority Options**: Low, Medium, High, Urgent  
3. **Energy Options**: Low, Medium, High, Extreme
4. **Core Contexts**: Phone, Computer, Home, Email, Online Shopping
5. **Voice Contexts**: voice, auto-processed, voice-created, needs-review

### Workflow Considerations:
- Default new items to "Inbox" status
- Use voice-specific contexts for tracking
- Maintain Project/Area relationships for organization
- Support GTD methodology with status transitions
- Enable both manual and automated processing

### Schema Extensions Needed:
- None - current schema is comprehensive
- Consider clarifying Notes database configuration  
- May need to expand Context options based on usage

---

*This analysis reflects the actual production database schema as of 2025-07-25. Use these exact values and structures when planning system enhancements.*