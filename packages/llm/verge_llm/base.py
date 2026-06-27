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
    role: str  # system | user | assistant
    content: str


@dataclass(frozen=True)
class Completion:
    text: str
    model: str
    degraded: bool = False
    reason: str | None = None
    usage: dict[str, int] = field(default_factory=dict)


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

    def healthy(self) -> bool: ...
