"""Post-transition hooks (memory ingest, etc.)."""

from __future__ import annotations

import os

from verge_memory import ingest_closed_finding, ingest_feedback
from verge_memory.client import CogneeClient
from verge_memory.datasets import dataset_name
from verge_schema.enums import FindingState as S
from verge_schema.findings import RiskFinding

_CLOSED = {S.RESOLVED, S.CLOSED, S.SUPPRESSED_AS_DUPLICATE}
_TRUE = {"1", "true", "yes", "on"}


def _memory_enabled() -> bool:
    return os.environ.get("VERGE_COGNEE_ENABLED", "").lower() in _TRUE


def maybe_ingest_closed_finding(finding: RiskFinding, *, to: S) -> None:
    """Best-effort Cognee ingest when a finding closes; never raises."""
    if to not in _CLOSED or not _memory_enabled():
        return
    try:
        env = dict(os.environ)
        client = CogneeClient.from_env(env)
        ingest_closed_finding(client, dataset_name(env), finding)
    except Exception:
        return


def maybe_ingest_feedback(
    finding: RiskFinding,
    *,
    verdict: str,
    reason_code: str | None,
    reason_text: str | None,
) -> None:
    """Best-effort Cognee ingest of operator feedback; never raises."""
    if not _memory_enabled():
        return
    try:
        env = dict(os.environ)
        client = CogneeClient.from_env(env)
        ingest_feedback(
            client,
            dataset_name(env),
            finding,
            verdict=verdict,
            reason_code=reason_code,
            reason_text=reason_text,
        )
    except Exception:
        return
