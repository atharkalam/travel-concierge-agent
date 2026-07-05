"""Google Maps Grounding Lite MCP toolset factory.

This module provides a reusable ``McpToolset`` instance that connects to
Google's hosted **Maps Grounding Lite** MCP server.  The server exposes three
tools that give agents access to real-time geospatial data:

    ===============  ============================================
    MCP Tool          Purpose
    ===============  ============================================
    search_places     Find businesses, landmarks, addresses, or
                      points of interest by text query.
    lookup_weather    Get current conditions and hourly/daily
                      forecasts for a location.
    compute_routes    Calculate travel distance and duration
                      between two points (driving or walking).
    ===============  ============================================

Usage
─────
Import the factory function and add its return value to any agent's
``tools`` list::

    from app.maps_mcp import get_maps_toolset

    my_agent = Agent(
        ...,
        tools=[get_maps_toolset()],
    )

Authentication
──────────────
The ``GOOGLE_MAPS_API_KEY`` environment variable **must** be set.  The key is
passed to the MCP server via the ``X-Goog-Api-Key`` HTTP header — it is never
hardcoded in source.

For local development, add the key to ``.env``.  For Cloud Run deployments,
provision it as a Secret Manager secret or set it in the service's environment
variables.

Transport
─────────
Maps Grounding Lite is a hosted **Streamable HTTP** MCP endpoint.  We use
``StreamableHTTPConnectionParams`` (not ``SseConnectionParams``) because the
server speaks the Streamable HTTP transport defined by the MCP spec.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Ensure .env is loaded before reading GOOGLE_MAPS_API_KEY, regardless of
# import order across modules.  load_dotenv() is a no-op if already called.
_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent
# Local dev: load from project root (.env)
load_dotenv(_PROJECT_ROOT / ".env")
# Deployed container: load from app/ directory (app/.env)
load_dotenv(_THIS_DIR / ".env")

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StreamableHTTPConnectionParams,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Maps Grounding Lite MCP endpoint
# ---------------------------------------------------------------------------
# This is Google's managed MCP server for Maps data.  It requires an API key
# with the Maps Grounding Lite service enabled in the Google Cloud Console.
# ---------------------------------------------------------------------------
_MAPS_MCP_URL = "https://mapstools.googleapis.com/mcp"


def get_maps_toolset() -> McpToolset:
    """Create an ``McpToolset`` connected to the Maps Grounding Lite MCP.

    The toolset reads ``GOOGLE_MAPS_API_KEY`` from the environment at call
    time.  If the variable is unset, a warning is logged and the toolset is
    still returned (it will fail at runtime when the agent tries to invoke a
    Maps tool, making the error obvious and debuggable).

    Returns:
        A configured ``McpToolset`` ready to be passed to an agent's
        ``tools`` list.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")

    if not api_key:
        logger.warning(
            "GOOGLE_MAPS_API_KEY is not set.  Maps MCP tools will fail at "
            "runtime.  Set the variable in .env or your deployment config."
        )

    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=_MAPS_MCP_URL,
            headers={
                "X-Goog-Api-Key": api_key,
                "Content-Type": "application/json",
            },
        ),
    )
