"""P1 / Phase 2.5: safety core must never import verge_llm."""

from __future__ import annotations

import ast
from pathlib import Path

RISK_ROOT = Path(__file__).resolve().parents[1] / "verge_risk"


def test_verge_risk_does_not_import_verge_llm():
    offenders: list[str] = []
    for path in RISK_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "verge_llm" or alias.name.startswith("verge_llm."):
                        offenders.append(f"{path.name}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod == "verge_llm" or mod.startswith("verge_llm."):
                    offenders.append(f"{path.name}: from {mod}")
    assert offenders == [], f"LLM imports in safety core: {offenders}"
