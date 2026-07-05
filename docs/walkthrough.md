# Travel Concierge Agent — Code Walkthrough

## Files Changed / Created

| File | Action | Purpose |
|---|---|---|
| [agent.py](file:///Users/mohammedathar/Desktop/agy2-projects/TravelAgent/travel-concierge/app/agent.py) | Rewritten | Orchestrator agent definition with external prompt loading |
| [travel_concierge.md](file:///Users/mohammedathar/Desktop/agy2-projects/TravelAgent/travel-concierge/app/prompts/travel_concierge.md) | **New** | System prompt as standalone Markdown |
| [prompts/\_\_init\_\_.py](file:///Users/mohammedathar/Desktop/agy2-projects/TravelAgent/travel-concierge/app/prompts/__init__.py) | **New** | Makes `prompts/` a Python package |

---

## Project Structure (updated)

```
app/
├── __init__.py          # App wiring (imports root_agent, initialises logging)
├── agent.py             # root_agent definition + prompt loader
├── config.py            # Environment variable loading
├── logging_config.py    # Structured logging setup
├── tools.py             # Placeholder for custom tool functions
└── prompts/
    ├── __init__.py      # Package marker
    └── travel_concierge.md  # ← NEW: System prompt for the orchestrator
```

---

## agent.py — Section-by-Section Explanation

### Section 1: Prompt Loading ([L58–L82](file:///Users/mohammedathar/Desktop/agy2-projects/TravelAgent/travel-concierge/app/agent.py#L58-L82))

```python
_PROMPT_DIR = Path(__file__).resolve().parent / "prompts"

def _load_prompt(filename: str) -> str:
    path = _PROMPT_DIR / filename
    return path.read_text(encoding="utf-8")

_INSTRUCTION = _load_prompt("travel_concierge.md")
```

**Why a separate file instead of a Python string?**

| Concern | Embedded string | External `.md` file |
|---|---|---|
| **Readability** | Triple-quoted strings with escaped chars | Clean Markdown with syntax highlighting |
| **Editing** | Requires Python knowledge | Anyone can edit Markdown |
| **Code review** | Diffs mix prompt changes with code changes | Prompt diffs are isolated and clean |
| **Tooling** | No Markdown linting/preview | Standard Markdown editors/linters work |
| **Reuse** | One file per agent | Prompts can be shared across agents |

**Why `Path(__file__).resolve().parent`?** Uses the module's own filesystem location to resolve the path, so it works regardless of the working directory (`adk web`, `adk run`, `uv run`, etc. all invoke from different CWDs).

---

### Section 2: Generation Config ([L84–L106](file:///Users/mohammedathar/Desktop/agy2-projects/TravelAgent/travel-concierge/app/agent.py#L84-L106))

```python
_GENERATE_CONTENT_CONFIG = genai_types.GenerateContentConfig(
    temperature=0.4,
    max_output_tokens=8192,
    top_p=0.9,
)
```

| Parameter | Value | Why this value for an orchestrator |
|---|---|---|
| `temperature` | `0.4` | The orchestrator makes **routing decisions** (which sub-agent to call, what data to collect). These must be deterministic. A specialist agent doing creative destination writing would use 0.7–1.0. |
| `max_output_tokens` | `8192` | The orchestrator combines outputs from up to 3 sub-agents into one response. 8K tokens prevents mid-plan truncation. |
| `top_p` | `0.9` | Tighter nucleus sampling than the default 0.95. Creative diversity is the sub-agents' job, not the coordinator's. |

---

### Section 3: Agent Constructor ([L108–L164](file:///Users/mohammedathar/Desktop/agy2-projects/TravelAgent/travel-concierge/app/agent.py#L108-L164))

```python
root_agent = Agent(
    name="travel_concierge",
    model="gemini-2.0-flash",
    description="Orchestrates travel planning by coordinating specialist agents ...",
    instruction=_INSTRUCTION,
    generate_content_config=_GENERATE_CONTENT_CONFIG,
    sub_agents=[],
    tools=[],
    output_key="last_response",
)
```

| Field | Value | Why |
|---|---|---|
| `name` | `"travel_concierge"` | Snake-case internal ID used by ADK for routing, logging, and session state keys. Must be unique among sibling agents. |
| `model` | `"gemini-2.0-flash"` | Gemini 2.0 Flash on Vertex AI — fast latency for real-time orchestration, capable enough for multi-step delegation logic. Uses Application Default Credentials (no API key needed). |
| `description` | `"Orchestrates travel planning…"` | Read by **parent agents** or `AgentTool` wrappers when deciding whether to delegate to this agent. Kept to one sentence. |
| `instruction` | `_INSTRUCTION` | Loaded from `app/prompts/travel_concierge.md`. Contains the full system prompt with 6 sections. |
| `generate_content_config` | `_GENERATE_CONTENT_CONFIG` | Low-temperature, tight-top_p sampling tuned for orchestration. |
| `sub_agents` | `[]` | Placeholder. Once implemented, specialist agents will be listed here and ADK auto-generates delegation routing from their `name` + `description`. |
| `tools` | `[]` | The orchestrator has no tools — sub-agents carry their own domain-specific tools. |
| `output_key` | `"last_response"` | Persists the final response to `session.state["last_response"]`, making it readable by downstream agents via `{last_response}` in their instructions. |

> [!NOTE]
> The variable **must** be named `root_agent` — this is the name ADK's discovery mechanism looks for when loading an agent package.

---

## System Prompt — Section-by-Section Explanation

The prompt in [travel_concierge.md](file:///Users/mohammedathar/Desktop/agy2-projects/TravelAgent/travel-concierge/app/prompts/travel_concierge.md) has **6 sections**:

### 1. Identity
Establishes the agent's role as an **orchestrator, not a domain expert**. The phrase "You do **not** research destinations, build itineraries, or estimate budgets yourself" is the single most important sentence — without it, Gemini will answer domain questions directly instead of delegating.

### 2. Responsibilities
Defines the 4-step workflow (welcome → collect → delegate → combine) and lists **7 data collection points** as a structured table:

| Data Point | Why |
|---|---|
| Departure location | Flight routing, travel time |
| Destination preference | Guides `destination_agent` |
| Travel dates | Seasonality, pricing |
| Trip duration | Itinerary depth |
| Budget | Constraints for `budget_agent` |
| Number of travelers | Room types, per-person costs |
| Interests | Activity focus |

The "max 3 questions at a time" rule prevents the agent from firing 7 questions at once.

### 3. Decision Making
A 3-step decision tree the LLM follows every turn:
1. Do I have enough info? → Ask or delegate
2. Which agent? → Route by topic
3. Revision? → Re-delegate only the affected agent

### 4. Delegation Rules
The mechanical rules that prevent the orchestrator from doing a specialist's job. The **logical ordering** (destination → itinerary → budget) ensures each agent has the previous agent's output as context.

### 5. Safety & Integrity
Non-negotiable constraints: no fabrication, no assumptions about missing data, facts vs. estimates distinction, privacy limits.

### 6. Output Style
Formatting directives for the combined response: Markdown, section-header emojis, currency symbols, per-person vs. total labeling.

---

## Verification Results

| Check | Result |
|---|---|
| Prompt file loads | ✅ 4,850 chars / ~678 words |
| All 6 prompt sections present | ✅ |
| All 7 data points referenced | ✅ |
| All 3 sub-agent names referenced | ✅ |
| `ruff check app/` | ✅ All checks passed |
| `from app import app, root_agent` | ✅ Imports OK |

---

## What's Next

The `sub_agents=[]` list is empty. To enable actual delegation, the next step is to create the three specialist agents:

```
app/
└── sub_agents/
    ├── __init__.py
    ├── destination_agent.py   # destination_agent
    ├── itinerary_agent.py     # itinerary_agent
    └── budget_agent.py        # budget_agent
```

Each would define an `Agent` with its own prompt, tools, and model config, then be imported and registered in `agent.py`:

```python
from app.sub_agents.destination_agent import destination_agent
from app.sub_agents.itinerary_agent import itinerary_agent
from app.sub_agents.budget_agent import budget_agent

root_agent = Agent(
    ...
    sub_agents=[destination_agent, itinerary_agent, budget_agent],
)
```
