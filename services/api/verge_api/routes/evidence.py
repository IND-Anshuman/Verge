"""Evidence retrieval routes."""

from __future__ import annotations

from fastapi import APIRouter

from ..evidence_store import get_evidence_manifest

router = APIRouter(tags=["evidence"])


@router.get("/evidence/{pack_id}")
def evidence_manifest(pack_id: str, findingId: str | None = None) -> dict:
    """Fetch an evidence manifest from MinIO when configured."""
    return get_evidence_manifest(pack_id, finding_id=findingId)
