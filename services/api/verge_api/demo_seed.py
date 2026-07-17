"""Demo / reconstruction seed policy (Phase 0 truth gate).

Default is ``demo`` so local Maya narrative and the existing test suite keep
working. Production / summit-truth boots set ``VERGE_SEED=off`` so the console
never invents findings, permits, or replay ribbon data.
"""

from __future__ import annotations

import os


def seed_mode(env: dict[str, str] | None = None) -> str:
    env = env if env is not None else dict(os.environ)
    raw = (env.get("VERGE_SEED") or "demo").strip().lower()
    if raw in {"0", "false", "no", "off", "none"}:
        return "off"
    if raw in {"1", "true", "yes", "demo", "on"}:
        return "demo"
    return "off"


def seed_enabled(env: dict[str, str] | None = None) -> bool:
    return seed_mode(env) == "demo"
