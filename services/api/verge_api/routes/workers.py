"""Worker location plane routes (spec §5 — geospatial heatmap worker layer).

Zone-level presence from any RTLS provider (omlox hub, BLE gateway, access-
control badging, or the sim), contract-validated at the boundary like every
other canonical event. Serves the map's worker layer, per-finding exposure
headcounts, and — during an emergency — the muster roll-call source data.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from verge_contracts.envelope import ContractViolation, validate_and_enrich

from .. import metrics_counters
from ..trace import current_trace_id, record_trace

router = APIRouter(tags=["workers"])


class WorkerLocationBody(BaseModel):
    type: str = "worker-location"
    ts: str
    workerId: str
    zoneId: str
    name: str | None = None
    role: str | None = None
    source: str | None = None
    eventId: str | None = None
    siteId: str | None = None


@router.post("/workers/ingest")
def ingest_worker_location(body: WorkerLocationBody, request: Request) -> dict:
    """Ingest one canonical worker-location fix."""
    raw = body.model_dump(exclude_none=True)
    try:
        payload = validate_and_enrich(raw, trace_id=current_trace_id())
    except ContractViolation as exc:
        metrics_counters.contract_rejections += 1
        raise HTTPException(422, {"errors": exc.result.errors}) from exc

    request.app.state.occupancy.ingest(payload)
    record_trace(
        request.app,
        payload.get("traceId"),
        "api.workers.ingest",
        workerId=payload["workerId"],
        eventId=payload.get("eventId"),
    )
    return {"ok": True, "workerId": payload["workerId"], "zoneId": payload["zoneId"]}


@router.get("/workers")
def list_workers(request: Request) -> dict:
    """Current positions and zone rosters, staleness flagged (never hidden)."""
    occupancy = request.app.state.occupancy
    positions = occupancy.positions()
    latest = occupancy.latest_ts()
    return {
        "workers": positions,
        "byZone": occupancy.zone_roster(),
        "total": len(positions),
        "stale": sum(1 for w in positions if w["stale"]),
        "latestFixTs": latest.isoformat() if latest else None,
    }


@router.get("/findings/{finding_id}/exposure")
def finding_exposure(finding_id: str, request: Request) -> dict:
    """Headcount at risk for a finding: its zone plus adjacent zones."""
    store = request.app.state.store
    finding = store.get_finding(finding_id)
    if finding is None:
        raise HTTPException(404, "finding not found")
    plant = request.app.state.plant
    zone = finding.zone_id
    adjacent = set(plant.adjacency().get(zone, set()))
    exposure = request.app.state.occupancy.exposure({zone}, adjacent)
    return {"findingId": finding_id, **exposure}
