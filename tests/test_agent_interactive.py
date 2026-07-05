"""Test the Travel Concierge agent with sample user messages.

Uses the ADK Runner + InMemorySessionService to send messages to the
root_agent and print the agent's responses.  No sub-agents are registered
yet, so the orchestrator will handle everything conversationally.

Usage:
    uv run python tests/test_agent_interactive.py
"""

from __future__ import annotations

import asyncio

from dotenv import load_dotenv

# Load environment variables BEFORE importing ADK / agent code
load_dotenv()

from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types as genai_types  # noqa: E402

from app.agent import root_agent  # noqa: E402

# ──────────────────────────────────────────────────────────────────────────────
# Sample test messages — simulates a multi-turn conversation
# ──────────────────────────────────────────────────────────────────────────────
SAMPLE_MESSAGES: list[str] = [
    # Turn 1: vague opening — the agent should welcome and ask questions
    "Hi! I want to plan a vacation.",
    # Turn 2: provide some details — the agent should collect remaining info
    "I'm flying from San Francisco. I'd love to visit Japan in October for about 10 days.",
    # Turn 3: provide budget and interests — the agent now has enough to delegate
    "My budget is around $5,000. I'm traveling solo and I'm interested in food, temples, and hiking.",
]


async def run_test() -> None:
    """Send sample messages to the agent and print responses."""

    # --- Set up session ---
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="app",
        user_id="test_user",
    )

    # --- Create runner ---
    runner = Runner(
        agent=root_agent,
        app_name="app",
        session_service=session_service,
    )

    print("=" * 70)
    print("  TRAVEL CONCIERGE — Interactive Test")
    print("=" * 70)

    for i, message in enumerate(SAMPLE_MESSAGES, start=1):
        print(f"\n{'─' * 70}")
        print(f"  👤 User (Turn {i}):")
        print(f"  {message}")
        print(f"{'─' * 70}")

        # Build the user message content
        user_content = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=message)],
        )

        # Run the agent and collect the response events
        response_text = ""
        async for event in runner.run_async(
            session_id=session.id,
            user_id="test_user",
            new_message=user_content,
        ):
            # ADK emits multiple events; we want the final agent response
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text = part.text  # keep the last text

        print(f"\n  🤖 Travel Concierge:")
        print()
        # Indent the response for readability
        for line in response_text.split("\n"):
            print(f"    {line}")

    print(f"\n{'=' * 70}")
    print("  Test complete.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(run_test())
