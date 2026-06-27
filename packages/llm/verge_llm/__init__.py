"""Swappable LLM provider abstraction (spec §7, P1/P2)."""

from __future__ import annotations

import os

from .base import Completion, LLMProvider, Message
from .providers import NullProvider, OpenAICompatProvider

__all__ = [
    "Completion",
    "LLMProvider",
    "Message",
    "NullProvider",
    "OpenAICompatProvider",
    "provider_from_env",
]
__version__ = "0.3.0"


def provider_from_env(env: dict[str, str] | None = None) -> LLMProvider:
    """Build the configured provider. Defaults to NullProvider so a fresh
    checkout and the air-gapped safety core run with no credentials."""
    env = env or dict(os.environ)
    kind = env.get("VERGE_LLM_PROVIDER", "null").lower()

    if kind == "aimlapi":
        return OpenAICompatProvider(
            name="aimlapi",
            base_url=env.get("AIMLAPI_BASE_URL", "https://api.aimlapi.com/v1"),
            api_key=env.get("AIMLAPI_API_KEY"),
            default_model=env.get("VERGE_LLM_SYNTHESIS_MODEL", "claude-sonnet-4-5"),
        )
    if kind in {"ollama", "vllm"}:
        return OpenAICompatProvider(
            name=kind,
            base_url=env.get("VERGE_LLM_BASE_URL", "http://localhost:11434/v1"),
            api_key=env.get("VERGE_LLM_API_KEY"),
            default_model=env.get("VERGE_LLM_SYNTHESIS_MODEL", "llama3.1:8b"),
        )
    return NullProvider()
