"""Travel Budget sub-agent.

This module defines ``budget_agent`` — the specialist responsible for
estimating trip costs once a destination has been selected.

Responsibilities
────────────────
The budget agent:

    1. Receives a selected destination (typically from the orchestrator
       after the destination agent has run).
    2. Produces an itemised cost estimate covering flights, accommodation,
       food, local transportation, and activities.
    3. Clearly disclaims that all figures are estimates.

It does **not** recommend destinations or build day-by-day itineraries —
those tasks belong to the destination and itinerary agents respectively.

Integration with the Travel Concierge
──────────────────────────────────────
This agent is designed to be imported by ``agent.py`` and registered as a
sub-agent of the root ``travel_concierge`` orchestrator::

    from app.budget_agent import budget_agent

    root_agent = Agent(
        ...,
        sub_agents=[destination_agent, budget_agent],
    )

ADK uses the agent's ``name`` and ``description`` fields to build delegation
prompts, so both are kept concise and accurate.

Prompt loading
──────────────
The system instruction is loaded from ``app/prompts/budget.md``.
See the root ``agent.py`` docstring for the rationale behind external prompt
files.
"""

from __future__ import annotations

from pathlib import Path

from google.adk.agents import Agent
from google.genai import types as genai_types

# ──────────────────────────────────────────────────────────────────────────────
# 1. Load the system instruction from the shared prompts directory
# ──────────────────────────────────────────────────────────────────────────────

_PROMPT_DIR = Path(__file__).resolve().parent / "prompts"


def _load_prompt(filename: str) -> str:
    """Read a prompt file from the ``app/prompts/`` directory.

    Args:
        filename: Name of the Markdown file (e.g. ``"budget.md"``).

    Returns:
        The file contents as a string.

    Raises:
        FileNotFoundError: If the prompt file does not exist.
    """
    path = _PROMPT_DIR / filename
    return path.read_text(encoding="utf-8")


_INSTRUCTION = _load_prompt("budget.md")

# ──────────────────────────────────────────────────────────────────────────────
# 2. Model generation configuration
# ──────────────────────────────────────────────────────────────────────────────
# These parameters are tuned for a *factual estimation* specialist:
#
#   temperature = 0.3
#       Lower than the destination agent (0.7) and the orchestrator (0.4).
#       Budget estimates should be consistent and grounded — creative flair
#       is counterproductive when producing cost figures.
#
#   max_output_tokens = 4096
#       A structured cost breakdown with five categories plus a total fits
#       comfortably in 4K tokens.
#
#   top_p = 0.85
#       Tighter than the destination agent to keep numerical outputs
#       focused and reduce variance across runs.
# ──────────────────────────────────────────────────────────────────────────────

_GENERATE_CONTENT_CONFIG = genai_types.GenerateContentConfig(
    temperature=0.3,
    max_output_tokens=4096,
    top_p=0.85,
)

# ──────────────────────────────────────────────────────────────────────────────
# 3. Budget agent definition
# ──────────────────────────────────────────────────────────────────────────────
#   name = "budget_agent"
#       Snake-case identifier matching the table in the root agent's
#       docstring.  ADK uses this for event routing and log prefixes.
#
#   model = "gemini-2.5-flash"
#       Same model as the other agents — fast enough for real-time
#       estimation while maintaining high quality.
#
#   description = "Estimates total trip cost …"
#       One-line summary consumed by the orchestrator's delegation logic.
#       ADK automatically injects sub-agent descriptions into the parent's
#       prompt, so this text directly influences routing accuracy.
#
#   instruction = _INSTRUCTION
#       Full system prompt loaded from ``app/prompts/budget.md``.
#
#   tools = []
#       No tools yet.  Future iterations may add pricing APIs or
#       currency-conversion tools.
#
#   output_key = "budget_estimate"
#       Persists the agent's final response into
#       ``session.state["budget_estimate"]``.  This allows downstream
#       agents or the orchestrator to reference the estimate via
#       ``{budget_estimate}`` in their instructions.
# ──────────────────────────────────────────────────────────────────────────────

budget_agent = Agent(
    name="budget_agent",
    model="gemini-2.5-flash",
    description=(
        "Estimates the total trip cost for a selected destination, covering "
        "flights, accommodation, food, transportation, and activities."
    ),
    instruction=_INSTRUCTION,
    generate_content_config=_GENERATE_CONTENT_CONFIG,
    tools=[],
    output_key="budget_estimate",
)
