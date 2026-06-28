"""The store contract.

The API depends only on this Protocol, never on a concrete backend. Two
implementations satisfy it — InMemoryStore (dev/tests/demo) and SqlStore
(durable, Postgres or SQLite) — and a shared contract test proves they are
interchangeable. Audit access is exposed as methods (not a raw chain object) so
a durable backend can persist and re-verify the chain across restarts (P6).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from verge_schema.enums import DataQuality, FeedbackVerdict
from verge_schema.enums import FindingState as S
from verge_schema.findings import FindingFeedback, RiskFinding


@runtime_checkable
class StoreProtocol(Protocol):
    # ── findings ──────────────────────────────────────────────────────────
    def add_finding(self, f: RiskFinding) -> RiskFinding: ...
    def get_finding(self, finding_id: str) -> RiskFinding | None: ...
    def list_findings(
        self, state: str | None = None, shadow: bool | None = False
    ) -> list[RiskFinding]: ...
    def transition(
        self, finding_id: str, to: S, actor: str,
        reason_code: str | None = None, reason_text: str | None = None,
    ) -> RiskFinding: ...

    # ── alert fatigue (spec §4.6) ─────────────────────────────────────────
    def add_feedback(
        self, finding_id: str, actor: str, verdict: FeedbackVerdict,
        reason_code: str | None = None,
    ) -> FindingFeedback: ...
    def fpr(self) -> float | None: ...

    # ── shadow mode (spec §14.5) ──────────────────────────────────────────
    def shadow_summary(self) -> dict: ...

    # ── sensor health ribbon (spec §4.7) ──────────────────────────────────
    def get_sensor_health(self) -> dict[DataQuality, int]: ...
    def set_sensor_health(self, counts: dict[DataQuality, int]) -> None: ...

    # ── audit (P6) ────────────────────────────────────────────────────────
    def audit_append(
        self, actor: str, kind: str, payload: dict, timestamp: datetime
    ) -> dict: ...
    def audit_entries(self, limit: int = 50) -> list[dict]: ...
    def audit_head(self) -> str: ...
    def audit_len(self) -> int: ...
    def audit_verify(self) -> bool: ...
