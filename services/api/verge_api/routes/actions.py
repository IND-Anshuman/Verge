"""Corrective-action (CAPA) routes — ISO 45001 10.2 workflow over gaps.

Generation is idempotent (a live action per clause, never duplicates), every
transition demands a named actor, closing demands a verification note, and
everything lands in the hash-chained audit.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from verge_compliance import IllegalActionTransition, assess
from verge_risk import STARTER_RULES, load_rules
from verge_twin import load_plant
from verge_twin.plant import DEMO_PLANT

router = APIRouter(tags=["actions"])


class TransitionBody(BaseModel):
    to: str
    actor: str | None = None
    note: str | None = None


class AssignBody(BaseModel):
    owner: str | None = None
    due: str | None = None
    actor: str | None = None


@router.get("/compliance/actions")
def list_actions(request: Request) -> dict:
    actions = request.app.state.actions.list()
    return {
        "actions": [a.to_dict() for a in actions],
        "total": len(actions),
        "openCount": sum(1 for a in actions if a.state != "closed-effective"),
    }


@router.post("/compliance/actions/generate")
def generate_actions(request: Request) -> dict:
    plant, rules = load_plant(DEMO_PLANT), load_rules(STARTER_RULES)
    report = assess(plant, rules)
    now = datetime.now(UTC)
    created = request.app.state.actions.generate_from_gaps(report, now=now)
    if created:
        request.app.state.store.audit_append(
            actor="compliance-agent",
            kind="corrective-actions-generated",
            payload={
                "count": len(created),
                "actionIds": [a.action_id for a in created],
                "clauses": [a.clause_id for a in created],
            },
            timestamp=now,
        )
    return {
        "created": [a.to_dict() for a in created],
        "count": len(created),
        "note": None if created else "no new gaps without a live action (idempotent)",
    }


@router.post("/compliance/actions/{action_id}/transition")
def transition_action(action_id: str, body: TransitionBody, request: Request) -> dict:
    action = request.app.state.actions.get(action_id)
    if action is None:
        raise HTTPException(404, "action not found")
    now = datetime.now(UTC)
    try:
        action.transition(body.to, actor=body.actor or "", note=body.note or "", now=now)
    except IllegalActionTransition as exc:
        raise HTTPException(409, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    request.app.state.store.audit_append(
        actor=(body.actor or "").strip(),
        kind="corrective-action-transition",
        payload={
            "actionId": action_id,
            "to": body.to,
            "clauseId": action.clause_id,
            "note": body.note or "",
        },
        timestamp=now,
    )
    return action.to_dict()


@router.post("/compliance/actions/{action_id}/assign")
def assign_action(action_id: str, body: AssignBody, request: Request) -> dict:
    action = request.app.state.actions.get(action_id)
    if action is None:
        raise HTTPException(404, "action not found")
    if body.owner is not None:
        action.owner = body.owner.strip() or None
    if body.due is not None:
        action.due = body.due.strip() or None
    request.app.state.store.audit_append(
        actor=(body.actor or "").strip() or "anonymous",
        kind="corrective-action-assigned",
        payload={"actionId": action_id, "owner": action.owner, "due": action.due},
        timestamp=datetime.now(UTC),
    )
    return action.to_dict()
