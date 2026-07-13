"""The provider contract.

Verge's safety core never depends on an LLM (P1). LLM-backed components (RAG
narrative, orchestrator messaging, optional CV enrichment) go through this one
interface so the model can be cloud (aimlapi) or on-prem (Ollama/vLLM) with no
code change (P2).

Every call returns a `Completion`. If the provider is unreachable, providers do
NOT raise into the caller -- they return a `Completion` with `degraded=True` and
a `last_known`/template fallback, so the console can show the §10.6 banner
("AI narrative: degraded") while the safety core keeps running.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Message:
    role: str  # system | user | assistant | tool
    # str for text-only messages (every existing call site). A vision-capable
    # caller (e.g. the PPE crop classifier in verge_vision) may pass the
    # OpenAI-style multimodal content-parts list instead --
    # ``[{"type": "text", ...}, {"type": "image_url", "image_url": {...}}]``
    # -- which OpenAICompatProvider forwards to the API verbatim either way.
    content: str | list[dict]
    # Tool-calling plumbing (OpenAI wire shape). ``tool_call_id`` marks a
    # role="tool" result message; ``tool_calls`` echoes an assistant turn that
    # requested tools (the API requires it in the follow-up transcript).
    tool_call_id: str | None = None
    tool_calls: tuple[dict, ...] | None = None


@dataclass(frozen=True)
class ToolCall:
    """One tool invocation requested by the model (arguments already parsed)."""

    id: str
    name: str
    arguments: dict
    raw: dict = field(default_factory=dict)  # verbatim wire form for echo-back


@dataclass(frozen=True)
class Completion:
    text: str
    model: str
    degraded: bool = False
    reason: str | None = None
    usage: dict[str, int] = field(default_factory=dict)
    tool_calls: tuple[ToolCall, ...] = ()


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> Completion: ...

    def chat(
        self,
        messages: list[Message],
        *,
        tools: list[dict] | None = None,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> Completion: ...

    def healthy(self) -> bool: ...
