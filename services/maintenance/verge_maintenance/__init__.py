"""Maintenance / RCA plane — work orders + similar-failure helpers (Phase 3A)."""

from .store import WorkOrder, WorkOrderStore, default_store
from .rca import build_rca_digest, similar_failures

__all__ = [
    "WorkOrder",
    "WorkOrderStore",
    "build_rca_digest",
    "default_store",
    "similar_failures",
]
__version__ = "0.1.0"
