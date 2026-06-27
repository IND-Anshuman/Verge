"""Concrete providers. All OpenAI-compatible chat-completions shape.

- AimlapiProvider  : cloud gateway (hackathon default)
- OpenAICompatProvider : on-prem Ollama / vLLM (air-gap)
- NullProvider     : deterministic echo; the safe default and the test double
"""

from __future__ import annotations

from .base import Completion, Message


class NullProvider:
    """No network. Returns a deterministic, clearly-labeled stub.

    This is the default when VERGE_LLM_PROVIDER is unset or `null`, so a fresh
    checkout and the air-gapped safety core both run with zero credentials.
    """

    name = "null"

    def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> Completion:
        last = messages[-1].content if messages else ""
        return Completion(
            text=f"[null-provider] narrative unavailable; echo: {last[:160]}",
            model=model or "null",
            degraded=True,
            reason="null provider (no LLM configured)",
        )

    def healthy(self) -> bool:
        return True


class OpenAICompatProvider:
    """Talks to any OpenAI-compatible /chat/completions endpoint.

    Used for aimlapi (cloud) and Ollama/vLLM (on-prem) alike -- only base_url,
    api_key and default model differ. httpx is imported lazily so the package
    has no hard runtime dependency in air-gapped, LLM-free deployments.
    """

    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        api_key: str | None,
        default_model: str,
        timeout_s: float = 20.0,
    ) -> None:
        self.name = name
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._default_model = default_model
        self._timeout_s = timeout_s

    def _client(self):
        import httpx  # lazy: only needed when an LLM is actually configured

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return httpx.Client(base_url=self._base_url, headers=headers, timeout=self._timeout_s)

    def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> Completion:
        mdl = model or self._default_model
        body = {
            "model": mdl,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        try:
            with self._client() as client:
                resp = client.post("/chat/completions", json=body)
                resp.raise_for_status()
                data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return Completion(text=text, model=mdl, usage=data.get("usage", {}))
        except Exception as exc:  # degrade, never raise into the safety path (P1)
            return Completion(
                text="",
                model=mdl,
                degraded=True,
                reason=f"{self.name} unreachable: {type(exc).__name__}",
            )

    def healthy(self) -> bool:
        try:
            with self._client() as client:
                client.get("/models")
            return True
        except Exception:
            return False
