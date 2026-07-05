"""Logging configuration for the Travel Concierge.

Call `setup_logging()` once at application startup to configure structured
logging with sensible defaults for both local development and production.
"""

from __future__ import annotations

import logging
import sys

from app.config import LOG_LEVEL


def setup_logging() -> None:
    """Configure application-wide logging.

    - Logs to **stderr** so they don't mix with ADK's stdout output.
    - Uses a human-readable format for local development; swap to
      `json` formatting for production / Cloud Logging if desired.
    - Respects the ``LOG_LEVEL`` environment variable (default: INFO).
    """
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format=log_format,
        datefmt=date_format,
        stream=sys.stderr,
        force=True,  # override any prior basicConfig
    )

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)

    # Keep ADK events visible at INFO for debugging agent flow
    logging.getLogger("google.adk").setLevel(logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info("Logging initialised — level=%s", LOG_LEVEL)
