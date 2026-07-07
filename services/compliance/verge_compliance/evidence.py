"""Regulator-ready compliance evidence packs (spec §5 compliance, P6).

A compliance pack is a tamper-evident snapshot of a gap assessment: the clause
verdicts, the supporting finding ids, and the audit-chain head at the time of
assessment, all bound by a content hash computed with the **same**
``canonical_json`` as the audit chain. Two assessments over identical inputs
hash identically — the pack is reproducible, which is what makes it defensible
in front of a regulator.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime

from verge_audit import canonical_json
from verge_audit.chain import GENESIS_HASH

from .gaps import ComplianceReport


def manifest_hash(body: dict) -> str:
    """Deterministic content hash of a pack body (order-independent by key)."""
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


@dataclass
class CompliancePack:
    pack_id: str
    plant: str
    created_at: datetime
    coverage_ratio: float
    clauses: list[dict]  # [{id, status}]
    gap_clause_ids: list[str]
    finding_ids: list[str]
    audit_head: str
    hash: str = ""

    def to_dict(self) -> dict:
        return {
            "packId": self.pack_id,
            "plant": self.plant,
            "createdAt": self.created_at.isoformat(),
            "coverageRatio": round(self.coverage_ratio, 4),
            "clauses": self.clauses,
            "gapClauseIds": self.gap_clause_ids,
            "findingIds": self.finding_ids,
            "auditHead": self.audit_head,
            "manifestHash": self.hash,
        }


def build_compliance_pack(
    report: ComplianceReport,
    *,
    created_at: datetime,
    finding_ids: list[str] | None = None,
    audit_head: str = GENESIS_HASH,
) -> CompliancePack:
    finding_ids = sorted(set(finding_ids or []))
    clauses = [{"id": r.clause.id, "status": r.status} for r in report.results]
    gap_ids = sorted(r.clause.id for r in report.gaps)
    # The hash covers the assessment content + supporting evidence + audit head,
    # but NOT the wall-clock time, so identical assessments are comparable.
    body = {
        "plant": report.plant,
        "coverageRatio": round(report.coverage_ratio, 4),
        "clauses": sorted(clauses, key=lambda c: c["id"]),
        "findingIds": finding_ids,
        "auditHead": audit_head,
    }
    pack = CompliancePack(
        pack_id=f"CP-{report.plant}",
        plant=report.plant,
        created_at=created_at,
        coverage_ratio=report.coverage_ratio,
        clauses=clauses,
        gap_clause_ids=gap_ids,
        finding_ids=finding_ids,
        audit_head=audit_head,
    )
    pack.hash = manifest_hash(body)
    return pack
