"""Release bundle verification tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from verge_supplychain import inspect_bundle, verify_bundle
from verge_supplychain.signatures import sign_hmac

ROOT = Path(__file__).resolve().parents[3] / "deploy" / "bundles" / "demo-0.3.0"
SECRET = "verge-dev-bundle-secret"


@pytest.fixture(scope="module", autouse=True)
def _ensure_demo_sig() -> None:
    manifest = (ROOT / "bundle.manifest.json").read_bytes()
    sig = sign_hmac(manifest, SECRET)
    (ROOT / "bundle.manifest.sig.json").write_text(
        json.dumps({"algorithm": "hmac-sha256", "signature": sig}, indent=2) + "\n",
        encoding="utf-8",
    )


def test_inspect_demo_bundle() -> None:
    info = inspect_bundle(ROOT)
    assert info["version"] == "0.3.0"
    assert info["components"] == 2


def test_verify_demo_bundle_with_hmac_secret() -> None:
    report = verify_bundle(ROOT, env={"VERGE_BUNDLE_HMAC_SECRET": SECRET})
    assert report["configured"] is True
    assert report["verified"] is True
    assert report["digestsOk"] is True
    assert report["signature"]["verified"] is True


def test_verify_fails_on_tampered_manifest(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "components").mkdir()
    (bundle / "components" / "a.txt").write_text("hello", encoding="utf-8")
    manifest = {
        "version": "9.9.9",
        "builtAt": "2026-01-01T00:00:00+00:00",
        "components": [{"path": "components/a.txt", "digest": "sha256:deadbeef"}],
    }
    (bundle / "bundle.manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    sig = sign_hmac((bundle / "bundle.manifest.json").read_bytes(), SECRET)
    (bundle / "bundle.manifest.sig.json").write_text(
        json.dumps({"algorithm": "hmac-sha256", "signature": sig}),
        encoding="utf-8",
    )
    report = verify_bundle(bundle, env={"VERGE_BUNDLE_HMAC_SECRET": SECRET})
    assert report["verified"] is False
    assert report["digestsOk"] is False
