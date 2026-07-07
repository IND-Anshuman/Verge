#!/usr/bin/env python3
"""Sign a dev release bundle manifest with HMAC-SHA256 (pilot / CI only).

Production air-gap installs should use cosign:
  cosign sign-blob --key cosign.key bundle.manifest.json
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from verge_supplychain.signatures import ALGO_HMAC, sign_hmac


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Sign a Verge bundle manifest (dev HMAC)")
    ap.add_argument("root", type=Path, help="bundle directory containing bundle.manifest.json")
    ap.add_argument(
        "--secret",
        default=os.environ.get("VERGE_BUNDLE_HMAC_SECRET", "verge-dev-bundle-secret"),
    )
    args = ap.parse_args(argv)

    manifest_path = args.root / "bundle.manifest.json"
    data = manifest_path.read_bytes()
    sig = sign_hmac(data, args.secret)
    out = args.root / "bundle.manifest.sig.json"
    out.write_text(
        json.dumps({"algorithm": ALGO_HMAC, "signature": sig}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"signed {manifest_path.name} -> {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
