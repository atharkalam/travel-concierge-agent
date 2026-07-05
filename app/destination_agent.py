"""Destination Recommendation sub-agent.

This module defines ``destination_agent`` — the specialist responsible for
suggesting travel destinations to the user.

Responsibilities
────────────────
The destination agent:

    1. Receives the user's travel preferences (budget, dates, duration,
       interests) from the orchestrator.
    2. Recommends up to three matching destinations with reasoning,
       best-visit timing, top attractions, and estimated costs.
    3. Asks clarifying questions when the user's requirements are ambiguous.

It does **not** create day-by-day itineraries or produce detailed budget
breakdowns — those tasks belong to the itinerary and budget agents
respectively.

Integration with the Travel Concierge
──────────────────────────────────────
This agent is designed to be imported by ``agent.py`` and registered as a
sub-agent of the root ``travel_concierge`` orchestrator::

    from app.destination_agent import destination_agent

    root_agent = Agent(
        ...,
        sub_agents=[destination_agent],
    )

ADK uses the agent's ``name`` and ``description`` fields to build delegation
prompts, so both are kept concise and accurate.

Prompt loading
──────────────
The system instruction is loaded from ``app/prompts/destination_recommendation.md``.
See the root ``agent.py`` docstring for the rationale behind external prompt
files.
"""

from __future__ import annotations

from pathlib import Path

from google.adk.agents import Agent
from google.genai import types as genai_types

from app.maps_mcp import get_maps_toolset

# ──────────────────────────────────────────────────────────────────────────────
# 1. Load the system instruction from the shared prompts directory
# ──────────────────────────────────────────────────────────────────────────────

_PROMPT_DIR = Path(__file__).resolve().parent / "prompts"


def _load_prompt(filename: str) -> str:
    """Read a prompt file from the ``app/prompts/`` directory.

    Args:
        filename: Name of the Markdown file (e.g. ``"destination_recommendation.md"``).

    Returns:
        The file contents as a string.

    Raises:
        FileNotFoundError: If the prompt file does not exist.
    """
    path = _PROMPT_DIR / filename
    return path.read_text(encoding="utf-8")


_INSTRUCTION = _load_prompt("destination_recommendation.md")

# ──────────────────────────────────────────────────────────────────────────────
# 2. Model generation configuration
# ──────────────────────────────────────────────────────────────────────────────
# These parameters are tuned for a *creative specialist* rather than a
# routing orchestrator:
#
#   temperature = 0.7
#       Higher than the orchestrator's 0.4.  Destination recommendations
#       benefit from more diverse and evocative suggestions — the agent
#       should "sell" each destination with vivid descriptions.
#
#   max_output_tokens = 4096
#       The agent returns at most three destinations with brief write-ups.
#       4K tokens is ample for this scope and keeps responses focused.
#
#   top_p = 0.95
#       Slightly broader than the orchestrator to allow more creative
#       vocabulary while still avoiding incoherent outputs.
# ──────────────────────────────────────────────────────────────────────────────

_GENERATE_CONTENT_CONFIG = genai_types.GenerateContentConfig(
    temperature=0.7,
    max_output_tokens=4096,
    top_p=0.95,
)

# ──────────────────────────────────────────────────────────────────────────────
# 3. Destination agent definition
# ──────────────────────────────────────────────────────────────────────────────
#   name = "destination_agent"
#       Snake-case identifier matching the table in the root agent's
#       docstring.  ADK uses this for event routing and log prefixes.
#
#   model = "gemini-2.5-flash"
#       Same model as the orchestrator — fast enough for real-time
#       recommendations while maintaining high quality.
#
#   description = "Recommends travel destinations …"
#       One-line summary consumed by the orchestrator's delegation logic.
#       ADK automatically injects sub-agent descriptions into the parent's
#       prompt, so this text directly influences routing accuracy.
#
#   instruction = _INSTRUCTION
#       Full system prompt loaded from
#       ``app/prompts/destination_recommendation.md``.
#
#   tools = [get_maps_toolset()]
#       Connects to Google Maps Grounding Lite MCP, providing the agent
#       with search_places, lookup_weather, and compute_routes tools
#       for real-time geospatial data.
#
#   output_key = "destination_recommendation"
#       Persists the agent's final response into
#       ``session.state["destination_recommendation"]``.  This allows
#       downstream agents (e.g. itinerary_agent) to reference the
#       recommended destinations via ``{destination_recommendation}``
#       in their own instructions.
# ──────────────────────────────────────────────────────────────────────────────

destination_agent = Agent(
    name="destination_agent",
    model="gemini-2.5-flash",
    description=(
        "Recommends up to three travel destinations based on the user's "
        "budget, travel dates, trip duration, and interests."
    ),
    instruction=_INSTRUCTION,
    generate_content_config=_GENERATE_CONTENT_CONFIG,
    tools=[get_maps_toolset()],
    output_key="destination_recommendation",
)
