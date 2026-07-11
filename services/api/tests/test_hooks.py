"""Best-effort memory-ingest hooks: never raise, no-op when memory is off."""

from __future__ import annotations

from verge_api.hooks import maybe_ingest_near_miss


def test_maybe_ingest_near_miss_noop_when_memory_disabled(monkeypatch) -> None:
    monkeypatch.delenv("VERGE_COGNEE_ENABLED", raising=False)
    # No network configured at all -- must not raise.
    maybe_ingest_near_miss("gas near miss in B-04", structured={"summary": "gas near miss"})


def test_maybe_ingest_near_miss_noop_on_empty_transcript(monkeypatch) -> None:
    monkeypatch.setenv("VERGE_COGNEE_ENABLED", "true")
    maybe_ingest_near_miss("   ", structured={})


def test_maybe_ingest_near_miss_swallows_client_errors(monkeypatch) -> None:
    monkeypatch.setenv("VERGE_COGNEE_ENABLED", "true")
    # unreachable/misconfigured -> the underlying client raises or degrades
    monkeypatch.setenv("COGNEE_API_KEY", "")
    # Must not propagate any exception into the caller (best-effort, P4).
    maybe_ingest_near_miss(
        "gas near miss in B-04",
        structured={"summary": "gas", "hazards": ["gas"], "zones": ["B-04"], "actions": []},
        finding_id="F-1",
    )


def test_maybe_ingest_near_miss_calls_ingest_document_when_enabled(monkeypatch) -> None:
    calls: list[tuple] = []

    def fake_ingest_document(client, dataset, title, body):
        calls.append((dataset, title, body))
        return None

    monkeypatch.setenv("VERGE_COGNEE_ENABLED", "true")
    monkeypatch.setenv("VERGE_SITE_ID", "test-site")
    monkeypatch.setattr("verge_api.hooks.ingest_document", fake_ingest_document)
    monkeypatch.setattr(
        "verge_api.hooks.CogneeClient.from_env", staticmethod(lambda env: object())
    )

    structured = {
        "summary": "gas near miss", "hazards": ["gas"], "zones": ["B-04"], "actions": ["pause"],
    }
    maybe_ingest_near_miss(
        "gas near miss in B-04, pause work", structured=structured, finding_id="F-1",
    )

    assert len(calls) == 1
    dataset, title, body = calls[0]
    assert "F-1" in title
    assert "gas" in body.lower()
    assert "B-04" in body
