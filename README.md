# Travel Concierge

Travel Concierge is a multi-agent application powered by the Google Agent Development Kit (ADK). It orchestrates specialized agents to plan vacations, providing personalized destination recommendations, interactive itineraries, and budget tracking—all enhanced by live data via the Google Maps Grounding Lite MCP.

## Overview
This project showcases how to build a robust, scalable agentic application using Google's ADK. The orchestrator agent delegates tasks to specialized sub-agents based on the user's input, creating a seamless conversational experience for planning a complete trip.

## Features
* **Multi-Agent Orchestration**: A root agent intelligently routes user queries to specialized agents.
* **Destination Recommendations**: Tailored travel destination suggestions based on preferences.
* **Itinerary Planning**: Detailed, day-by-day travel schedules.
* **Budget Tracking**: Cost estimations and budget planning.
* **Live Location Data**: Integrates the Google Maps Grounding Lite MCP for real-time place search, nearby attractions, route planning, and weather.
* **Web UI**: Interactive local web interface provided by ADK.

## Multi-Agent Architecture
The application follows a hierarchical structure:
1. **Root Agent (`app`)**: The main entry point that interacts with the user and delegates to sub-agents.
2. **Destination Agent**: Specializes in finding the perfect travel destination.
3. **Itinerary Agent**: Creates detailed, actionable itineraries.
4. **Budget Agent**: Handles financial planning and cost estimation.

## Folder Structure
```text
travel-concierge/
├── app/                      # Application source code
│   ├── agents/               # Agent definitions
│   │   ├── app/              # Root agent
│   │   ├── budget_agent/     # Budget sub-agent
│   │   ├── destination_agent/# Destination sub-agent
│   │   └── itinerary_agent/  # Itinerary sub-agent
│   ├── maps_mcp.py           # Google Maps MCP integration
│   ├── requirements.txt      # Python dependencies for deployment
│   └── ...
├── prompts/                  # Markdown files containing agent instructions
├── .env.example              # Example environment variables
├── Dockerfile                # Containerization for Cloud Run
├── pyproject.toml            # Python project metadata
└── README.md                 # This file
```

## Prerequisites
* Python 3.11+ (matches `requires-python` in `pyproject.toml`)
* `uv` (Python package manager)
* Google Cloud account with Vertex AI enabled
* Google Maps API Key

## Installation

### 1. Clone the repository
```bash
git clone <your-repository-url>
cd travel-concierge
```

### 2. Virtual Environment & Dependencies
We recommend using `uv` for fast dependency management.
```bash
# Create a virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .
```

### 3. Environment Variables
Create a `.env` file in the root directory based on the provided example:
```bash
cp .env.example .env
```
Edit `.env` to include your actual API keys and Google Cloud project details.

### 4. Configure Vertex AI Credentials
Ensure you are authenticated with Google Cloud to use Vertex AI:
```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 5. Obtain a Google Maps API Key
To enable the live data features (MCP), you need a Google Maps API key:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the **Places API (New)** and **Geocoding API**.
3. Go to **APIs & Services > Credentials** and create an API Key.
4. Add the key to your `.env` file as `GOOGLE_MAPS_API_KEY`.

## Running Locally
Start the interactive ADK web interface:
```bash
uv run adk web
```
Open your browser to `http://localhost:8000` to start chatting with the Travel Concierge.

## Example User Prompts
* *"I have a budget of $3000 and want to go somewhere warm for 5 days next month. Can you recommend a destination?"*
* *"Create a 3-day itinerary for Tokyo, including popular attractions and nearby restaurants."*
* *"What's the current weather in Paris, and how much would a weekend trip cost?"*

## MCP Integration Details
This project utilizes the **Google Maps Grounding Lite MCP** via the official Google ADK MCP integration (`McpToolset`). The MCP is attached exclusively to the `destination_agent` and `itinerary_agent`, providing them with secure access to:
* Place search and details
* Nearby attractions
* Route planning
* Weather lookup

## Deployment

### Deploying to Vertex AI Agent Runtime
```bash
# Build and deploy the agent engine
uv run adk deploy agent_engine \
  --project YOUR_PROJECT_ID \
  --region us-central1 \
  --display_name "travel-concierge" \
  app
```
*(Ensure you have configured `GOOGLE_MAPS_API_KEY` in Google Cloud Secret Manager and granted the required permissions).*

### Deploying to Google Cloud Run
The repository includes a `Dockerfile` optimized for Cloud Run.
```bash
gcloud run deploy travel-concierge-web \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID \
  --set-env-vars GOOGLE_CLOUD_LOCATION=us-central1 \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=True \
  --set-secrets GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY:latest
```

## Technologies Used
* **Google Agent Development Kit (ADK)**
* **Google Vertex AI** (Gemini Models)
* **Model Context Protocol (MCP)**
* **Python** (FastAPI, Pydantic)
* **Google Cloud Run** & **Agent Runtime**

## Future Improvements
* Add user authentication and profile management.
* Integrate flight and hotel booking APIs.
* Support multi-modal inputs (e.g., uploading travel inspiration photos).
* Implement long-term memory for returning users.

## License
MIT License. See the `LICENSE` file for details.
