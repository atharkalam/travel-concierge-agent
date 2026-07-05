"""End-to-end smoke test for the Travel Concierge multi-agent system.

Sends three targeted queries through the orchestrator and verifies that
each one delegates to the correct specialist sub-agent by inspecting
the ADK event stream for agent transfer events.

Usage:
    python tests/e2e_delegation_test.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure the project root is on sys.path so `app` is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from app.agent import root_agent

# ──────────────────────────────────────────────────────────────────────────────
# Test configuration
# ──────────────────────────────────────────────────────────────────────────────

APP_NAME = "travel_concierge_test"
USER_ID = "test_user"

# Each test case: (description, user message, expected sub-agent name)
TEST_CASES = [
    (
        "Destination delegation",
        "I have a $3,000 budget and 10 days in December. I love beaches and snorkeling. "
        "What destinations do you recommend?",
        "destination_agent",
    ),
    (
        "Itinerary delegation",
        "I've decided on Bali. Create a 5-day itinerary for me.",
        "itinerary_agent",
    ),
    (
        "Budget delegation",
        "How much will a 5-day trip to Bali cost for 2 people?",
        "budget_agent",
    ),
]


# ──────────────────────────────────────────────────────────────────────────────
# Runner helper
# ──────────────────────────────────────────────────────────────────────────────


async def run_single_test(
    runner: Runner,
    session_id: str,
    description: str,
    user_message: str,
    expected_agent: str,
) -> bool:
    """Send a message and check which agent(s) responded.

    Returns True if the expected agent was observed in the event stream.
    """
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"  Query: {user_message[:80]}...")
    print(f"  Expecting delegation to: {expected_agent}")
    print(f"{'='*70}")

    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=user_message)],
    )

    agents_seen: list[str] = []
    final_text = ""

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=content,
    ):
        # Track which agents produced events
        if hasattr(event, "author") and event.author:
            if event.author not in agents_seen:
                agents_seen.append(event.author)

        # Capture final response text
        if event.is_final_response():
            if event.content and event.content.parts:
                final_text = event.content.parts[0].text or ""

    delegated = expected_agent in agents_seen

    print(f"\n  Agents in event stream: {agents_seen}")
    print(f"  Delegation to {expected_agent}: {'✅ YES' if delegated else '❌ NO'}")
    if final_text:
        # Show first 300 chars of the response
        preview = final_text[:300].replace("\n", "\n    ")
        print(f"  Response preview:\n    {preview}...")

    return delegated


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────


async def main() -> None:
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    results: list[tuple[str, bool]] = []

    for i, (description, message, expected_agent) in enumerate(TEST_CASES):
        # Use a separate session per test to avoid context bleed
        session_id = f"test_session_{i}"
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )

        passed = await run_single_test(
            runner=runner,
            session_id=session.id,
            description=description,
            user_message=message,
            expected_agent=expected_agent,
        )
        results.append((description, passed))

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"\n\n{'='*70}")
    print("RESULTS SUMMARY")
    print(f"{'='*70}")
    all_passed = True
    for desc, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {desc}")
        if not passed:
            all_passed = False

    print(f"\n{'='*70}")
    if all_passed:
        print("🎉 All delegation tests passed!")
    else:
        print("⚠️  Some tests failed — check output above for details.")
    print(f"{'='*70}\n")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
