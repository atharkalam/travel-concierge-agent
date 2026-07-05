"""Root agent definition for the Travel Concierge.

This module defines ``root_agent`` — the **orchestrator** that coordinates
the multi-agent travel concierge system.

Architecture
────────────
The Travel Concierge does NOT perform destination research, itinerary creation,
or budget estimation directly.  Instead, it:

    1. Greets the user and collects travel requirements.
    2. Decides which specialist sub-agent(s) should handle the request.
    3. Delegates to those sub-agents via ADK's ``sub_agents`` mechanism.
    4. Synthesises the sub-agent outputs into one coherent response.

Sub-agents (to be registered in ``sub_agents=[]`` once implemented):

    ============== ========================================
    Agent name      Responsibility
    ============== ========================================
    destination_agent  Destination recommendations
    itinerary_agent    Day-by-day itinerary planning
    budget_agent       Cost estimation and budgeting
    ============== ========================================

Prompt loading
──────────────
The system instruction is loaded from an external Markdown file
(``app/prompts/travel_concierge.md``) rather than being embedded as a Python
string.  This separation provides three benefits:

    - **Readability** — Markdown is easier to review than triple-quoted strings.
    - **Iteration** — Prompt engineers can edit the ``.md`` file without
      touching Python code.
    - **Version control** — Diffs on Markdown are cleaner than diffs inside
      Python strings.

Vertex AI environment variables required (see ``.env.example``):
    GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, GOOGLE_GENAI_USE_VERTEXAI=True
"""

from __future__ import annotations

from pathlib import Path

from google.adk.agents import Agent
from google.genai import types as genai_types

from app.budget_agent import budget_agent
from app.destination_agent import destination_agent
from app.itinerary_agent import itinerary_agent

# ──────────────────────────────────────────────────────────────────────────────
# 1. Load the system instruction from an external Markdown file
# ──────────────────────────────────────────────────────────────────────────────
# Why a separate file?
#   • Keeps agent.py focused on wiring (model, tools, sub-agents).
#   • The .md file can be reviewed, linted, and diffed independently.
#   • Non-engineers (prompt designers) can iterate without Python knowledge.
#
# Path resolution uses __file__ so it works regardless of the working
# directory from which the ADK CLI is invoked.
# ──────────────────────────────────────────────────────────────────────────────

_PROMPT_DIR = Path(__file__).resolve().parent / "prompts"


def _load_prompt(filename: str) -> str:
    """Read a prompt file from the ``app/prompts/`` directory.

    Args:
        filename: Name of the Markdown file (e.g. ``"travel_concierge.md"``).

    Returns:
        The file contents as a string.

    Raises:
        FileNotFoundError: If the prompt file does not exist.
    """
    path = _PROMPT_DIR / filename
    return path.read_text(encoding="utf-8")


_INSTRUCTION = _load_prompt("travel_concierge.md")

# ──────────────────────────────────────────────────────────────────────────────
# 2. Model generation configuration
# ──────────────────────────────────────────────────────────────────────────────
# These parameters control how the LLM generates responses.  They are tuned
# for an orchestrator, which needs different characteristics than a domain
# specialist.
#
#   temperature = 0.4
#       Lower than a creative agent (typically 0.7–1.0).  The orchestrator
#       makes routing decisions (which sub-agent to call, what questions to
#       ask) that must be deterministic and predictable.  0.4 is warm enough
#       for natural-sounding greetings and follow-ups.
#
#   max_output_tokens = 8192
#       The orchestrator synthesises responses from multiple sub-agents into
#       one unified travel plan.  8K tokens provides enough room for a
#       combined destination + itinerary + budget response without truncation.
#
#   top_p = 0.9
#       Slightly tighter than the default (0.95) to keep the orchestrator
#       focused.  Creative diversity is the sub-agents' responsibility, not
#       the coordinator's.
# ──────────────────────────────────────────────────────────────────────────────

_GENERATE_CONTENT_CONFIG = genai_types.GenerateContentConfig(
    temperature=0.4,
    max_output_tokens=8192,
    top_p=0.9,
)

# ──────────────────────────────────────────────────────────────────────────────
# 3. Root agent definition
# ──────────────────────────────────────────────────────────────────────────────
# This is the variable that ADK discovers.  It MUST be named ``root_agent``.
#
#   name = "travel_concierge"
#       Snake-case identifier used internally by ADK for event routing,
#       session state namespacing, and log prefixes.  Does not affect the
#       user-facing persona (that's defined in the prompt file).
#
#   model = "gemini-2.5-flash"
#       Gemini 2.0 Flash via Vertex AI.  Fast enough for real-time
#       orchestration, capable enough for multi-step delegation logic.
#       Requires GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, and
#       GOOGLE_GENAI_USE_VERTEXAI=True to be set in the environment.
#
#   description = "Orchestrates travel planning …"
#       A concise summary consumed by *parent* agents (or tools like
#       AgentTool) when they need to decide whether to route a request
#       to this agent.  Keep it one or two sentences.
#
#   instruction = _INSTRUCTION
#       The full system prompt, loaded from
#       ``app/prompts/travel_concierge.md``.  Defines the agent's persona,
#       data-collection checklist, decision tree, delegation rules, safety
#       constraints, and output formatting.
#
#   generate_content_config = _GENERATE_CONTENT_CONFIG
#       LLM sampling parameters tuned for orchestration (low temperature,
#       tight top_p, generous max tokens).
#
#   sub_agents = [destination_agent, itinerary_agent, budget_agent]
#       All three specialist sub-agents are registered here.
#       ADK reads each sub-agent's ``name`` and ``description`` to build
#       the delegation prompt automatically.
#
#   tools = []
#       The orchestrator has no tools of its own.  The specialist sub-agents
#       carry their own domain-specific tools.  If cross-cutting tools are
#       needed later (e.g. session state helpers), they would go here.
#
#   output_key = "last_response"
#       Persists the orchestrator's final response text into
#       ``session.state["last_response"]``.  This makes the output available
#       to downstream agents in a SequentialAgent or ParallelAgent pipeline,
#       or accessible via ``{last_response}`` in another agent's instruction.
# ──────────────────────────────────────────────────────────────────────────────

root_agent = Agent(
    name="travel_concierge",
    model="gemini-2.5-flash",
    description=(
        "Orchestrates travel planning by coordinating specialist agents "
        "for destinations, itineraries, and budgets."
    ),
    instruction=_INSTRUCTION,
    generate_content_config=_GENERATE_CONTENT_CONFIG,
    sub_agents=[destination_agent, itinerary_agent, budget_agent],
    tools=[],
    output_key="last_response",
)
