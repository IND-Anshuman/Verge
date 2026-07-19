"""RCA helpers — similar failures + distilled digest (LLM-free)."""

from __future__ import annotations

from typing import Any

from .store import WorkOrder, WorkOrderStore


def similar_failures(
    store: WorkOrderStore,
    *,
    failure_code: str | None = None,
    equipment_id: str | None = None,
    zone_id: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Rank closed WOs by shared failure code / equipment / zone. No invention."""
    scored: list[tuple[int, WorkOrder]] = []
    for wo in store.orders:
        if wo.state not in {"closed", "completed", "resolved"}:
            continue
        score = 0
        if failure_code and wo.failure_code.lower() == failure_code.lower():
            score += 3
        if equipment_id and wo.equipment_id == equipment_id:
            score += 2
        if zone_id and wo.zone_id == zone_id:
            score += 1
        if score:
            scored.append((score, wo))
    scored.sort(key=lambda x: (-x[0], x[1].order_id))
    return [wo.to_dict() | {"matchScore": sc} for sc, wo in scored[:limit]]


def build_rca_digest(
    *,
    work_orders: list[dict[str, Any]],
    sensor_window: dict[str, Any] | None,
    manuals: dict[str, Any] | None,
    similar: list[dict[str, Any]],
    finding_title: str = "",
) -> dict[str, Any]:
    """Distill RCA evidence. Schedule suggestion only when WOs exist."""
    citations: list[dict[str, str]] = []
    for wo in work_orders[:5]:
        citations.append({
            "kind": "work-order",
            "refId": str(wo.get("orderId") or ""),
            "summary": str(wo.get("title") or wo.get("orderId") or ""),
        })
    if sensor_window and not sensor_window.get("degraded"):
        series = sensor_window.get("series") or []
        if series:
            sid = series[0].get("sensorId") if isinstance(series[0], dict) else None
            citations.append({
                "kind": "sensor-window",
                "refId": str(sid or "telemetry"),
                "summary": f"{len(series)} sensor series in finding window",
            })
    if manuals and isinstance(manuals, dict):
        for c in (manuals.get("citations") or [])[:3]:
            if not isinstance(c, dict):
                continue
            citations.append({
                "kind": "manual",
                "refId": str(c.get("documentId") or c.get("chunkId") or "doc"),
                "summary": str(c.get("excerpt") or c.get("title") or "")[:160],
            })
    for sim in similar[:3]:
        citations.append({
            "kind": "similar-failure",
            "refId": str(sim.get("orderId") or ""),
            "summary": str(sim.get("title") or sim.get("failureCode") or ""),
        })
    citations = [c for c in citations if c.get("refId")]

    schedule_why = None
    if work_orders:
        open_like = [w for w in work_orders if w.get("state") in {"open", "in-progress", "degraded"}]
        if open_like:
            wo = open_like[0]
            schedule_why = (
                f"Prioritise follow-up on {wo.get('orderId')} "
                f"({wo.get('failureCode') or 'WO'}) for {wo.get('equipmentId')} — "
                f"open maintenance overlaps live finding '{finding_title or 'risk'}'."
            )
        elif similar:
            s0 = similar[0]
            schedule_why = (
                f"History: {s0.get('orderId')} closed after "
                f"{s0.get('failureCode') or 'similar failure'} on "
                f"{s0.get('equipmentId')} — reuse that corrective pattern."
            )

    return {
        "workOrderCount": len(work_orders),
        "similarFailureCount": len(similar),
        "citationCount": len(citations),
        "citations": citations[:8],
        "scheduleSuggestion": schedule_why,
        "degraded": len(citations) < 3,
        "reason": "" if len(citations) >= 3 else "insufficient-rca-citations",
    }
