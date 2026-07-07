"""Data contract registry API (audit §6)."""

from __future__ import annotations

from fastapi import APIRouter
from verge_contracts import ContractRegistry

router = APIRouter(tags=["contracts"])
_registry = ContractRegistry()


@router.get("/contracts/summary")
def contracts_summary() -> dict:
    """Versioned event contracts available on this deployment."""
    return _registry.summary()
