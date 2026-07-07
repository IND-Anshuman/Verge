"""CLI bundle verification."""

from __future__ import annotations

import json
from pathlib import Path

from verge_cli.cli import main

ROOT = Path(__file__).resolve().parents[2] / "deploy" / "bundles" / "demo-0.3.0"


def test_cli_bundle_verify_demo() -> None:
    code = main([
        "bundle", "verify", "--root", str(ROOT),
        "--hmac-secret", "verge-dev-bundle-secret",
    ])
    assert code == 0


def test_cli_bundle_inspect_demo(capsys) -> None:
    code = main(["bundle", "inspect", "--root", str(ROOT)])
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body["version"] == "0.3.0"
