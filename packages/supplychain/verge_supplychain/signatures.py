"""Detached signature verification for release bundles (cosign / dev HMAC)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

ALGO_HMAC = "hmac-sha256"
ALGO_COSIGN = "cosign"


def _read_sig_doc(root: Path) -> dict[str, Any] | None:
    for name in ("bundle.manifest.sig.json", "bundle.manifest.sig"):
        path = root / name
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8").strip()
        if raw.startswith("{"):
            return json.loads(raw)
        return {"algorithm": ALGO_COSIGN, "signatureFile": name}
    return None


def verify_hmac(data: bytes, signature_b64: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), data, hashlib.sha256).digest()
    try:
        actual = base64.b64decode(signature_b64)
    except Exception:
        return False
    return hmac.compare_digest(expected, actual)


def sign_hmac(data: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), data, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def verify_cosign_blob(
    manifest_path: Path,
    *,
    sig_path: Path,
    pubkey_path: Path,
) -> dict[str, Any]:
    cosign = shutil.which("cosign")
    if cosign is None:
        return {"verified": False, "algorithm": ALGO_COSIGN, "reason": "cosign not in PATH"}
    cmd = [
        cosign,
        "verify-blob",
        "--key",
        str(pubkey_path),
        "--signature",
        str(sig_path),
        str(manifest_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    ok = result.returncode == 0
    reason = (result.stderr or result.stdout or "").strip() or None
    return {"verified": ok, "algorithm": ALGO_COSIGN, "reason": reason}


def verify_manifest_signature(
    root: Path,
    manifest_bytes: bytes,
    *,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Verify the detached signature for ``bundle.manifest.json``."""
    env = env or dict(os.environ)
    doc = _read_sig_doc(root)
    if doc is None:
        return {"verified": False, "configured": False, "reason": "signature file missing"}

    algo = doc.get("algorithm", ALGO_COSIGN)
    if algo == ALGO_HMAC:
        secret = env.get("VERGE_BUNDLE_HMAC_SECRET")
        if not secret:
            return {
                "verified": False,
                "configured": True,
                "algorithm": algo,
                "reason": "VERGE_BUNDLE_HMAC_SECRET not configured",
            }
        sig = str(doc.get("signature", ""))
        ok = verify_hmac(manifest_bytes, sig, secret)
        return {
            "verified": ok,
            "configured": True,
            "algorithm": algo,
            "reason": None if ok else "HMAC signature mismatch",
        }

    manifest_path = root / "bundle.manifest.json"
    sig_file = doc.get("signatureFile", "bundle.manifest.cosign.sig")
    pubkey = doc.get("publicKeyFile") or env.get("VERGE_BUNDLE_PUBLIC_KEY", "cosign.pub")
    sig_path = root / sig_file if not Path(str(sig_file)).is_absolute() else Path(str(sig_file))
    pubkey_path = root / pubkey if not Path(str(pubkey)).is_absolute() else Path(str(pubkey))
    if not sig_path.exists():
        return {
            "verified": False,
            "configured": True,
            "algorithm": ALGO_COSIGN,
            "reason": f"signature file not found: {sig_path.name}",
        }
    if not pubkey_path.exists():
        return {
            "verified": False,
            "configured": True,
            "algorithm": ALGO_COSIGN,
            "reason": f"public key not found: {pubkey_path.name}",
        }
    return verify_cosign_blob(manifest_path, sig_path=sig_path, pubkey_path=pubkey_path)
