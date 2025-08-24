**Voice Note Task Management System Architecture**

---

### 🌍 Background & Rationale

Managing tasks and notes by voice is an intuitive and efficient way to reduce friction in busy or mobile workflows. Typing tasks manually—especially from a smartwatch—is slow, distracting, and often leads to lost ideas. A voice-first pipeline addresses this by enabling:

* On-the-go, low-friction task entry
* Post-hoc transcription and structured task extraction
* Categorization based on existing task/project context
* Full integration with existing task systems via API

The advent of accurate speech-to-text models (e.g., Whisper), reliable LLMs (e.g., GPT-4), and customizable automation platforms (e.g., n8n) makes it feasible to build a robust system that captures voice intent and turns it into meaningful, categorized updates.

---

### 🎯 Goals

1. **Hands-free capture of structured ideas** using natural voice input from a Pixel Watch.
2. **High transcription accuracy** via state-of-the-art speech recognition.
3. **Full context-awareness** for task categorization and updates.
4. **Human-readable and editable task system**, integrated with Notion.
5. **Long-form voice entry support**, including multi-task updates and note creation.
6. **Seamless offline use**, with syncing when online.
7. **Low-maintenance architecture**, with extensibility for chat and AI assistant workflows.

---

### ⚖️ Considered Options

#### Voice Capture

* **Pixel Watch Sound Recorder**: native and offline-friendly.
* **Otter.ai**: higher-quality ASR but requires connectivity and lacks automation hooks.
* **Custom Wear App**: too much overhead.

**✅ Chosen**: *Pixel Watch + Google Drive auto-sync* for simplicity and offline capture.

#### Transcription (ASR)

* **Google Speech-to-Text**: fast but expensive and less accurate for long-form.
* **AssemblyAI**: strong features but pricey at scale.
* **OpenAI Whisper**: state-of-the-art accuracy, punctuation, and support for self-hosting.

**✅ Chosen**: *Whisper (OpenAI API version)*

#### Task System

* **Obsidian**: markdown-based, powerful, local-first. But requires plugin management and scripting.
* **Notion**: relational DBs, good UI, robust API, cloud-native, LLM-friendly.
* **Neo4j/Logseq**: powerful graph model but high-maintenance.

**✅ Chosen**: *Notion* for low-maintenance cloud structure and easy GUI/API access.

#### Orchestration

* **Zapier**: no real LLM/AI support, too limited.
* **Pipedream**: capable, but not as visual.
* **n8n**: programmable, open source, supports HTTP/LLM/nodes, best trade-off.

**✅ Chosen**: *n8n* for visual, programmable automation.

---

### 🛠️ Components

| Component     | Tool                         | Description                                                             |
| ------------- | ---------------------------- | ----------------------------------------------------------------------- |
| Voice Capture | Pixel Watch Sound Recorder   | Captures voice notes with offline support                               |
| Cloud Sync    | Google Drive                 | Auto-upload once online                                                 |
| Orchestrator  | n8n (hosted or self-managed) | Automates the entire pipeline                                           |
| ASR           | OpenAI Whisper API           | Converts voice to text                                                  |
| Task Store    | Notion                       | Main UI & database for tasks, notes, projects                           |
| LLM           | OpenAI GPT-4 or Claude       | Interprets voice-to-text using context, returns structured task updates |
| Optional UI   | ChatGPT or custom assistant  | Voice chat with your task system                                        |

---

### ✅ Flow Breakdown

#### 1. **Voice Note Capture**

* Device: Pixel Watch
* Format: .m4a or .wav
* Storage: Google Drive (synced via phone when online)

#### 2. **Trigger Pipeline**

* `n8n` detects new file upload to Drive folder
* Passes file to Whisper for transcription

#### 3. **Transcription**

* Whisper transcribes file
* Returns full text (supports long-form, multi-sentence entries)

#### 4. **Context Fetching**

* `n8n` pulls current data from Notion API:

  * All open tasks
  * Recently closed tasks
  * Notes and project tags
* Summarizes into prompt-friendly format (e.g., JSON + bullet points)

#### 5. **LLM Prompt**

* System prompt:

  * You are an assistant managing tasks and notes.
  * Input: Transcript and task context
  * Output: Structured JSON with updates
  * Classify ambiguous content that doesn't clearly relate to tasks
  * Include confidence levels for uncertain interpretations
* Example input:

  ```json
  {
    "context_summary": "5 open tasks in project 'Sleep Worlds', 3 completed today...",
    "transcript": "I finished the water feature project today. Tomorrow I need to test the pump and maybe buy more tubing. Also add a note about possibly moving the bamboo to the north side."
  }
  ```

#### 6. **Output from LLM**

```json
{
  "completed_tasks": ["Finish water feature project"],
  "new_tasks": ["Test pond pump", "Buy tubing"],
  "notes": ["Consider moving bamboo to north side"],
  "ambiguous_notes": {
    "content": "Feeling really good about the garden progress",
    "confidence": "low",
    "reason": "No clear task or actionable item"
  }
}
```

#### 7. **Apply Updates**

* `n8n` uses Notion API to:

  * Mark tasks as complete
  * Create new tasks
  * Append notes to appropriate pages
  * Add ambiguous content to "Notes for Review" with metadata:
    * Original transcript
    * Timestamp
    * Confidence level
    * Suggested categorization

#### 8. **Logs and Error Handling**

* `n8n` writes a summary of changes to a log DB (Notion or external)
* Email or mobile alert for failures or ambiguous interpretations

#### 9. **Voice Chat (optional)**

* Frontend with Whisper for ASR and TTS for reply
* Query via: "What did I add yesterday?" → Summarize via GPT → Respond via audio

---

### 🚀 Deployment Options

#### n8n

* Hosted: [n8n.cloud](https://n8n.io)
* Self-hosted: Docker on VPS or Cloud Run
* Needs API keys for:

  * Google Drive API
  * Notion API
  * Whisper endpoint
  * OpenAI/Claude (for LLMs)

#### Whisper

* OpenAI API (recommended for ease)
* Optional: Self-host whisper.cpp + exposed REST

#### Notion

* Create one or more databases:

  * Tasks (with status, tags, due, project)
  * Notes
  * Projects (optional)
  * Notes for Review (with transcript, timestamp, confidence, suggested_action)

---

### 📊 Scaling Notes

* LLM token limits may require transcript chunking
* Parallel processing of multiple voice notes is supported via queue
* Fuzzy matching logic can associate spoken task names with Notion entries
* Long-form entries (>500 words) chunked and merged intelligently

---

### 📋 Review Workflow

* **Daily/Weekly Review**: Check "Notes for Review" database
* **Actions**: Convert to task, move to notes, or discard
* **Learning**: Feed decisions back to improve LLM classification
* **Notifications**: Alert when review queue exceeds threshold

---

### ❓ Future Enhancements

* Voice-triggered reminders or recurring tasks
* Auto-tagging by location or time
* Time tracking summaries based on audio
* ChatGPT plugin for querying current status
* ML feedback loop from review decisions

---

### ✅ Status

* ☑ Flow and architecture validated
* ☑ Ready to draft n8n workflow nodes and LLM prompts
* ☑ Confirm ASR preference: OpenAI Whisper or Alt?
* ☑ Confirm data schema in Notion

---
