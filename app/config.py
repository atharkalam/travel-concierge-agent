"""Centralized configuration for the Travel Concierge.

Loads environment variables from `.env` (if present) and provides typed
configuration constants used across the application.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env from the project root (two levels up from this file)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"

load_dotenv(_ENV_FILE)

# ---------------------------------------------------------------------------
# Google Cloud / Vertex AI
# ---------------------------------------------------------------------------
GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_GENAI_USE_VERTEXAI: bool = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "True").lower() == "true"

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
APP_NAME: str = "app"  # Must match the agent directory name
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
