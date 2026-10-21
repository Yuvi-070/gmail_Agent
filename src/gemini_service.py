"""
L&D Operations Copilot — Gemini AI Service

Handles all interactions with Gemini 2.5 Flash via Google AI Studio.
ADK Migration: This module is replaced entirely by ADK's built-in LlmAgent.
"""

import json
import logging
import os
from typing import Any

from google import genai
from google.genai.types import GenerateContentConfig

from src.config import get_config

logger = logging.getLogger(__name__)


def _get_client() -> genai.Client:
    """Build Gemini client using AI Studio API key."""
    config = get_config()
    return genai.Client(api_key=config.gemini_api_key)


async def generate_executive_brief(
    emails_data: dict[str, Any],
    calendar_data: dict[str, Any],
    drive_data: dict[str, Any],
    ace_data: dict[str, Any],
) -> str:
    """
    Send all collected data to Gemini and generate the executive daily brief.

    Args:
        emails_data: Output from gmail_tool.fetch_priority_emails()
        calendar_data: Output from calendar_tool.fetch_todays_events()
        drive_data: Output from drive_tool.fetch_recent_files()
        ace_data: Output from ace_tracker.fetch_ace_progress()

    Returns:
        str: HTML-formatted executive brief
    """
    logger.info("Generating executive brief with Gemini 2.5 Flash")

    client = _get_client()

    # Build the prompt with all data
    prompt = _build_prompt(emails_data, calendar_data, drive_data, ace_data)

    try:
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=4096,
                response_mime_type="text/plain",
            ),
        )

        brief_content = response.text
        logger.info("Gemini generated brief (%d characters)", len(brief_content))
        return brief_content

    except Exception as e:
        logger.error("Gemini generation failed: %s", e, exc_info=True)
        return _fallback_brief(emails_data, calendar_data, drive_data, ace_data)


def _build_prompt(
    emails_data: dict,
    calendar_data: dict,
    drive_data: dict,
    ace_data: dict,
) -> str:
    """Build the structured prompt for Gemini."""

    return f"""You are an executive AI assistant creating a daily morning brief for a Learning & Development professional who is also preparing for the Google Associate Cloud Engineer (ACE) certification.

Generate a well-structured HTML email brief. Use inline CSS for email compatibility (no external stylesheets). Use a clean, professional design with these colors: #1a73e8 (Google blue) for headers, #202124 for text, #f8f9fa for backgrounds.

## DATA SOURCES

### EMAILS (Last 24 Hours)
```json
{json.dumps(emails_data, indent=2, default=str)}
```

### CALENDAR (Today's Events)
```json
{json.dumps(calendar_data, indent=2, default=str)}
```

### GOOGLE DRIVE (Recently Modified Files)
```json
{json.dumps(drive_data, indent=2, default=str)}
```

### ACE CERTIFICATION TRACKER
```json
{json.dumps(ace_data, indent=2, default=str)}
```

## REQUIRED SECTIONS

Generate the brief with these exact sections:

### 1. 🌅 Morning Brief Header
- Date and greeting
- Quick summary line (1 sentence overview of the day)

### 2. 📧 Priority Emails
Categorize each email into:
- 🔴 **Urgent** — needs immediate attention
- 🟡 **Action Required** — needs response today
- 🟢 **FYI** — informational only
Include sender, subject, and a 1-line action recommendation for each.
If no emails, say "Inbox clear — great start to the day!"

### 3. 📅 Meetings Today
For each meeting:
- Time (in IST)
- Title
- Attendees (if available)
- Google Meet link (if available)
If no meetings, say "No meetings — deep work day!"

### 4. 🎯 Meeting Preparation
For each meeting, suggest:
- Relevant documents from Drive (cross-reference with Drive data)
- Key topics to prepare
- Follow-up items from previous context
If no meetings, skip this section.

### 5. 📚 ACE Certification Progress
- Current module being studied
- Overall progress: X/Y modules (Z%)
- Average quiz score
- Weakest area needing attention
- Revision recommendations
- Suggested study duration for today

### 6. 📁 Google Drive Intelligence
- Recently modified files (with links if available)
- Documents that relate to today's meetings
- Important shared documents

### 7. ⭐ Top 5 Priorities
Generate a prioritized list of the 5 most important things to focus on today, synthesizing across all data sources. Include a mix of:
- Urgent email responses
- Meeting preparation
- Study goals
- Document reviews
- Any deadlines

## FORMATTING RULES
- Output raw HTML only (no markdown, no ```html wrappers)
- Use inline CSS for all styling
- Use a max-width of 680px, centered layout
- Use Google-style typography (font-family: 'Google Sans', Arial, sans-serif)
- Make it visually clean and scannable
- Use emoji sparingly but effectively for section headers
- Include a footer with generation timestamp
- Make sure all links are clickable <a> tags
"""


def _fallback_brief(
    emails_data: dict,
    calendar_data: dict,
    drive_data: dict,
    ace_data: dict,
) -> str:
    """Generate a basic brief if Gemini fails."""
    logger.warning("Using fallback brief generator")

    email_count = emails_data.get("total_count", 0)
    event_count = calendar_data.get("total_count", 0)
    file_count = drive_data.get("total_count", 0)
    ace_stats = ace_data.get("stats", {})
    completion = ace_stats.get("completion_percentage", 0)

    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 680px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #1a73e8;">🌅 Morning Brief</h1>
        <p style="color: #666;">⚠️ AI summary unavailable — here's your raw data overview.</p>

        <h2 style="color: #202124;">📧 Emails</h2>
        <p>{email_count} new emails in the last 24 hours.</p>

        <h2 style="color: #202124;">📅 Meetings</h2>
        <p>{event_count} meetings scheduled for today.</p>

        <h2 style="color: #202124;">📁 Drive</h2>
        <p>{file_count} files modified recently.</p>

        <h2 style="color: #202124;">📚 ACE Progress</h2>
        <p>{completion}% complete</p>

        <hr style="border: 1px solid #e0e0e0;">
        <p style="color: #999; font-size: 12px;">
            Fallback brief generated by L&D Operations Copilot.
            Gemini was unavailable — the full AI brief will resume tomorrow.
        </p>
    </div>
    """
