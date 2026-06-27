"""Evidence-pack assembly (spec §4.4, P3/P6).

Snapshots the source-linked evidence behind a finding into a manifest with a
content hash, so the pack is tamper-evident and the report can cite it. The
manifest hash uses the same canonical_json as the audit chain, so the same set
of items always hashes identically.
"""

from __future__ import annotations

import hashlib
from datetime import datetime

from verge_audit import canonical_json
from verge_schema.audit import EvidencePack
from verge_schema.findings import RiskFinding


def manifest_hash(items: list[str]) -> str:
    """Order-independent content hash of the evidence item keys."""
    return hashlib.sha256(canonical_json(sorted(items)).encode("utf-8")).hexdigest()


def build_evidence_pack(
    finding: RiskFinding, *, created_at: datetime, extra_items: list[str] | None = None
) -> EvidencePack:
    """Assemble the pack from the finding's lineage + any captured artifacts
    (frames, traces). Items are object-store keys; here we seed from lineage."""
    items = list(finding.lineage)
    if extra_items:
        items.extend(extra_items)
    items = sorted(set(items))
    return EvidencePack(
        pack_id=f"EP-{finding.finding_id}",
        finding_id=finding.finding_id,
        items=items,
        manifest_hash=manifest_hash(items),
        created_at=created_at,
    )
