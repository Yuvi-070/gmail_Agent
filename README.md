# L&D Operations Copilot 🤖

A personal AI agent that generates and emails a daily executive brief every morning, combining data from Gmail, Google Calendar, Google Drive, Google Sheets (ACE Certification Tracker), and Google Meet — all powered by **Gemini 2.5 Flash**.

## Architecture

```
GitHub Actions (9:00 AM IST cron)
        ↓ POST /generate-brief
Cloud Run (FastAPI)
        ↓ concurrent fetch
┌───────┬───────────┬─────────┬──────────────┐
│ Gmail │ Calendar  │  Drive  │ ACE Tracker  │
│  API  │   API     │   API   │ (Sheets API) │
└───────┴───────────┴─────────┴──────────────┘
        ↓ all data
   Gemini 2.5 Flash
        ↓ HTML brief
   Gmail Send API
        ↓
   📧 yuvrajtale070@gmail.com
```

## Project Structure

```
ld-operations-copilot/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py             # Secret Manager / .env config
│   ├── auth.py               # OAuth credential management
│   ├── gmail_tool.py         # Gmail reader
│   ├── calendar_tool.py      # Calendar reader
│   ├── drive_tool.py         # Drive reader
│   ├── ace_tracker.py        # Sheets reader + analytics
│   ├── gemini_service.py     # Gemini AI brief generator
│   ├── brief_generator.py    # Orchestrator
│   └── emailer.py            # Gmail send
├── scripts/
│   └── generate_token.py     # One-time OAuth token generator
├── .github/
│   └── workflows/
│       └── daily-brief.yml   # Daily cron workflow
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.12+
- Google Cloud project with billing enabled
- `gcloud` CLI installed and authenticated

### 1. Enable APIs
```bash
export PROJECT_ID="project-e5a2b3a6-f74d-4dfa-bed"
gcloud config set project $PROJECT_ID

gcloud services enable \
  gmail.googleapis.com \
  calendar-json.googleapis.com \
  drive.googleapis.com \
  sheets.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  iam.googleapis.com
```

### 2. Create OAuth Credentials
1. Go to [GCP Console → APIs & Services → OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent)
2. Configure as External, add your email as test user
3. Add scopes: `gmail.readonly`, `gmail.send`, `calendar.readonly`, `drive.readonly`, `spreadsheets.readonly`
4. Create OAuth Client ID (Desktop type)
5. Download JSON as `client_secret.json`

### 3. Generate Refresh Token
```bash
pip install google-auth-oauthlib
python scripts/generate_token.py
```

### 4. Get Gemini API Key
Go to [Google AI Studio](https://aistudio.google.com/apikey) → Create API Key

### 5. Create ACE Tracker Sheet
Create a Google Sheet with columns: `Course Module | Status | Quiz Score | Revision Status | Notes`

### 6. Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
uvicorn src.main:app --port 8080

# Test all 5 connections
curl -X POST http://localhost:8080/test-connections \
  -H "Authorization: Bearer <YOUR_API_TRIGGER_TOKEN>"

# Generate and send daily brief
curl -X POST http://localhost:8080/generate-brief \
  -H "Authorization: Bearer <YOUR_API_TRIGGER_TOKEN>"
```

### 7. Deploy to Cloud Run (Zero Secret Manager)
Deploy directly passing environment variables (or using `--env-vars-file`):

```bash
export PROJECT_ID="project-e5a2b3a6-f74d-4dfa-bed"
export REGION="asia-south1"

gcloud run deploy ld-copilot \
  --source . \
  --region $REGION \
  --set-env-vars="OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com,OAUTH_CLIENT_SECRET=GOCSPX-your-secret,OAUTH_REFRESH_TOKEN=your-refresh-token,GEMINI_API_KEY=your-gemini-key,GEMINI_MODEL=gemini-3.5-flash,ACE_SHEET_ID=your-sheet-id,API_TRIGGER_TOKEN=your-trigger-token,USER_EMAIL=your-email@gmail.com,GCP_PROJECT_ID=${PROJECT_ID}" \
  --min-instances 0 \
  --max-instances 1 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 120 \
  --allow-unauthenticated \
  --project $PROJECT_ID
```

### 8. Configure GitHub Secrets
In your GitHub repo → Settings → Secrets and variables → Actions:
- `CLOUD_RUN_URL` = Cloud Run service URL (output from step 7)
- `API_TRIGGER_TOKEN` = The same API_TRIGGER_TOKEN you configured in your environment

Test endpoints:
```bash
# Health check
curl http://localhost:8080/health

# Test all connections
curl -X POST http://localhost:8080/test-connections \
  -H "Authorization: Bearer YOUR_TOKEN"

# Generate brief
curl -X POST http://localhost:8080/generate-brief \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Daily Brief Sections

| Section | Source | Content |
|---------|--------|---------|
| 📧 Priority Emails | Gmail API | Urgent / Action Required / FYI |
| 📅 Meetings Today | Calendar API | Time, title, attendees, Meet links |
| 🎯 Meeting Prep | Calendar + Drive | Relevant docs, topics, follow-ups |
| 📚 ACE Progress | Sheets API | Completion %, scores, recommendations |
| 📁 Drive Intel | Drive API | Recent files, meeting-related docs |
| ⭐ Top 5 Priorities | Gemini AI | Cross-source executive summary |

## Cost (Monthly)

| Service | Est. Cost |
|---------|-----------|
| Cloud Run | $0.00 |
| Gemini 2.5 Flash | $0.00 |
| All Workspace APIs | $0.00 |
| Secret Manager | $0.00 |
| Artifact Registry | $0.00 |
| GitHub Actions | $0.00 |
| **Total** | **$0.00** |

## ADK Migration

Each tool module is designed for 1:1 mapping to ADK `@tool` functions:

| Current | ADK |
|---------|-----|
| `gmail_tool.py` | `@tool` GmailTool |
| `calendar_tool.py` | `@tool` CalendarTool |
| `drive_tool.py` | `@tool` DriveTool |
| `ace_tracker.py` | `@tool` AceTrackerTool |
| `brief_generator.py` | `Agent(DailyBriefAgent)` |
| `gemini_service.py` | Built into ADK's LlmAgent |

## License

Personal project — not licensed for distribution.
