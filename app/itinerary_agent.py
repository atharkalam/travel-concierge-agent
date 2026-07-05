"""Itinerary Planning sub-agent.

This module defines ``itinerary_agent`` — the specialist responsible for
building day-by-day travel itineraries once a destination has been selected.

Responsibilities
────────────────
The itinerary agent:

    1. Receives a selected destination (typically from the orchestrator
       after the destination agent has run).
    2. Produces a structured day-by-day plan covering daily activities,
       suggested attractions, meal breaks, and transportation tips.
    3. Balances sightseeing with rest to keep the plan realistic.

It does **not** recommend destinations or estimate trip costs — those
tasks belong to the destination and budget agents respectively.

Integration with the Travel Concierge
──────────────────────────────────────
This agent is designed to be imported by ``agent.py`` and registered as a
sub-agent of the root ``travel_concierge`` orchestrator::

    from app.itinerary_agent import itinerary_agent

    root_agent = Agent(
        ...,
        sub_agents=[destination_agent, itinerary_agent, budget_agent],
    )

ADK uses the agent's ``name`` and ``description`` fields to build delegation
prompts, so both are kept concise and accurate.

Prompt loading
──────────────
The system instruction is loaded from ``app/prompts/itinerary.md``.
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
        filename: Name of the Markdown file (e.g. ``"itinerary.md"``).

    Returns:
        The file contents as a string.

    Raises:
        FileNotFoundError: If the prompt file does not exist.
    """
    path = _PROMPT_DIR / filename
    return path.read_text(encoding="utf-8")


_INSTRUCTION = _load_prompt("itinerary.md")

# ──────────────────────────────────────────────────────────────────────────────
# 2. Model generation configuration
# ──────────────────────────────────────────────────────────────────────────────
# These parameters are tuned for a *structured planning* specialist:
#
#   temperature = 0.5
#       A middle ground between the creative destination agent (0.7) and the
#       factual budget agent (0.3).  Itineraries need enough variety to feel
#       personalised, but enough structure to produce a coherent day-by-day
#       plan that balances sightseeing with rest.
#
#   max_output_tokens = 8192
#       Multi-day itineraries can be lengthy — each day includes activities,
#       attractions, meal recommendations, and transport notes.  8K tokens
#       provides ample room for trips up to ~10 days without truncation.
#
#   top_p = 0.9
#       Matches the orchestrator.  Broad enough for interesting activity
#       suggestions while keeping the plan well-organised.
# ──────────────────────────────────────────────────────────────────────────────

_GENERATE_CONTENT_CONFIG = genai_types.GenerateContentConfig(
    temperature=0.5,
    max_output_tokens=8192,
    top_p=0.9,
)

# ──────────────────────────────────────────────────────────────────────────────
# 3. Itinerary agent definition
# ──────────────────────────────────────────────────────────────────────────────
#   name = "itinerary_agent"
#       Snake-case identifier matching the table in the root agent's
#       docstring.  ADK uses this for event routing and log prefixes.
#
#   model = "gemini-2.5-flash"
#       Same model as the other agents — fast enough for real-time
#       planning while maintaining high quality.
#
#   description = "Creates a day-by-day itinerary …"
#       One-line summary consumed by the orchestrator's delegation logic.
#       ADK automatically injects sub-agent descriptions into the parent's
#       prompt, so this text directly influences routing accuracy.
#
#   instruction = _INSTRUCTION
#       Full system prompt loaded from ``app/prompts/itinerary.md``.
#
#   tools = [get_maps_toolset()]
#       Connects to Google Maps Grounding Lite MCP, providing the agent
#       with search_places, compute_routes, and lookup_weather tools
#       for real-time geospatial data during itinerary planning.
#
#   output_key = "itinerary_plan"
#       Persists the agent's final response into
#       ``session.state["itinerary_plan"]``.  This allows downstream
#       agents (e.g. budget_agent) or the orchestrator to reference
#       the plan via ``{itinerary_plan}`` in their instructions.
# ──────────────────────────────────────────────────────────────────────────────

itinerary_agent = Agent(
    name="itinerary_agent",
    model="gemini-2.5-flash",
    description=(
        "Creates a day-by-day travel itinerary for a selected destination, "
        "including daily activities, attractions, meal breaks, and "
        "transportation suggestions."
    ),
    instruction=_INSTRUCTION,
    generate_content_config=_GENERATE_CONTENT_CONFIG,
    tools=[get_maps_toolset()],
    output_key="itinerary_plan",
)
