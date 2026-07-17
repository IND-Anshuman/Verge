"""Build an equipment–permit–risk graph from live plant state (Phase 0).

Replaces hardcoded console NODES/LINKS with a deterministic projection of the
twin + open permits + active findings. Layout positions are stable hashes so
the SVG does not jump between polls.
"""

from __future__ import annotations

import hashlib
from typing import Any

from verge_schema.enums import FindingState
from verge_schema.findings import RiskFinding
from verge_twin.plant import PlantModel

ACTIVE = {
    FindingState.NEW,
    FindingState.ACKNOWLEDGED,
    FindingState.ESCALATED,
    FindingState.SNOOZED,
}


def _pos(key: str, lane: int) -> tuple[float, float]:
    """Deterministic pseudo-layout in a 360×240 canvas."""
    digest = hashlib.sha256(key.encode()).hexdigest()
    x = 40 + (int(digest[:4], 16) % 280)
    y = 36 + lane * 72 + (int(digest[4:8], 16) % 48)
    return float(x), float(y)


def build_plant_graph(
    plant: PlantModel,
    permits: list[Any],
    findings: list[RiskFinding],
) -> dict:
    nodes: list[dict] = []
    links: list[dict] = []
    seen: set[str] = set()

    # Prefer equipment that is referenced by permits/findings; fall back to a
    # bounded sample so an empty plant still shows the twin, not fiction.
    eq_ids: set[str] = set()
    for p in permits:
        eid = getattr(p, "equipment_id", None) or (p.get("equipmentId") if isinstance(p, dict) else None)
        if eid:
            eq_ids.add(str(eid))
    for f in findings:
        if f.state not in ACTIVE or f.shadow:
            continue
        for sig in f.contributing_signals or []:
            if sig.kind == "equipment" and sig.ref_id:
                eq_ids.add(sig.ref_id)
        for item in f.lineage or []:
            if item.startswith("equipment:"):
                eq_ids.add(item.split(":", 1)[1])

    equipment = [plant.equipment[i] for i in eq_ids if i in plant.equipment]
    if not equipment:
        equipment = list(plant.equipment.values())[:8]

    for eq in equipment:
        nid = f"eq:{eq.equipment_id}"
        if nid in seen:
            continue
        seen.add(nid)
        x, y = _pos(nid, 1)
        nodes.append(
            {
                "id": nid,
                "label": eq.name or eq.equipment_id,
                "type": "equipment",
                "x": x,
                "y": y,
                "details": f"{eq.kind} · zone {eq.zone_id}",
                "zoneId": eq.zone_id,
                "refId": eq.equipment_id,
            }
        )

    for p in permits:
        pid = getattr(p, "permit_id", None) or (p.get("permitId") if isinstance(p, dict) else None)
        kind = getattr(p, "kind", None) or (p.get("kind") if isinstance(p, dict) else "permit")
        zone = getattr(p, "zone_id", None) or (p.get("zoneId") if isinstance(p, dict) else "")
        eid = getattr(p, "equipment_id", None) or (p.get("equipmentId") if isinstance(p, dict) else None)
        if not pid:
            continue
        nid = f"ptw:{pid}"
        if nid in seen:
            continue
        seen.add(nid)
        x, y = _pos(nid, 0)
        nodes.append(
            {
                "id": nid,
                "label": f"{kind} {pid}",
                "type": "permit",
                "x": x,
                "y": y,
                "details": f"Active {kind} in zone {zone}",
                "zoneId": zone,
                "refId": pid,
            }
        )
        if eid and f"eq:{eid}" in seen:
            links.append({"source": nid, "target": f"eq:{eid}", "kind": "permits"})
        else:
            # Link permit to any equipment in the same zone.
            for eq in equipment:
                if eq.zone_id == zone and f"eq:{eq.equipment_id}" in seen:
                    links.append({"source": nid, "target": f"eq:{eq.equipment_id}", "kind": "permits"})
                    break

    for f in findings:
        if f.state not in ACTIVE or f.shadow:
            continue
        nid = f"risk:{f.finding_id}"
        if nid in seen:
            continue
        seen.add(nid)
        x, y = _pos(nid, 2)
        band = (
            f.lead_time_band.value
            if hasattr(f.lead_time_band, "value")
            else str(f.lead_time_band)
        )
        state = f.state.value if hasattr(f.state, "value") else str(f.state)
        nodes.append(
            {
                "id": nid,
                "label": f.title[:48] or f.finding_id,
                "type": "risk",
                "x": x,
                "y": y,
                "details": f"{band} · zone {f.zone_id} · {state}",
                "zoneId": f.zone_id,
                "refId": f.finding_id,
            }
        )
        # Link risk → permits / equipment mentioned in lineage.
        for item in f.lineage or []:
            if item.startswith("permit:"):
                target = f"ptw:{item.split(':', 1)[1]}"
                if target in seen:
                    links.append({"source": nid, "target": target, "kind": "implicates"})
            if item.startswith("equipment:"):
                target = f"eq:{item.split(':', 1)[1]}"
                if target in seen:
                    links.append({"source": nid, "target": target, "kind": "implicates"})
        for eq in equipment:
            if eq.zone_id == f.zone_id and f"eq:{eq.equipment_id}" in seen:
                links.append({"source": nid, "target": f"eq:{eq.equipment_id}", "kind": "in-zone"})
                break

    return {
        "nodes": nodes,
        "links": links,
        "plant": plant.name,
        "degraded": False,
        "source": "twin+permits+findings",
    }
