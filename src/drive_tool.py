"""
L&D Operations Copilot — Drive Tool

Reads recently modified files from Google Drive.
ADK Migration: Wrap `fetch_recent_files()` as an ADK @tool.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from src.auth import get_drive_service

logger = logging.getLogger(__name__)

# IST timezone
IST = timezone(timedelta(hours=5, minutes=30))


async def fetch_recent_files(max_results: int = 15) -> dict[str, Any]:
    """
    Fetch recently modified files from Google Drive (last 48 hours).

    Returns:
        dict with keys: files (list), total_count (int), fetch_time (str)
    """
    logger.info("Fetching recent Drive files (max: %d)", max_results)
    service = get_drive_service()

    # Look back 48 hours to catch files from yesterday evening
    cutoff = datetime.now(IST) - timedelta(hours=48)
    cutoff_rfc = cutoff.strftime("%Y-%m-%dT%H:%M:%S")

    try:
        results = (
            service.files()
            .list(
                q=f"modifiedTime > '{cutoff_rfc}' and trashed = false",
                orderBy="modifiedTime desc",
                pageSize=max_results,
                fields="files(id, name, mimeType, modifiedTime, webViewLink, owners, shared)",
                spaces="drive",
            )
            .execute()
        )

        raw_files = results.get("files", [])

        files = []
        for f in raw_files:
            # Map MIME types to friendly names
            mime = f.get("mimeType", "")
            file_type = _mime_to_friendly(mime)

            owners = [
                o.get("displayName", o.get("emailAddress", "Unknown"))
                for o in f.get("owners", [])
            ]

            files.append({
                "id": f.get("id", ""),
                "name": f.get("name", "Untitled"),
                "type": file_type,
                "mime_type": mime,
                "modified_time": f.get("modifiedTime", ""),
                "web_link": f.get("webViewLink", ""),
                "owners": owners,
                "is_shared": f.get("shared", False),
            })

        logger.info("Found %d recently modified files", len(files))
        return {
            "files": files,
            "total_count": len(files),
            "fetch_time": datetime.now(IST).isoformat(),
        }

    except Exception as e:
        logger.error("Drive fetch failed: %s", e, exc_info=True)
        return {
            "files": [],
            "total_count": 0,
            "fetch_time": datetime.now(IST).isoformat(),
            "error": str(e),
        }


def _mime_to_friendly(mime: str) -> str:
    """Convert MIME type to a human-friendly file type name."""
    mime_map = {
        "application/vnd.google-apps.document": "Google Doc",
        "application/vnd.google-apps.spreadsheet": "Google Sheet",
        "application/vnd.google-apps.presentation": "Google Slides",
        "application/vnd.google-apps.form": "Google Form",
        "application/vnd.google-apps.folder": "Folder",
        "application/pdf": "PDF",
        "image/png": "PNG Image",
        "image/jpeg": "JPEG Image",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word Doc",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel Sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PowerPoint",
        "text/plain": "Text File",
        "application/json": "JSON File",
        "text/csv": "CSV File",
    }
    return mime_map.get(mime, "File")
