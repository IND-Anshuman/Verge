"""Emergency mode routes (spec §4.4) — declare, muster roll-call, stand down.

Every state change is operator-attributed and hash-chained into the audit.
Declaration is deliberately explicit: the operator is the safety interlock
(P8); Verge choreographs what follows, it never self-triggers.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(tags=["emergency"])


class DeclareBody(BaseModel):
    approvedBy: str | None = None


class CheckInBody(BaseModel):
    workerId: str
    musterId: str
    recordedBy: str | None = None


class StandDownBody(BaseModel):
    approvedBy: str | None = None


@router.post("/findings/{finding_id}/emergency/declare")
def declare_emergency(finding_id: str, body: DeclareBody, request: Request) -> dict:
    app = request.app
    store = app.state.store
    finding = store.get_finding(finding_id)
    if finding is None:
        raise HTTPException(404, "finding not found")
    now = datetime.now(UTC)
    try:
        status = app.state.emergency.declare(
            finding,
            approved_by=body.approvedBy or "",
            plant=app.state.plant,
            occupancy=app.state.occupancy,
            readings=app.state.readings,
            thresholds=getattr(app.state, "sensor_thresholds", {}),
            now=now,
        )
    except PermissionError as exc:
        # A refused attempt is itself evidence (P8) — audit it, attributed to
        # a human ("anonymous"), never to the platform.
        store.audit_append(
            actor="anonymous",
            kind="emergency-declare-refused",
            payload={"findingId": finding_id, "reason": str(exc)},
            timestamp=now,
        )
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

    store.audit_append(
        actor=status["declaredBy"],
        kind="emergency-declared",
        payload={
            "emergencyId": status["emergencyId"],
            "findingId": finding_id,
            "affectedZones": status["affectedZones"],
            "evidenceFreezeHash": status["evidenceFreeze"]["hash"],
            "headcountExpected": status["muster"]["expected"],
            "trappedZones": status["evacuation"]["trappedZones"],
        },
        timestamp=now,
    )
    return status


@router.get("/emergency/status")
def emergency_status(request: Request) -> dict:
    return request.app.state.emergency.status()


@router.post("/emergency/muster/check-in")
def muster_check_in(body: CheckInBody, request: Request) -> dict:
    app = request.app
    now = datetime.now(UTC)
    try:
        status = app.state.emergency.check_in(
            body.workerId, body.musterId,
            recorded_by=body.recordedBy or "", now=now,
        )
    except LookupError as exc:
        raise HTTPException(409, str(exc)) from exc
    app.state.store.audit_append(
        actor=(body.recordedBy or "").strip() or "anonymous",
        kind="muster-check-in",
        payload={
            "emergencyId": status["emergencyId"],
            "workerId": body.workerId,
            "musterId": body.musterId,
            "accounted": len(status["muster"]["accounted"]),
            "missing": len(status["muster"]["missing"]),
        },
        timestamp=now,
    )
    return status


@router.post("/emergency/stand-down")
def emergency_stand_down(body: StandDownBody, request: Request) -> dict:
    app = request.app
    now = datetime.now(UTC)
    try:
        final = app.state.emergency.stand_down(approved_by=body.approvedBy or "", now=now)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(409, str(exc)) from exc
    app.state.store.audit_append(
        actor=final["stoodDownBy"],
        kind="emergency-stand-down",
        payload={
            "emergencyId": final["emergencyId"],
            "allAccounted": final["muster"]["allAccounted"],
            "missingAtStandDown": len(final["muster"]["missing"]),
        },
        timestamp=now,
    )
    return final


@router.get("/emergency/evidence")
def emergency_evidence(request: Request) -> dict:
    """The frozen evidence manifest for the active emergency (hash-bound)."""
    frozen = request.app.state.emergency.frozen_evidence()
    if frozen is None:
        raise HTTPException(404, "no active emergency")
    return frozen
