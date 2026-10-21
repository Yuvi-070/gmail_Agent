"""
L&D Operations Copilot — Calendar Tool

Reads today's calendar events including Google Meet links.
ADK Migration: Wrap `fetch_todays_events()` as an ADK @tool.
"""

import logging
from datetime import datetime, timedelta, timezone, time
from typing import Any

from src.auth import get_calendar_service

logger = logging.getLogger(__name__)

# IST timezone
IST = timezone(timedelta(hours=5, minutes=30))


async def fetch_todays_events() -> dict[str, Any]:
    """
    Fetch all calendar events for today (IST).

    Returns:
        dict with keys: events (list), total_count (int), date (str)
    """
    logger.info("Fetching today's calendar events")
    service = get_calendar_service()

    # Today's boundaries in IST
    now_ist = datetime.now(IST)
    start_of_day = datetime.combine(now_ist.date(), time.min, tzinfo=IST)
    end_of_day = datetime.combine(now_ist.date(), time.max, tzinfo=IST)

    try:
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=25,
            )
            .execute()
        )

        raw_events = events_result.get("items", [])

        events = []
        for event in raw_events:
            start = event.get("start", {})
            end = event.get("end", {})

            # Extract Google Meet link if present
            conference_data = event.get("conferenceData", {})
            meet_link = None
            for entry_point in conference_data.get("entryPoints", []):
                if entry_point.get("entryPointType") == "video":
                    meet_link = entry_point.get("uri")
                    break

            # Extract attendees
            attendees = []
            for attendee in event.get("attendees", []):
                attendees.append({
                    "email": attendee.get("email", ""),
                    "name": attendee.get("displayName", attendee.get("email", "")),
                    "response": attendee.get("responseStatus", "needsAction"),
                })

            events.append({
                "id": event.get("id", ""),
                "title": event.get("summary", "(No Title)"),
                "description": (event.get("description") or "")[:300],
                "start_time": start.get("dateTime", start.get("date", "")),
                "end_time": end.get("dateTime", end.get("date", "")),
                "location": event.get("location", ""),
                "meet_link": meet_link,
                "attendees": attendees,
                "organizer": event.get("organizer", {}).get("email", ""),
                "status": event.get("status", "confirmed"),
                "is_all_day": "date" in start and "dateTime" not in start,
            })

        logger.info("Found %d events for today", len(events))
        return {
            "events": events,
            "total_count": len(events),
            "date": now_ist.strftime("%Y-%m-%d"),
        }

    except Exception as e:
        logger.error("Calendar fetch failed: %s", e, exc_info=True)
        return {
            "events": [],
            "total_count": 0,
            "date": datetime.now(IST).strftime("%Y-%m-%d"),
            "error": str(e),
        }
