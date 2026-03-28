"""
Agent voice — uses Claude API to generate personality-rich commentary.

Each agent narrates their actions through their persona.
Falls back to plain descriptions if the API is unavailable.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.agents.personas import PERSONAS

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None
_api_key: str = ""


def init_voice(api_key: str) -> None:
    """Initialize the Claude API client."""
    global _client, _api_key
    _api_key = api_key
    if api_key:
        _client = httpx.AsyncClient(
            base_url="https://api.anthropic.com",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            timeout=15.0,
        )
        logger.info("Agent voice initialized with Claude API")
    else:
        logger.warning("No ANTHROPIC_API_KEY — agents will use plain descriptions")


async def narrate(agent_name: str, context: str) -> str:
    """
    Have an agent narrate their findings/actions in their voice.

    Args:
        agent_name: Rick, Hank, Ron, or Marcus
        context: What happened — data, findings, actions taken

    Returns:
        Personality-rich commentary string
    """
    if not _client or not _api_key:
        return context  # Fallback: plain description

    persona = PERSONAS.get(agent_name)
    if not persona:
        return context

    try:
        resp = await _client.post("/v1/messages", json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 150,
            "system": persona["system_prompt"],
            "messages": [
                {
                    "role": "user",
                    "content": f"Based on this data, give your assessment in your voice. Be specific with numbers. Respond with ONLY your commentary, nothing else.\n\nData:\n{context}",
                }
            ],
        })
        if resp.status_code == 200:
            data = resp.json()
            text = data.get("content", [{}])[0].get("text", "")
            if text:
                return text.strip()
        else:
            logger.warning("Claude API returned %d: %s", resp.status_code, resp.text[:200])
    except Exception as e:
        logger.warning("Claude API error for %s: %s", agent_name, e)

    return context  # Fallback


async def narrate_coordination(context: str) -> str:
    """Marcus-specific: narrate cross-agent coordination."""
    return await narrate("Marcus", context)


async def close_voice() -> None:
    """Cleanup the HTTP client."""
    global _client
    if _client:
        await _client.aclose()
        _client = None
