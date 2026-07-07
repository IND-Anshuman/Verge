"""Regulatory-change monitoring (spec §14 Phase 3 — compliance).

Standards move: OISD revises a clause, a new requirement lands, an old one is
withdrawn. A plant that certified against last year's subset needs to know
*exactly what changed* — not re-read the whole standard. This diffs the current
clause library against a prior certified snapshot and reports added, removed, and
modified clauses (field-level), plus a content **fingerprint** of each library so
a drift from the certified baseline is detectable at a glance.

The fingerprint uses the audit chain's ``canonical_json``, so the same library
always fingerprints identically across machines.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from verge_audit import canonical_json

from .clauses import CLAUSES_DIR, Clause, load_clauses

# The library as certified at the last regulatory review (demo baseline).
PRIOR_SNAPSHOT = CLAUSES_DIR / "oisd-2023.json"

_TRACKED_FIELDS = ("title", "requirement", "standard", "capability", "oisd_ref")


def library_fingerprint(clauses: list[Clause]) -> str:
    """Order-independent content hash of a clause library."""
    material = [
        {
            "id": c.id, "title": c.title, "requirement": c.requirement,
            "standard": c.standard, "capability": c.capability, "oisdRef": c.oisd_ref,
        }
        for c in sorted(clauses, key=lambda c: c.id)
    ]
    return hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()


@dataclass
class ClauseChange:
    clause_id: str
    changes: dict  # field -> {"from": ..., "to": ...}


def diff_clauses(old: list[Clause], new: list[Clause]) -> dict:
    """Diff two clause libraries: added / removed / modified (field-level)."""
    old_by_id = {c.id: c for c in old}
    new_by_id = {c.id: c for c in new}
    old_ids, new_ids = set(old_by_id), set(new_by_id)

    added = sorted(new_ids - old_ids)
    removed = sorted(old_ids - new_ids)
    modified: list[ClauseChange] = []
    for cid in sorted(old_ids & new_ids):
        o, n = old_by_id[cid], new_by_id[cid]
        field_changes = {
            f: {"from": getattr(o, f), "to": getattr(n, f)}
            for f in _TRACKED_FIELDS
            if getattr(o, f) != getattr(n, f)
        }
        if field_changes:
            modified.append(ClauseChange(cid, field_changes))

    # `changed` is derived from the visible diff, never from the fingerprint
    # alone — an alarm always comes with an explanation of what changed.
    return {
        "changed": bool(added or removed or modified),
        "fingerprintFrom": library_fingerprint(old),
        "fingerprintTo": library_fingerprint(new),
        "added": added,
        "removed": removed,
        "modified": [{"clauseId": c.clause_id, "changes": c.changes} for c in modified],
    }


def load_prior(path: str | Path | None = None) -> list[Clause]:
    return load_clauses(path or PRIOR_SNAPSHOT)


def changes_since_prior(current: list[Clause] | None = None) -> dict:
    """Diff the current library against the certified prior snapshot."""
    current = current if current is not None else load_clauses()
    return diff_clauses(load_prior(), current)
