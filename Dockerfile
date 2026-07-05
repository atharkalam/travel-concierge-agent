# =============================================================================
# Dockerfile — Travel Concierge (Google ADK on Cloud Run)
# =============================================================================
# Builds a production container that serves the multi-agent Travel Concierge
# via the ADK API server.
#
# Build:
#   docker build -t travel-concierge .
#
# Run locally:
#   docker run -p 8000:8000 \
#     -e GOOGLE_CLOUD_PROJECT=<project> \
#     -e GOOGLE_CLOUD_LOCATION=us-central1 \
#     -e GOOGLE_GENAI_USE_VERTEXAI=True \
#     -e GOOGLE_MAPS_API_KEY=<key> \
#     travel-concierge
#
# Deploy to Cloud Run:
#   adk deploy cloud_run \
#     --project=<project> --region=us-central1 \
#     --service_name=travel-concierge \
#     app
# =============================================================================

# ---------------------------------------------------------------------------
# Base image
# ---------------------------------------------------------------------------
# Python 3.11 slim — matches pyproject.toml requires-python=">=3.11,<3.13"
FROM python:3.11-slim AS base

# ---------------------------------------------------------------------------
# System dependencies
# ---------------------------------------------------------------------------
# - build-essential: needed by some Python C-extension wheels
# - curl: health-check probe for Cloud Run
# Clean up apt caches in the same layer to keep the image small.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl && \
    rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Non-root user (Cloud Run best practice)
# ---------------------------------------------------------------------------
RUN adduser --disabled-password --gecos "" appuser

WORKDIR /app

# ---------------------------------------------------------------------------
# Install Python dependencies
# ---------------------------------------------------------------------------
# Copy requirements.txt first for Docker layer caching — dependencies change
# less often than agent source code.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Copy agent source code
# ---------------------------------------------------------------------------
# The ADK api_server expects the agent module at /app/agents/<app_name>/
# where <app_name> matches App(name="app") in __init__.py.
COPY app/ /app/agents/app/

# ---------------------------------------------------------------------------
# Switch to non-root user
# ---------------------------------------------------------------------------
RUN chown -R appuser:appuser /app
USER appuser

# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------
# These are defaults for local/dev use.  In Cloud Run, override via
# --set-env-vars or Secret Manager references.
#
# GOOGLE_CLOUD_PROJECT and GOOGLE_MAPS_API_KEY intentionally have NO default
# — they must be provided at runtime.
ENV GOOGLE_GENAI_USE_VERTEXAI=True
ENV GOOGLE_CLOUD_LOCATION=us-central1

# ---------------------------------------------------------------------------
# Expose port and start the ADK Web server
# ---------------------------------------------------------------------------
# Cloud Run expects the container to listen on the port defined by the PORT
# environment variable (defaulting to 8080).
ENV PORT=8080
EXPOSE 8080

# Health-check for Cloud Run / load balancers
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/ || exit 1

CMD ["sh", "-c", "adk web --port=${PORT} --host=0.0.0.0 --session_service_uri=memory:// /app/agents"]
