"""Signed bundle ops routes."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from verge_api.main import app

client = TestClient(app)
DEMO_ROOT = Path(__file__).resolve().parents[3] / "deploy" / "bundles" / "demo-0.3.0"


@pytest.fixture(autouse=True)
def _bundle_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERGE_BUNDLE_ROOT", str(DEMO_ROOT))
    monkeypatch.setenv("VERGE_BUNDLE_HMAC_SECRET", "verge-dev-bundle-secret")


def test_ops_bundle_verify_endpoint() -> None:
    body = client.get("/api/ops/bundle/verify").json()
    assert body["configured"] is True
    assert body["verified"] is True


def test_ops_status_includes_bundle_verification() -> None:
    body = client.get("/api/ops/status").json()
    verification = body["signedBundle"]["verification"]
    assert verification["verified"] is True
    assert body["signedBundle"]["builtTs"] is not None
