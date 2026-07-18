"""Best-effort memory-ingest hooks: never raise, no-op when memory is off."""

from __future__ import annotations

from verge_api.hooks import maybe_ingest_near_miss
from verge_memory.client import CogneeResult


def test_maybe_ingest_near_miss_noop_when_memory_disabled(monkeypatch) -> None:
    monkeypatch.setenv("VERGE_COGNEE_ENABLED", "false")
    monkeypatch.delenv("COGNEE_API_KEY", raising=False)
    out = maybe_ingest_near_miss(
        "gas near miss in B-04", structured={"summary": "gas near miss"}
    )
    assert out["degraded"] is True


def test_maybe_ingest_near_miss_noop_on_empty_transcript(monkeypatch) -> None:
    monkeypatch.setenv("VERGE_COGNEE_ENABLED", "true")
    out = maybe_ingest_near_miss("   ", structured={})
    assert out["degraded"] is True
    assert out["reason"] == "cognee-disabled-or-empty"


def test_maybe_ingest_near_miss_swallows_client_errors(monkeypatch) -> None:
    monkeypatch.setenv("VERGE_COGNEE_ENABLED", "true")
    monkeypatch.setenv("COGNEE_API_KEY", "")
    # Must not propagate any exception into the caller (best-effort, P4).
    out = maybe_ingest_near_miss(
        "gas near miss in B-04",
        structured={"summary": "gas", "hazards": ["gas"], "zones": ["B-04"], "actions": []},
        finding_id="F-1",
    )
    assert out["degraded"] is True


def test_maybe_ingest_near_miss_calls_ingest_and_cognify_when_enabled(monkeypatch) -> None:
    calls: list[tuple] = []

    def fake_ingest_and_cognify(client, dataset, title, body):
        calls.append((dataset, title, body))
        return CogneeResult.success({"ok": True})

    class _Settings:
        ready = True

        def missing_reason(self):
            return None

    class _Ready:
        settings = _Settings()

    monkeypatch.setenv("VERGE_COGNEE_ENABLED", "true")
    monkeypatch.setenv("VERGE_SITE_ID", "test-site")
    monkeypatch.setenv("COGNEE_API_KEY", "test-key")
    monkeypatch.setenv("COGNEE_BASE_URL", "https://example.cognee.ai")
    monkeypatch.setattr("verge_api.hooks.ingest_and_cognify", fake_ingest_and_cognify)
    monkeypatch.setattr(
        "verge_api.hooks.CogneeClient.from_env", staticmethod(lambda env: _Ready())
    )

    structured = {
        "summary": "gas near miss",
        "hazards": ["gas"],
        "zones": ["B-04"],
        "actions": ["pause"],
    }
    out = maybe_ingest_near_miss(
        "gas near miss in B-04, pause work", structured=structured, finding_id="F-1",
    )

    assert out["degraded"] is False
    assert len(calls) == 1
    dataset, title, body = calls[0]
    assert "F-1" in title
    assert "gas" in body.lower()
    assert "B-04" in body
