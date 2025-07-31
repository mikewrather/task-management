# Voice Task Manager - User Guide

**Version**: 2.0  
**Last Updated**: 2025-07-31

## 🎯 Overview

The Voice Task Manager automatically converts your voice recordings into organized tasks in Notion. Simply record a voice note on your mobile device, and within 5 minutes it will be transcribed, intelligently categorized, and added to your task management system.

## 🚀 Quick Start

### 1. Record a Voice Note
- Use **Voice Recorder Pro** (iOS) or **Just Press Record** (iOS)
- Speak clearly and mention what you need to do
- The app will sync to Google Drive automatically

### 2. Automatic Processing
- The system checks for new recordings every 5 minutes
- Your voice is transcribed using OpenAI Whisper
- Claude AI analyzes and categorizes your task
- Tasks are created in your Notion workspace

### 3. Check Your Tasks
- Open Notion to see your new tasks
- Tasks are automatically assigned to projects and areas
- Desktop notifications confirm successful processing

## 🎤 Recording Best Practices

### Single Task
```
"Call the dentist to schedule my cleaning appointment"
```

### Multiple Tasks (NEW!)
```
"I need to call the plumber about the kitchen sink, 
schedule my dentist appointment, 
and pick up groceries on the way home"
```
→ Creates 3 separate tasks with appropriate categorization

### Task with Context
```
"For the Sleep Worlds project, I need to set up 
the Android emulator for testing the Adapty migration"
```
→ Automatically assigns to "Sleep Worlds" project

### Priority Tasks
```
"Urgent: Submit the tax documents by end of day"
```
→ Sets high priority based on "urgent" keyword

## 📝 Task Organization

### Automatic Categorization
The AI analyzes your tasks and:
- **Assigns Projects**: Matches to existing projects by name/context
- **Sets Areas**: Broader categories like Work, House, Health
- **Adds Contexts**: @home, @office, @computer, @phone
- **Sets Priority**: Based on urgency keywords

### PARA Method
Tasks are organized using the PARA methodology:
- **Projects**: Specific outcomes with deadlines
- **Areas**: Ongoing responsibilities
- **Resources**: Reference materials (created as Notes)
- **Archive**: Completed items

## 🔧 Command Line Interface

### Process Voice Files Manually
```bash
vtm process
```

### Query Your Tasks
```bash
# List all tasks
vtm query tasks

# Filter by status
vtm query tasks --status "In Progress"

# Filter by project
vtm query tasks --project "Sleep Worlds"

# Filter by priority
vtm query tasks --priority urgent
```

### Export Data
```bash
# Export to JSON
vtm export --format json

# Export to CSV
vtm export --format csv --output tasks.csv

# Export to Markdown
vtm export --format markdown
```

### Other Commands
```bash
vtm status        # Check system health
vtm cleanup       # Manage processed files
vtm archive       # Archive old tasks
vtm notify --test # Test notifications
```

## 🔔 Notifications

### Desktop Notifications
- **Success**: Shows task name and project assignment
- **Error**: Alerts you to processing failures
- **Daily Summary**: Overview of tasks processed (optional)

### Email Notifications (Optional)
Configure in `.env` file:
```env
NOTIFICATIONS_EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_USER=your-email@gmail.com
NOTIFICATION_EMAIL=your-email@gmail.com
```

## 🎨 Advanced Features

### Multi-Task Processing
The system now extracts ALL tasks from a single recording:
- Each task is independently categorized
- Tasks can go to different projects/areas
- Maintains context between related tasks

### Smart Categorization
Claude AI uses:
- Your existing projects and areas
- Recent task patterns
- Contextual keywords
- Natural language understanding

### Storage Backends
1. **Notion**: Primary task storage with full PARA support
2. **GraphRAG**: Knowledge graph for relationships (beta)
3. **SQLite**: Processing history and duplicate prevention

## 🔍 Troubleshooting

### Tasks Not Appearing
1. Check if cron is running: `crontab -l`
2. Check logs: `tail -f logs/voice-automation.log`
3. Verify API keys in `.env` file
4. Run manual test: `vtm process`

### Poor Transcription
- Speak clearly and minimize background noise
- Keep recordings under 2 minutes
- Use a good quality microphone
- Avoid multiple speakers

### Wrong Categorization
- Be specific about project names
- Mention area/context explicitly
- Check existing project names in Notion
- Review Claude's reasoning in logs

### Notification Issues
- Ensure desktop notifications are enabled
- Check D-Bus service (Linux)
- Verify notification permissions
- Test with: `vtm notify --test`

## 📊 Usage Tips

### Daily Workflow
1. **Morning**: Record tasks during commute
2. **Throughout Day**: Capture ideas immediately
3. **Evening**: Review processed tasks in Notion
4. **Weekly**: Clean up old audio files

### Best Practices
- Keep recordings focused and clear
- Mention project/area names explicitly
- Use priority keywords when needed
- Group related tasks in one recording

### What to Say
✅ **Good Examples**:
- "For the Sleep Worlds project, implement user authentication"
- "Call dentist tomorrow morning to schedule cleaning"
- "Buy milk, eggs, and bread at grocery store"
- "Urgent: Submit expense report before Friday"

❌ **Avoid**:
- Vague requests: "That thing I mentioned yesterday"
- Too many details: Long explanations
- Background conversations
- Multiple languages in one recording

## 🎆 What's New

### Version 2.0 (July 2025)
- 🎉 **Multi-task extraction** from single recordings
- 🤖 **Claude AI integration** for smart categorization
- 🦾 **GraphRAG support** for knowledge graphs
- 📦 **Modern Python package** with UV
- 🔔 **Enhanced notifications** with multiple channels
- 🧑‍💻 **90+ debug tools** for troubleshooting

## 📞 Getting Help

### Resources
- **Documentation**: `/docs` folder
- **Logs**: `logs/voice-automation.log`
- **Debug Tools**: `scripts/debug/`
- **Configuration**: `.env` file

### Common Issues
- **No tasks created**: Check API keys and network
- **Duplicate tasks**: System prevents this automatically
- **Wrong project**: Be more specific in recording
- **Missing notifications**: Check system settings

### Support
- Check logs for detailed error messages
- Use debug scripts for troubleshooting
- Review CLAUDE_LOG.md for development history
- Consult API documentation for integrations

---

**Remember**: The system is designed to be invisible - just speak your tasks and they'll appear in Notion! 🎩✨