"""
L&D Operations Copilot — FastAPI Application

Main entry point for the Cloud Run service.
Exposes endpoints for brief generation and health checks.
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import get_config
from src.brief_generator import generate_daily_brief
from src.emailer import send_brief_email

# ─── Logging Setup ────────────────────────────────────────────
# Structured logging compatible with Cloud Run / Cloud Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ld-copilot")

# IST timezone
IST = timezone(timedelta(hours=5, minutes=30))


# ─── App Lifecycle ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("🚀 L&D Operations Copilot starting up...")
    # Pre-load config (validates all env vars are present)
    try:
        config = get_config()
        logger.info("✅ Configuration loaded for user: %s", config.user_email)
    except Exception as e:
        logger.error("❌ Failed to load configuration: %s", e)
    yield
    logger.info("👋 L&D Operations Copilot shutting down")


# ─── FastAPI App ──────────────────────────────────────────────
app = FastAPI(
    title="L&D Operations Copilot",
    description="Personal AI agent that generates daily executive briefs.",
    version="1.0.0",
    lifespan=lifespan,
)

security = HTTPBearer()


# ─── Auth Middleware ──────────────────────────────────────────
def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Verify the Bearer token matches our API trigger token."""
    config = get_config()
    if credentials.credentials != config.api_trigger_token:
        logger.warning("Unauthorized request — invalid bearer token")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
        )
    return credentials.credentials


# ─── Endpoints ────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint (unauthenticated for Cloud Run)."""
    return {
        "status": "healthy",
        "service": "ld-operations-copilot",
        "timestamp": datetime.now(IST).isoformat(),
    }


@app.post("/generate-brief")
async def generate_brief_endpoint(token: str = Security(verify_token)):
    """
    Generate and email the daily brief.

    This is the endpoint called by GitHub Actions cron every morning.
    Requires Bearer token authentication.
    """
    request_time = time.time()
    logger.info("📋 Brief generation request received")

    try:
        # Step 1: Generate the brief
        result = await generate_daily_brief()
        brief_html = result["brief_html"]
        metadata = result["metadata"]

        # Step 2: Send email
        logger.info("📧 Sending brief email...")
        email_result = await send_brief_email(brief_html, metadata)

        total_time = time.time() - request_time

        if email_result["success"]:
            logger.info(
                "✅ Daily brief generated and sent in %.2fs (Message ID: %s)",
                total_time,
                email_result["message_id"],
            )
            return {
                "status": "success",
                "message": "Daily brief generated and sent",
                "email_message_id": email_result["message_id"],
                "total_time_seconds": round(total_time, 2),
                "metadata": metadata,
            }
        else:
            logger.error("❌ Brief generated but email failed: %s", email_result["error"])
            raise HTTPException(
                status_code=500,
                detail=f"Brief generated but email failed: {email_result['error']}",
            )

    except HTTPException:
        raise
    except Exception as e:
        total_time = time.time() - request_time
        logger.error(
            "❌ Brief generation failed after %.2fs: %s",
            total_time, e, exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Brief generation failed: {str(e)}",
        )


@app.post("/test-connections")
async def test_connections(token: str = Security(verify_token)):
    """
    Test all API connections without generating a full brief.
    Useful for debugging after initial setup.
    """
    logger.info("🔍 Testing all API connections...")
    results = {}

    # Test Gmail
    try:
        from src.auth import get_gmail_service
        service = get_gmail_service()
        profile = service.users().getProfile(userId="me").execute()
        results["gmail"] = {"status": "ok", "email": profile.get("emailAddress")}
    except Exception as e:
        results["gmail"] = {"status": "error", "error": str(e)}

    # Test Calendar
    try:
        from src.auth import get_calendar_service
        service = get_calendar_service()
        calendars = service.calendarList().list(maxResults=1).execute()
        results["calendar"] = {"status": "ok", "calendars": len(calendars.get("items", []))}
    except Exception as e:
        results["calendar"] = {"status": "error", "error": str(e)}

    # Test Drive
    try:
        from src.auth import get_drive_service
        service = get_drive_service()
        about = service.about().get(fields="user").execute()
        results["drive"] = {"status": "ok", "user": about.get("user", {}).get("displayName")}
    except Exception as e:
        results["drive"] = {"status": "error", "error": str(e)}

    # Test Sheets
    try:
        from src.auth import get_sheets_service
        config = get_config()
        service = get_sheets_service()
        sheet = service.spreadsheets().get(spreadsheetId=config.ace_sheet_id).execute()
        results["sheets"] = {"status": "ok", "title": sheet.get("properties", {}).get("title")}
    except Exception as e:
        results["sheets"] = {"status": "error", "error": str(e)}

    # Test Gemini
    try:
        from google import genai
        config = get_config()
        client = genai.Client(api_key=config.gemini_api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        response = client.models.generate_content(
            model=model_name,
            contents="Reply with exactly: CONNECTION_OK",
        )
        results["gemini"] = {"status": "ok", "response": response.text.strip()}
    except Exception as e:
        results["gemini"] = {"status": "error", "error": str(e)}

    # Overall status
    all_ok = all(r.get("status") == "ok" for r in results.values())
    logger.info("Connection test complete — all OK: %s", all_ok)

    return {
        "status": "all_ok" if all_ok else "partial_failure",
        "connections": results,
    }
