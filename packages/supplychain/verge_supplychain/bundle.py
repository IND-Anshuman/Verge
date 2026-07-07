"""Release bundle manifest verification (spec §14.6, IEC 62443 SBOM)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .signatures import verify_manifest_signature

MANIFEST_NAME = "bundle.manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_digest(value: str) -> str:
    return value.lower().removeprefix("sha256:")


def bundle_root(env: dict[str, str] | None = None) -> Path | None:
    env = env or dict(os.environ)
    raw = env.get("VERGE_BUNDLE_ROOT")
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_dir() else None


def load_manifest(root: Path) -> dict[str, Any]:
    path = root / MANIFEST_NAME
    if not path.exists():
        raise FileNotFoundError(MANIFEST_NAME)
    return json.loads(path.read_text(encoding="utf-8"))


def verify_component_digests(root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for comp in manifest.get("components", []):
        rel = comp["path"]
        expected = _normalize_digest(str(comp.get("digest", "")))
        file_path = root / rel
        if not file_path.exists():
            results.append({
                "path": rel,
                "ok": False,
                "reason": "missing",
            })
            continue
        actual = sha256_file(file_path)
        ok = actual == expected
        results.append({
            "path": rel,
            "ok": ok,
            "expected": expected,
            "actual": actual if not ok else expected,
        })
    return results


def inspect_bundle(root: Path) -> dict[str, Any]:
    """Return manifest metadata without verifying signatures."""
    manifest = load_manifest(root)
    return {
        "root": str(root),
        "version": manifest.get("version"),
        "builtAt": manifest.get("builtAt"),
        "siteProfile": manifest.get("siteProfile"),
        "components": len(manifest.get("components", [])),
        "sbom": manifest.get("sbom"),
    }


def verify_bundle(root: Path | None = None, *, env: dict[str, str] | None = None) -> dict[str, Any]:
    """Verify manifest signature and per-component SHA-256 digests."""
    env = env or dict(os.environ)
    root = root or bundle_root(env)
    if root is None:
        return {
            "configured": False,
            "verified": None,
            "reason": "VERGE_BUNDLE_ROOT not configured",
        }

    manifest_path = root / MANIFEST_NAME
    if not manifest_path.exists():
        return {
            "configured": True,
            "verified": False,
            "root": str(root),
            "reason": f"{MANIFEST_NAME} missing",
        }

    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    signature = verify_manifest_signature(root, manifest_bytes, env=env)
    components = verify_component_digests(root, manifest)
    digests_ok = all(item["ok"] for item in components) if components else True
    verified = bool(signature.get("verified")) and digests_ok

    return {
        "configured": True,
        "root": str(root),
        "version": manifest.get("version"),
        "builtAt": manifest.get("builtAt"),
        "sbom": manifest.get("sbom"),
        "signature": signature,
        "components": components,
        "digestsOk": digests_ok,
        "verified": verified,
    }
