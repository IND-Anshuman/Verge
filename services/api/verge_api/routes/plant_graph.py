"""Plant graph — live projection + optional Neo4j sync (spec §5)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from verge_risk import STARTER_RULES, load_rules
from verge_twin import load_plant
from verge_twin.neo4j_sync import sync_plant
from verge_twin.plant import DEMO_PLANT

from ..graph_view import build_plant_graph

router = APIRouter(tags=["plant"])


@router.get("/plant/graph")
def plant_graph(request: Request) -> dict:
    """Equipment–permit–risk graph from live twin + permits + findings.

    Never returns fabricated demo nodes. Empty plant → empty arrays.
    """
    app = request.app
    plant = getattr(app.state, "plant", None) or load_plant(DEMO_PLANT)
    permits = []
    registry = getattr(app.state, "permits", None)
    if registry is not None:
        permits = list(registry.list_active())
    findings = list(app.state.store.list_findings(shadow=False))
    return build_plant_graph(plant, permits, findings)


@router.post("/plant/graph-sync")
def plant_graph_sync(request: Request) -> dict:
    """Push the commissioned plant into Neo4j when configured."""
    plant = getattr(request.app.state, "plant", None) or load_plant(DEMO_PLANT)
    _ = load_rules(STARTER_RULES)  # ensures rules library is loadable
    return sync_plant(plant)
