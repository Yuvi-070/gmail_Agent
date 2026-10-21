"""
L&D Operations Copilot — Google OAuth Helper

Builds authenticated Google API service clients using OAuth refresh tokens.
Designed for ADK migration: each function returns data dicts, not service objects.
"""

import logging
from functools import lru_cache

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.config import get_config

logger = logging.getLogger(__name__)

# OAuth scopes required by the application
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

TOKEN_URI = "https://oauth2.googleapis.com/token"


def _get_credentials() -> Credentials:
    """Build OAuth credentials from refresh token."""
    config = get_config()
    creds = Credentials(
        token=None,
        refresh_token=config.oauth_refresh_token,
        token_uri=TOKEN_URI,
        client_id=config.oauth_client_id,
        client_secret=config.oauth_client_secret,
        scopes=SCOPES,
    )
    return creds


@lru_cache(maxsize=1)
def get_gmail_service():
    """Build Gmail API service client."""
    logger.info("Building Gmail API service")
    return build("gmail", "v1", credentials=_get_credentials())


@lru_cache(maxsize=1)
def get_calendar_service():
    """Build Calendar API service client."""
    logger.info("Building Calendar API service")
    return build("calendar", "v3", credentials=_get_credentials())


@lru_cache(maxsize=1)
def get_drive_service():
    """Build Drive API service client."""
    logger.info("Building Drive API service")
    return build("drive", "v3", credentials=_get_credentials())


@lru_cache(maxsize=1)
def get_sheets_service():
    """Build Sheets API service client."""
    logger.info("Building Sheets API service")
    return build("sheets", "v4", credentials=_get_credentials())
