"""Corrective-action workflow (CAPA) — ISO 45001 clause 10.2 shape.

Detection without a workflow is a report nobody owns. Every open compliance
gap (and optionally a finding) can spawn a corrective action that carries an
owner, a hierarchy-of-controls tier, and a state machine with the one step
audits actually check for: **effectiveness verification**. A closed-ineffective
action reopens — clause 10.2 is explicit that an unverified fix is incomplete.

States:  open → in-progress → pending-verification → closed-effective
                       ↑                    └→ reopened ──┘
Deterministic and LLM-free; the audit chain records every transition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from .gaps import ComplianceReport

STATES = ("open", "in-progress", "pending-verification", "closed-effective", "reopened")

LEGAL_TRANSITIONS: dict[str, set[str]] = {
    "open": {"in-progress"},
    "in-progress": {"pending-verification"},
    "pending-verification": {"closed-effective", "reopened"},
    "reopened": {"in-progress"},
    "closed-effective": set(),
}

# Hierarchy of controls, most effective first (clause 8.1.2). The suggestion is
# keyword-derived from the capability — a starting point for the engineer, not
# a verdict.
_CONTROL_SUGGESTIONS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("isolation", "lockout"), "engineering"),
    (("monitoring", "detection", "drift"), "engineering"),
    (("permit", "control", "review", "handover"), "administrative"),
    (("tank", "startup"), "engineering"),
)


def suggest_control_tier(capability: str) -> str:
    cap = capability.lower()
    for keywords, tier in _CONTROL_SUGGESTIONS:
        if any(k in cap for k in keywords):
            return tier
    return "administrative"


class IllegalActionTransition(ValueError):
    pass


@dataclass
class CorrectiveAction:
    action_id: str
    source: str  # "gap" | "finding"
    title: str
    requirement: str
    control_tier: str
    state: str = "open"
    clause_id: str | None = None
    finding_id: str | None = None
    standard: str | None = None
    owner: str | None = None
    due: str | None = None  # ISO date, set by the owner
    created_at: str = ""
    history: list[dict] = field(default_factory=list)

    def transition(
        self, to: str, *, actor: str, note: str = "", now: datetime | None = None
    ) -> None:
        if to not in STATES:
            raise IllegalActionTransition(f"unknown state {to!r}")
        if to not in LEGAL_TRANSITIONS[self.state]:
            raise IllegalActionTransition(
                f"{self.state} -> {to} is not a legal CAPA transition "
                f"(legal: {sorted(LEGAL_TRANSITIONS[self.state])})"
            )
        who = (actor or "").strip()
        if not who:
            raise PermissionError("transition requires a named actor")
        if to == "closed-effective" and not (note or "").strip():
            raise PermissionError(
                "closing as effective requires a verification note (clause 10.2: "
                "an unverified corrective action is incomplete)"
            )
        now = now or datetime.now(UTC)
        self.history.append(
            {"from": self.state, "to": to, "actor": who, "note": note, "ts": now.isoformat()}
        )
        self.state = to

    def to_dict(self) -> dict:
        return {
            "actionId": self.action_id,
            "source": self.source,
            "title": self.title,
            "requirement": self.requirement,
            "controlTier": self.control_tier,
            "state": self.state,
            "clauseId": self.clause_id,
            "findingId": self.finding_id,
            "standard": self.standard,
            "owner": self.owner,
            "due": self.due,
            "createdAt": self.created_at,
            "history": self.history,
        }


class ActionsLog:
    """In-memory CAPA registry. The hash-chained audit is the durable record of
    every generate/transition; this registry is the live working set."""

    def __init__(self) -> None:
        self._actions: dict[str, CorrectiveAction] = {}
        self._seq = 0

    def _next_id(self, now: datetime) -> str:
        self._seq += 1
        return f"CA-{now.strftime('%Y%m%d')}-{self._seq:03d}"

    def list(self) -> list[CorrectiveAction]:
        return sorted(self._actions.values(), key=lambda a: a.action_id)

    def get(self, action_id: str) -> CorrectiveAction | None:
        return self._actions.get(action_id)

    def _open_for_clause(self, clause_id: str) -> bool:
        return any(
            a.clause_id == clause_id and a.state != "closed-effective"
            for a in self._actions.values()
        )

    def generate_from_gaps(
        self, report: ComplianceReport, *, now: datetime | None = None
    ) -> list[CorrectiveAction]:
        """One action per open gap that doesn't already have a live action —
        idempotent: re-running after nothing changed creates nothing."""
        now = now or datetime.now(UTC)
        created: list[CorrectiveAction] = []
        for result in report.gaps:
            clause = result.clause
            if self._open_for_clause(clause.id):
                continue
            action = CorrectiveAction(
                action_id=self._next_id(now),
                source="gap",
                title=f"Close compliance gap: {clause.title}",
                requirement=clause.requirement,
                control_tier=suggest_control_tier(clause.capability),
                clause_id=clause.id,
                standard=clause.standard,
                created_at=now.isoformat(),
            )
            self._actions[action.action_id] = action
            created.append(action)
        return created

    def create_for_finding(
        self, finding_id: str, title: str, requirement: str,
        *, control_tier: str = "administrative", now: datetime | None = None,
    ) -> CorrectiveAction:
        now = now or datetime.now(UTC)
        action = CorrectiveAction(
            action_id=self._next_id(now),
            source="finding",
            title=title,
            requirement=requirement,
            control_tier=control_tier,
            finding_id=finding_id,
            created_at=now.isoformat(),
        )
        self._actions[action.action_id] = action
        return action
