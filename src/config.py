"""
L&D Operations Copilot — Configuration

Loads all configuration from environment variables.
- Local: reads from .env file via python-dotenv
- Cloud Run: reads from env vars set via --set-env-vars at deploy time

No Secret Manager dependency — keeps the stack simple and free.
"""

import os
import logging
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Always attempt to load .env (no-op if file doesn't exist, e.g. on Cloud Run)
load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration."""
    oauth_client_id: str
    oauth_client_secret: str
    oauth_refresh_token: str
    gemini_api_key: str
    ace_sheet_id: str
    api_trigger_token: str
    user_email: str
    gcp_project_id: str


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """
    Load configuration from environment variables.
    Cached so it's built only once per process.
    """
    logger.info("Loading configuration from environment variables")

    required_vars = [
        "OAUTH_CLIENT_ID",
        "OAUTH_CLIENT_SECRET",
        "OAUTH_REFRESH_TOKEN",
        "GEMINI_API_KEY",
        "ACE_SHEET_ID",
        "API_TRIGGER_TOKEN",
    ]

    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Set them in .env (local) or via Cloud Run --set-env-vars (production)."
        )

    raw_sheet_id = os.environ["ACE_SHEET_ID"].strip()
    # Extract ID if a full URL was provided
    if "/d/" in raw_sheet_id:
        raw_sheet_id = raw_sheet_id.split("/d/")[1].split("/")[0]

    return AppConfig(
        oauth_client_id=os.environ["OAUTH_CLIENT_ID"],
        oauth_client_secret=os.environ["OAUTH_CLIENT_SECRET"],
        oauth_refresh_token=os.environ["OAUTH_REFRESH_TOKEN"],
        gemini_api_key=os.environ["GEMINI_API_KEY"],
        ace_sheet_id=raw_sheet_id,
        api_trigger_token=os.environ["API_TRIGGER_TOKEN"],
        user_email=os.getenv("USER_EMAIL", "yuvrajtale070@gmail.com"),
        gcp_project_id=os.getenv("GCP_PROJECT_ID", "project-e5a2b3a6-f74d-4dfa-bed"),
    )
