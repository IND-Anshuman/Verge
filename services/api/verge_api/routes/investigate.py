"""Finding investigation agent route (spec — agentic advisory plane).

Binds the read-only tool registry over live app state and runs the
investigator from ``verge_agents``. Advisory only: the agent can look at
telemetry, permits, the plant graph, memory, and the clause library; it
cannot transition findings, dispatch alerts, or declare emergencies — those
stay operator-gated (P8). Every response carries the full tool-call evidence
trail, and each run is hash-chained into the audit.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from verge_agents import Tool, ToolRegistry, investigate
from verge_compliance.clauses import load_clauses

router = APIRouter(tags=["investigate"])

_STR = {"type": "string"}


def _build_tools(app, finding) -> ToolRegistry:
    store = app.state.store
    plant = app.state.plant
    readings = app.state.readings
    occupancy = app.state.occupancy
    permits = app.state.permits
    thresholds = getattr(app.state, "sensor_thresholds", {})

    def get_finding(finding_id: str = "") -> dict:
        f = store.get_finding(finding_id or finding.finding_id)
        if f is None:
            return {"error": "finding not found"}
        return f.model_dump(by_alias=True, mode="json")

    def get_zone_context(zone_id: str = "") -> dict:
        zid = zone_id or finding.zone_id
        zone = plant.zones.get(zid)
        return {
            "zoneId": zid,
            "name": zone.name if zone else "(unknown zone)",
            "adjacentZones": sorted(plant.adjacency().get(zid, set())),
            "sensors": [
                {"sensorId": s.sensor_id, "kind": s.kind, "unit": s.unit,
                 "threshold": s.threshold}
                for s in plant.sensors_in_zone(zid)
            ],
            "equipment": [
                {"equipmentId": e.equipment_id, "name": e.name, "kind": e.kind}
                for e in plant.equipment.values() if e.zone_id == zid
            ],
            "workersPresent": len(occupancy.zone_roster().get(zid, [])),
        }

    def get_recent_telemetry(finding_id: str = "") -> dict:
        f = store.get_finding(finding_id or finding.finding_id) or finding
        data = readings.series_for_finding(f, thresholds=thresholds)
        # Trim points so the model sees the shape, not a token flood.
        for series in data.get("series", []):
            pts = series.get("points", [])
            if len(pts) > 24:
                series["points"] = pts[-24:]
                series["trimmedTo"] = 24
        return data

    def get_active_permits(zone_id: str = "") -> list[dict]:
        zid = zone_id or finding.zone_id
        nearby = {zid} | set(plant.adjacency().get(zid, set()))
        return [
            {
                "permitId": p.permit_id, "kind": p.kind, "zoneId": p.zone_id,
                "equipmentId": p.equipment_id,
                "validTo": p.valid_to.isoformat(),
                "inFindingZone": p.zone_id == zid,
            }
            for p in permits.list_active()
            if p.zone_id in nearby
        ]

    def get_equipment_graph(zone_id: str = "") -> dict:
        """Equipment↔permit↔finding relations around a zone (knowledge graph)."""
        zid = zone_id or finding.zone_id
        nearby = {zid} | set(plant.adjacency().get(zid, set()))
        active = [p for p in permits.list_active() if p.zone_id in nearby]
        nodes = []
        for e in plant.equipment.values():
            if e.zone_id not in nearby:
                continue
            touching = [p.permit_id for p in active if p.equipment_id == e.equipment_id]
            nodes.append({
                "equipmentId": e.equipment_id, "name": e.name, "kind": e.kind,
                "zoneId": e.zone_id, "activePermits": touching,
                "riskNote": "permit-covered work on this equipment" if touching else None,
            })
        return {"zoneId": zid, "nearbyZones": sorted(nearby), "equipment": nodes}

    def search_incident_memory(query: str = "") -> dict:
        try:
            from verge_memory import query_memory
            return query_memory(
                query or f"incidents similar to: {finding.title}",
                finding=finding,
                provider=app.state.llm,
                env=dict(os.environ),
            )
        except Exception as exc:
            return {"answer": "", "citations": [], "degraded": True,
                    "reason": f"memory unavailable: {type(exc).__name__}"}

    def get_compliance_clauses(zone_id: str = "") -> list[dict]:
        title = finding.title.lower()
        lineage = " ".join(finding.lineage).lower()
        haystack = f"{title} {lineage}"
        scored = []
        for c in load_clauses():
            words = [w for w in c.capability.replace("-", " ").split() if len(w) > 3]
            if any(w in haystack for w in words):
                scored.append({"clauseId": c.id, "standard": c.standard,
                               "title": c.title, "requirement": c.requirement})
        return scored[:8]

    return ToolRegistry([
        Tool("get_finding", "Full details of a risk finding by id.",
             get_finding, {"type": "object", "properties": {"finding_id": _STR}}),
        Tool("get_zone_context",
             "Zone name, adjacency, sensors, equipment, and worker presence.",
             get_zone_context, {"type": "object", "properties": {"zone_id": _STR}}),
        Tool("get_recent_telemetry",
             "Recent time-series for the sensors behind a finding, with thresholds.",
             get_recent_telemetry, {"type": "object", "properties": {"finding_id": _STR}}),
        Tool("get_active_permits",
             "Active work permits in a zone and its adjacent zones.",
             get_active_permits, {"type": "object", "properties": {"zone_id": _STR}}),
        Tool("get_equipment_graph",
             "Equipment-permit-risk relationships around a zone (knowledge graph).",
             get_equipment_graph, {"type": "object", "properties": {"zone_id": _STR}}),
        Tool("search_incident_memory",
             "Search organizational memory: similar incidents, near-misses, OISD guidance.",
             search_incident_memory,
             {"type": "object", "properties": {"query": _STR}}),
        Tool("get_compliance_clauses",
             "Regulatory clauses (OISD/Factory Act) relevant to this finding.",
             get_compliance_clauses, {"type": "object", "properties": {"zone_id": _STR}}),
    ])


@router.post("/findings/{finding_id}/investigate")
def investigate_finding(finding_id: str, request: Request) -> dict:
    app = request.app
    store = app.state.store
    finding = store.get_finding(finding_id)
    if finding is None:
        raise HTTPException(404, "finding not found")

    tools = _build_tools(app, finding)
    model = os.environ.get("VERGE_LLM_AGENT_MODEL") or None
    result = investigate(
        app.state.llm,
        finding_id=finding.finding_id,
        zone_id=finding.zone_id,
        title=finding.title,
        tools=tools,
        model=model,
    )
    store.audit_append(
        actor="investigator-agent",
        kind="investigation-run",
        payload={
            "findingId": finding_id,
            "degraded": result["degraded"],
            "toolCalls": [s["tool"] for s in result["evidence"]],
            "model": result["model"],
        },
        timestamp=datetime.now(UTC),
    )
    return result
