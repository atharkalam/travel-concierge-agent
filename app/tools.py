"""Custom tool functions for the Travel Concierge agents.

ADK Tool Rules:
    - Use clear docstrings (they are sent to the LLM as tool descriptions).
    - All parameters must have type hints; do NOT use default values.
    - Return a dict (JSON-serializable).
    - Do NOT mention `tool_context` in the docstring.
    - Use `ToolContext` for state access, artifacts, or escalation.

Example:
    from google.adk.tools import ToolContext

    def search_flights(origin: str, destination: str, date: str) -> dict:
        \"\"\"Search for available flights between two airports on a given date.

        Args:
            origin: IATA airport code for departure (e.g., "SFO").
            destination: IATA airport code for arrival (e.g., "NRT").
            date: Travel date in YYYY-MM-DD format.

        Returns:
            dict with 'status' and 'flights' keys.
        \"\"\"
        # Implementation here
        return {"status": "success", "flights": []}
"""

# TODO: Add tool functions here when agent development begins.
