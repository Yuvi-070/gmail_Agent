"""
L&D Operations Copilot — Brief Generator (Orchestrator)

Orchestrates all tools and produces the final brief.
ADK Migration: This becomes the DailyBriefAgent with all tools registered.
"""

import asyncio
import logging
import time
from typing import Any

from src.gmail_tool import fetch_priority_emails
from src.calendar_tool import fetch_todays_events
from src.drive_tool import fetch_recent_files
from src.ace_tracker import fetch_ace_progress
from src.gemini_service import generate_executive_brief

logger = logging.getLogger(__name__)


async def generate_daily_brief() -> dict[str, Any]:
    """
    Full orchestration pipeline:
    1. Fetch data from all sources concurrently
    2. Send to Gemini for brief generation
    3. Return the brief HTML and metadata

    Returns:
        dict with keys: brief_html (str), metadata (dict)
    """
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("STARTING DAILY BRIEF GENERATION")
    logger.info("=" * 60)

    # Step 1: Fetch all data sources concurrently
    logger.info("Step 1/3: Fetching data from all sources...")
    emails_data, calendar_data, drive_data, ace_data = await asyncio.gather(
        fetch_priority_emails(),
        fetch_todays_events(),
        fetch_recent_files(),
        fetch_ace_progress(),
        return_exceptions=True,
    )

    # Handle any exceptions from concurrent fetches
    if isinstance(emails_data, Exception):
        logger.error("Gmail tool failed: %s", emails_data)
        emails_data = {"emails": [], "total_count": 0, "error": str(emails_data)}

    if isinstance(calendar_data, Exception):
        logger.error("Calendar tool failed: %s", calendar_data)
        calendar_data = {"events": [], "total_count": 0, "error": str(calendar_data)}

    if isinstance(drive_data, Exception):
        logger.error("Drive tool failed: %s", drive_data)
        drive_data = {"files": [], "total_count": 0, "error": str(drive_data)}

    if isinstance(ace_data, Exception):
        logger.error("ACE Tracker tool failed: %s", ace_data)
        ace_data = {
            "modules": [],
            "stats": {"completion_percentage": 0},
            "recommendations": {},
            "error": str(ace_data),
        }

    fetch_time = time.time() - start_time
    logger.info(
        "Data fetch complete in %.2fs — Emails: %d, Events: %d, Files: %d, ACE Modules: %d",
        fetch_time,
        emails_data.get("total_count", 0),
        calendar_data.get("total_count", 0),
        drive_data.get("total_count", 0),
        len(ace_data.get("modules", [])),
    )

    # Step 2: Generate brief with Gemini
    logger.info("Step 2/3: Generating brief with Gemini...")
    gemini_start = time.time()

    brief_html = await generate_executive_brief(
        emails_data=emails_data,
        calendar_data=calendar_data,
        drive_data=drive_data,
        ace_data=ace_data,
    )

    gemini_time = time.time() - gemini_start
    logger.info("Gemini generation complete in %.2fs", gemini_time)

    # Step 3: Build metadata
    total_time = time.time() - start_time
    metadata = {
        "generation_time_seconds": round(total_time, 2),
        "fetch_time_seconds": round(fetch_time, 2),
        "gemini_time_seconds": round(gemini_time, 2),
        "data_summary": {
            "emails_count": emails_data.get("total_count", 0),
            "events_count": calendar_data.get("total_count", 0),
            "files_count": drive_data.get("total_count", 0),
            "ace_modules": len(ace_data.get("modules", [])),
            "ace_completion": ace_data.get("stats", {}).get("completion_percentage", 0),
        },
        "errors": {
            source: data.get("error")
            for source, data in [
                ("gmail", emails_data),
                ("calendar", calendar_data),
                ("drive", drive_data),
                ("ace_tracker", ace_data),
            ]
            if data.get("error")
        },
    }

    logger.info("=" * 60)
    logger.info("DAILY BRIEF COMPLETE — Total: %.2fs", total_time)
    logger.info("=" * 60)

    return {
        "brief_html": brief_html,
        "metadata": metadata,
    }
