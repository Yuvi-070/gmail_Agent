"""
L&D Operations Copilot — ACE Certification Tracker Tool

Reads and analyzes the ACE study progress from a Google Sheet.
ADK Migration: Wrap `fetch_ace_progress()` as an ADK @tool.
"""

import logging
from typing import Any

from src.auth import get_sheets_service
from src.config import get_config

logger = logging.getLogger(__name__)


async def fetch_ace_progress() -> dict[str, Any]:
    """
    Read ACE Certification Tracker Google Sheet and calculate progress metrics.

    Expected Sheet columns (Row 1 = headers):
        A: Course Module
        B: Status (Done / In Progress / Pending)
        C: Quiz Score (integer or empty)
        D: Revision Status (Done / Pending / empty)
        E: Notes

    Returns:
        dict with keys: modules (list), stats (dict), recommendations (dict)
    """
    logger.info("Fetching ACE certification progress")
    config = get_config()
    service = get_sheets_service()

    try:
        # Read all data from Sheet1
        result = (
            service.spreadsheets()
            .values()
            .get(
                spreadsheetId=config.ace_sheet_id,
                range="Sheet1!A:E",
            )
            .execute()
        )

        rows = result.get("values", [])
        if len(rows) < 2:
            logger.warning("ACE Sheet has no data rows")
            return _empty_result("No data found in ACE Tracker Sheet")

        # Parse header and data rows
        headers = rows[0]
        data_rows = rows[1:]

        modules = []
        scores = []
        done_count = 0
        in_progress_count = 0
        pending_count = 0
        needs_revision = []

        for row in data_rows:
            # Pad row to 5 columns
            while len(row) < 5:
                row.append("")

            module_name = row[0].strip()
            status = row[1].strip() if row[1] else "Pending"
            quiz_score_raw = row[2].strip() if row[2] else ""
            revision_status = row[3].strip() if row[3] else ""
            notes = row[4].strip() if row[4] else ""

            # Parse quiz score
            quiz_score = None
            if quiz_score_raw and quiz_score_raw != "-":
                try:
                    quiz_score = int(quiz_score_raw)
                    scores.append(quiz_score)
                except ValueError:
                    pass

            module = {
                "name": module_name,
                "status": status,
                "quiz_score": quiz_score,
                "revision_status": revision_status,
                "notes": notes,
            }
            modules.append(module)

            # Count statuses
            status_lower = status.lower()
            if status_lower == "done":
                done_count += 1
                if revision_status.lower() == "pending":
                    needs_revision.append(module_name)
            elif status_lower == "in progress":
                in_progress_count += 1
            else:
                pending_count += 1

        total = len(modules)
        completion_pct = round((done_count / total) * 100, 1) if total > 0 else 0.0

        # Find weakest module (lowest quiz score)
        weakest_module = None
        if scores:
            min_score = min(scores)
            for m in modules:
                if m["quiz_score"] == min_score:
                    weakest_module = {"name": m["name"], "score": min_score}
                    break

        # Find recommended next topic
        recommended_next = None
        # Priority: In Progress first, then first Pending
        for m in modules:
            if m["status"].lower() == "in progress":
                recommended_next = m["name"]
                break
        if not recommended_next:
            for m in modules:
                if m["status"].lower() == "pending":
                    recommended_next = m["name"]
                    break

        # Calculate average score
        avg_score = round(sum(scores) / len(scores), 1) if scores else None

        # Study duration recommendation based on progress
        if completion_pct < 30:
            study_duration = "2-3 hours/day (intensive phase)"
        elif completion_pct < 60:
            study_duration = "1.5-2 hours/day (steady progress)"
        elif completion_pct < 90:
            study_duration = "1-1.5 hours/day (refinement phase)"
        else:
            study_duration = "1 hour/day (revision & practice exams)"

        stats = {
            "total_modules": total,
            "completed": done_count,
            "in_progress": in_progress_count,
            "pending": pending_count,
            "completion_percentage": completion_pct,
            "average_score": avg_score,
            "weakest_module": weakest_module,
        }

        recommendations = {
            "next_topic": recommended_next,
            "needs_revision": needs_revision,
            "suggested_study_duration": study_duration,
        }

        logger.info(
            "ACE progress: %d/%d completed (%.1f%%)",
            done_count, total, completion_pct,
        )

        return {
            "modules": modules,
            "stats": stats,
            "recommendations": recommendations,
        }

    except Exception as e:
        logger.error("ACE Tracker fetch failed: %s", e, exc_info=True)
        return _empty_result(str(e))


def _empty_result(error: str) -> dict[str, Any]:
    """Return an empty result structure with an error message."""
    return {
        "modules": [],
        "stats": {
            "total_modules": 0,
            "completed": 0,
            "in_progress": 0,
            "pending": 0,
            "completion_percentage": 0.0,
            "average_score": None,
            "weakest_module": None,
        },
        "recommendations": {
            "next_topic": None,
            "needs_revision": [],
            "suggested_study_duration": "N/A",
        },
        "error": error,
    }
