"""API unit tests: keep paid network planes off unless a test opts in."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_paid_planes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid live Cognee/Speechmatics/Neo4j calls hanging unit tests.

    Live E2E uses a real API process with .env loaded — not this suite.
    """
    monkeypatch.setenv("VERGE_COGNEE_ENABLED", "false")
    monkeypatch.delenv("COGNEE_API_KEY", raising=False)
    monkeypatch.delenv("COGNEE_BASE_URL", raising=False)
    monkeypatch.delenv("COGNEE_SERVICE_URL", raising=False)
    monkeypatch.delenv("SPEECHMATICS_API_KEY", raising=False)
    monkeypatch.delenv("NEO4J_URI", raising=False)
    monkeypatch.setenv("VERGE_VOICE_AUTO_FUSE", "false")
