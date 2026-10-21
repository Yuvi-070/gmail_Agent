"""
L&D Operations Copilot — Direct CLI Runner

Executes the complete daily brief pipeline directly from the command line
or inside GitHub Actions WITHOUT needing a Cloud Run server.

Usage:
    python -m src.run_daily
    # or
    python src/run_daily.py
"""

import asyncio
import logging
import sys
import time

from src.brief_generator import generate_daily_brief
from src.emailer import send_brief_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ld-copilot-cli")


async def main():
    start = time.time()
    logger.info("=" * 60)
    logger.info("🚀 Starting L&D Operations Copilot (Direct CLI Mode)")
    logger.info("=" * 60)

    try:
        # Step 1: Generate brief
        result = await generate_daily_brief()
        brief_html = result["brief_html"]
        metadata = result["metadata"]

        # Step 2: Send email
        logger.info("📧 Sending daily brief to inbox...")
        email_result = await send_brief_email(brief_html, metadata)

        total_time = round(time.time() - start, 2)

        if email_result["success"]:
            logger.info("=" * 60)
            logger.info(
                "✅ SUCCESS: Daily brief emailed in %.2fs (Message ID: %s)",
                total_time,
                email_result["message_id"],
            )
            logger.info("=" * 60)
            sys.exit(0)
        else:
            logger.error(
                "❌ Email dispatch failed after %.2fs: %s",
                total_time,
                email_result["error"],
            )
            sys.exit(1)

    except Exception as e:
        logger.error("❌ Pipeline failed: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
