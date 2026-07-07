"""Regulatory clause library for gap detection (spec §5 — compliance).

A clause is a single regulatory requirement (OISD / Factory Act / DGMS) mapped
to the **capability** a plant must demonstrate to satisfy it. Gap detection
(:mod:`verge_compliance.gaps`) then asks, per clause: does this plant's
commissioned configuration + adopted rules demonstrate the capability?

Capabilities split in two:

* **platform** — provided by the Verge core for every install (hash-chained
  audit, evidence packs, sensor-health plane, feedback loop, multi-channel
  advisory alerting). These are satisfied by having Verge, not by plant config.
* **config** — must be demonstrated by the plant's own sensors and adopted
  rules (gas detection, hot-work control, SIMOPS review, …). A config
  capability the plant has not configured is a real, honest **gap**.

The clause library is data (``clauses/oisd.json``), not code, so the regulatory
subset grows without a release. Clauses cite the OISD stub ids used by the
memory corpus so a finding's lineage stays consistent end to end (P3).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CLAUSES_DIR = Path(__file__).parent / "clauses"

# Capabilities the Verge core provides for every install (spec principles /
# §4.x). Satisfied by having Verge, independent of plant configuration.
PLATFORM_CAPABILITIES: frozenset[str] = frozenset(
    {
        "audit",  # P6 hash-chained audit
        "evidence",  # §4.4 evidence packs
        "sensor-health",  # §4.7 sensor-health plane
        "feedback",  # §4.6 alert-fatigue / FindingFeedback
        "multi-channel-alert",  # §4.4 orchestrator advisory alerting
        "evacuation-advisory",  # §4.4 advisory evacuation guidance
    }
)


@dataclass(frozen=True)
class Clause:
    id: str
    oisd_ref: str
    standard: str
    title: str
    requirement: str
    capability: str

    @property
    def is_platform(self) -> bool:
        return self.capability in PLATFORM_CAPABILITIES

    @staticmethod
    def from_dict(d: dict) -> Clause:
        return Clause(
            id=d["id"],
            oisd_ref=d.get("oisdRef", ""),
            standard=d.get("standard", ""),
            title=d["title"],
            requirement=d["requirement"],
            capability=d["capability"],
        )


def load_clauses(path: str | Path | None = None) -> list[Clause]:
    """Load the regulatory clause library (defaults to the bundled OISD subset).

    Enforces id-uniqueness: a duplicate id would inflate the coverage ratio (a
    legal claim) and silently drop a clause from the change diff, so it is a hard
    error, not a warning."""
    p = Path(path) if path else CLAUSES_DIR / "oisd.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(doc, list):
        msg = f"clause library must be a JSON list, got {type(doc).__name__}: {p}"
        raise ValueError(msg)
    clauses = [Clause.from_dict(d) for d in doc]
    ids = [c.id for c in clauses]
    dupes = sorted({cid for cid in ids if ids.count(cid) > 1})
    if dupes:
        msg = f"duplicate clause id(s) in {p}: {', '.join(dupes)}"
        raise ValueError(msg)
    return clauses
