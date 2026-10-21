"""
L&D Operations Copilot — Gmail Tool

Reads recent emails and categorizes them for the daily brief.
ADK Migration: Wrap `fetch_priority_emails()` as an ADK @tool.
"""

import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from src.auth import get_gmail_service

logger = logging.getLogger(__name__)

# IST timezone
IST = timezone(timedelta(hours=5, minutes=30))


async def fetch_priority_emails(max_results: int = 20) -> dict[str, Any]:
    """
    Fetch recent emails from the last 24 hours and return structured data.

    Returns:
        dict with keys: emails (list), total_count (int), fetch_time (str)
    """
    logger.info("Fetching priority emails (max: %d)", max_results)
    service = get_gmail_service()

    # Calculate 24 hours ago in epoch seconds
    yesterday = datetime.now(IST) - timedelta(hours=24)
    after_epoch = int(yesterday.timestamp())

    try:
        # Search for recent emails (exclude sent, chats, promotions, social)
        query = (
            f"after:{after_epoch} "
            "-in:sent -in:chats -category:promotions -category:social"
        )

        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )

        messages = results.get("messages", [])
        if not messages:
            logger.info("No new emails found in the last 24 hours")
            return {
                "emails": [],
                "total_count": 0,
                "fetch_time": datetime.now(IST).isoformat(),
            }

        emails = []
        for msg_meta in messages:
            try:
                msg = (
                    service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=msg_meta["id"],
                        format="metadata",
                        metadataHeaders=["From", "Subject", "Date"],
                    )
                    .execute()
                )

                headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
                snippet = msg.get("snippet", "")
                labels = msg.get("labelIds", [])

                emails.append({
                    "id": msg["id"],
                    "from": headers.get("From", "Unknown"),
                    "subject": headers.get("Subject", "(No Subject)"),
                    "date": headers.get("Date", ""),
                    "snippet": snippet[:200],
                    "labels": labels,
                    "is_unread": "UNREAD" in labels,
                    "is_important": "IMPORTANT" in labels,
                    "is_starred": "STARRED" in labels,
                })
            except Exception as e:
                logger.warning("Failed to fetch message %s: %s", msg_meta["id"], e)
                continue

        logger.info("Fetched %d emails successfully", len(emails))
        return {
            "emails": emails,
            "total_count": len(emails),
            "fetch_time": datetime.now(IST).isoformat(),
        }

    except Exception as e:
        logger.error("Gmail fetch failed: %s", e, exc_info=True)
        return {
            "emails": [],
            "total_count": 0,
            "fetch_time": datetime.now(IST).isoformat(),
            "error": str(e),
        }
