"""Travel Concierge — Google ADK 2.x multi-agent application.

This module is the entry point that ADK CLI tools (``adk web``, ``adk run``,
``agents-cli playground``) use to discover the application.  It wires together
the root agent, logging, and the ``App`` instance.

The ``App.name`` **must** match the directory name (``"app"``) to avoid
"Session not found" errors during evaluation.
"""

from google.adk.apps import App

from app.agent import root_agent
from app.logging_config import setup_logging

# Configure logging before any agent activity
setup_logging()

app = App(
    name="app",
    root_agent=root_agent,
)
