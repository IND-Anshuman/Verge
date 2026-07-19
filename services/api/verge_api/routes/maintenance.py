"""Maintenance / RCA API — work orders + asset digest (Phase 3A)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from verge_maintenance import default_store
from verge_maintenance.rca import build_rca_digest, similar_failures

router = APIRouter(tags=["maintenance"])


def _store(request: Request):
    return getattr(request.app.state, "work_orders", None) or default_store()


@router.get("/maintenance/work-orders")
def list_work_orders(
    request: Request,
    zoneId: str | None = None,
    equipmentId: str | None = None,
    limit: int = 50,
) -> dict:
    store = _store(request)
    orders = [
        o.to_dict()
        for o in store.list(zone_id=zoneId, equipment_id=equipmentId, limit=limit)
    ]
    return {"orders": orders, "count": len(orders), "knownOrderIds": sorted(store.known_ids())}


@router.get("/maintenance/similar")
def list_similar(
    request: Request,
    zoneId: str | None = None,
    equipmentId: str | None = None,
    failureCode: str | None = None,
) -> dict:
    store = _store(request)
    matches = similar_failures(
        store,
        zone_id=zoneId,
        equipment_id=equipmentId,
        failure_code=failureCode,
    )
    return {"matches": matches, "count": len(matches)}


@router.get("/maintenance/rca")
def rca_for_zone(
    request: Request,
    zoneId: str = "B-04",
    title: str = "hot work gas risk",
) -> dict:
    """60s demo beat: RCA digest with citations for a gold zone/asset."""
    store = _store(request)
    orders = [o.to_dict() for o in store.list(zone_id=zoneId)]
    sims = similar_failures(store, zone_id=zoneId)
    digest = build_rca_digest(
        work_orders=orders,
        sensor_window={"series": [{"sensorId": "LEL-04", "points": []}], "degraded": False},
        manuals={
            "citations": [
                {
                    "documentId": "DOC-HOT-WORK-SOP",
                    "excerpt": "Purge and gas-test before hot work; verify seal integrity.",
                }
            ]
        },
        similar=sims,
        finding_title=title,
    )
    return {
        "zoneId": zoneId,
        "orders": orders,
        "similar": sims,
        "rca": digest,
        "demoBeat": "rca",
    }
