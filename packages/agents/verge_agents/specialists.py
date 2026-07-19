"""Specialist digests for the advisory orchestrator (Phase 2.5 G1–G2).

Each specialist runs a fixed, read-only tool subset and returns a *distilled*
JSON digest — not a raw dump — so the orchestrator merge stays token-cheap
and grounded. Specialists never call the LLM themselves (context engineering).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .tools import ToolRegistry

TELEMETRY_TOOLS = (
    "get_finding",
    "get_zone_context",
    "get_recent_telemetry",
    "get_active_permits",
    "get_equipment_graph",
)
KNOWLEDGE_TOOLS = (
    "search_incident_memory",
    "search_plant_docs",
    "query_zone_graph",
)
COMPLIANCE_TOOLS = (
    "get_compliance_clauses",
    "get_compliance_gaps",
)
RCA_TOOLS = (
    "list_work_orders",
    "sensor_window",
    "manual_search",
    "similar_failures",
    "get_rca_digest",
)
LESSONS_TOOLS = ("match_lessons",)
MULTIMODAL_TOOLS = (
    "get_recent_voice_events",
    "get_recent_vision_events",
)


@dataclass
class SpecialistResult:
    name: str
    digest: dict[str, Any]
    evidence: list[dict] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)

    def to_wire(self) -> dict:
        return {
            "name": self.name,
            "digest": self.digest,
            "evidence": self.evidence,
            "refs": self.refs,
        }


def _run_tools(
    tools: ToolRegistry,
    names: tuple[str, ...],
    args_for: dict[str, dict],
) -> tuple[dict[str, Any], list[dict]]:
    facts: dict[str, Any] = {}
    steps: list[dict] = []
    for name in names:
        if tools.get(name) is None:
            continue
        args = args_for.get(name, {})
        raw = tools.execute(name, args)
        steps.append({"tool": name, "arguments": args, "result": raw, "specialist": True})
        try:
            facts[name] = json.loads(raw)
        except (ValueError, TypeError):
            facts[name] = raw
    return facts, steps


def _trim(obj: Any, *, max_list: int = 8, max_str: int = 400) -> Any:
    if isinstance(obj, str):
        return obj if len(obj) <= max_str else obj[: max_str - 1] + "…"
    if isinstance(obj, list):
        return [_trim(x, max_list=max_list, max_str=max_str) for x in obj[:max_list]]
    if isinstance(obj, dict):
        return {k: _trim(v, max_list=max_list, max_str=max_str) for k, v in obj.items()}
    return obj


def run_telemetry_specialist(
    tools: ToolRegistry,
    *,
    finding_id: str,
    zone_id: str,
) -> SpecialistResult:
    args = {
        "get_finding": {"finding_id": finding_id},
        "get_zone_context": {"zone_id": zone_id},
        "get_recent_telemetry": {"finding_id": finding_id},
        "get_active_permits": {"zone_id": zone_id},
        "get_equipment_graph": {"zone_id": zone_id},
    }
    facts, steps = _run_tools(tools, TELEMETRY_TOOLS, args)
    permits = facts.get("get_active_permits") or []
    zone = facts.get("get_zone_context") or {}
    finding = facts.get("get_finding") or {}
    digest = {
        "findingId": finding_id,
        "zoneId": zone_id,
        "title": finding.get("title") if isinstance(finding, dict) else None,
        "band": finding.get("leadTimeBand") if isinstance(finding, dict) else None,
        "lineage": (finding.get("lineage") if isinstance(finding, dict) else None) or [],
        "adjacentZones": zone.get("adjacentZones") if isinstance(zone, dict) else [],
        "activePermitCount": len(permits) if isinstance(permits, list) else 0,
        "permits": _trim(permits, max_list=6),
        "sensors": _trim(zone.get("sensors") if isinstance(zone, dict) else [], max_list=8),
        "equipment": _trim(zone.get("equipment") if isinstance(zone, dict) else [], max_list=8),
        "telemetry": _trim(facts.get("get_recent_telemetry") or {}, max_str=300),
        "equipmentGraph": _trim(facts.get("get_equipment_graph") or {}, max_list=6),
    }
    refs = []
    if isinstance(permits, list):
        refs.extend(
            str(p.get("permitId"))
            for p in permits
            if isinstance(p, dict) and p.get("permitId")
        )
    return SpecialistResult("telemetry", digest, steps, refs=[r for r in refs if r])


def run_knowledge_specialist(
    tools: ToolRegistry,
    *,
    finding_id: str,
    zone_id: str,
    title: str,
) -> SpecialistResult:
    query = f"{title} zone {zone_id} finding {finding_id}"
    args = {
        "search_incident_memory": {"query": query},
        "search_plant_docs": {"query": query},
        "query_zone_graph": {"zone_id": zone_id},
    }
    facts, steps = _run_tools(tools, KNOWLEDGE_TOOLS, args)
    memory = facts.get("search_incident_memory") or {}
    docs = facts.get("search_plant_docs") or {}
    graph = facts.get("query_zone_graph") or {}
    citations = []
    if isinstance(docs, dict):
        citations = docs.get("citations") or docs.get("chunks") or []
    if isinstance(memory, dict) and memory.get("citations"):
        citations = list(citations) + list(memory.get("citations") or [])
    digest = {
        "memory": _trim(memory, max_str=500),
        "documents": _trim(docs, max_list=5, max_str=400),
        "zoneGraph": _trim(graph, max_list=6),
        "citationCount": len(citations) if isinstance(citations, list) else 0,
    }
    refs: list[str] = []
    if isinstance(citations, list):
        for c in citations:
            if not isinstance(c, dict):
                continue
            for key in ("documentId", "chunkId", "id", "title"):
                if c.get(key):
                    refs.append(str(c[key]))
    return SpecialistResult("knowledge", digest, steps, refs=refs)


def run_compliance_specialist(
    tools: ToolRegistry,
    *,
    zone_id: str,
) -> SpecialistResult:
    args = {
        "get_compliance_clauses": {"zone_id": zone_id},
        "get_compliance_gaps": {"zone_id": zone_id},
    }
    facts, steps = _run_tools(tools, COMPLIANCE_TOOLS, args)
    clauses = facts.get("get_compliance_clauses") or []
    gaps = facts.get("get_compliance_gaps") or {}
    gap_board = gaps.get("gapBoard") if isinstance(gaps, dict) else []
    digest = {
        "clauseCount": len(clauses) if isinstance(clauses, list) else 0,
        "clauses": _trim(clauses, max_list=8, max_str=280),
        "gapBoard": _trim(gap_board, max_list=8, max_str=240),
        "evidenceLevels": gaps.get("evidenceLevels") if isinstance(gaps, dict) else {},
        "coverageDisclaimer": (
            gaps.get("coverageDisclaimer") if isinstance(gaps, dict) else None
        ),
    }
    refs = []
    if isinstance(clauses, list):
        refs = [
            str(c.get("clauseId"))
            for c in clauses
            if isinstance(c, dict) and c.get("clauseId")
        ]
    if isinstance(gap_board, list):
        refs.extend(
            str(c.get("clauseId"))
            for c in gap_board
            if isinstance(c, dict) and c.get("clauseId")
        )
    return SpecialistResult("compliance", digest, steps, refs=list(dict.fromkeys(refs)))


def run_rca_specialist(
    tools: ToolRegistry,
    *,
    finding_id: str,
    zone_id: str,
    title: str,
) -> SpecialistResult:
    args = {
        "list_work_orders": {"zone_id": zone_id},
        "sensor_window": {"finding_id": finding_id},
        "manual_search": {"query": f"{title} {zone_id} maintenance OEM"},
        "similar_failures": {"zone_id": zone_id},
        "get_rca_digest": {
            "finding_id": finding_id,
            "zone_id": zone_id,
            "title": title,
        },
    }
    facts, steps = _run_tools(tools, RCA_TOOLS, args)
    wos = facts.get("list_work_orders") or {}
    orders = wos.get("orders") if isinstance(wos, dict) else []
    if not isinstance(orders, list):
        orders = []
    similar = facts.get("similar_failures") or {}
    similar_list = similar.get("matches") if isinstance(similar, dict) else []
    if not isinstance(similar_list, list):
        similar_list = []
    digest_body = facts.get("get_rca_digest")
    if not isinstance(digest_body, dict):
        digest_body = {
            "workOrderCount": len(orders),
            "similarFailureCount": len(similar_list),
            "citationCount": 0,
            "citations": [],
            "degraded": True,
            "reason": "rca-digest-unavailable",
        }
    digest = {
        "workOrders": _trim(orders, max_list=6),
        "similarFailures": _trim(similar_list, max_list=5),
        "sensorWindow": _trim(facts.get("sensor_window") or {}, max_str=280),
        "manuals": _trim(facts.get("manual_search") or {}, max_list=4, max_str=280),
        "rca": _trim(digest_body, max_list=8, max_str=320),
    }
    refs: list[str] = []
    for wo in orders:
        if isinstance(wo, dict) and wo.get("orderId"):
            refs.append(str(wo["orderId"]))
    for c in digest_body.get("citations") or []:
        if isinstance(c, dict) and c.get("refId"):
            refs.append(str(c["refId"]))
    return SpecialistResult("rca", digest, steps, refs=list(dict.fromkeys(refs)))


def run_lessons_specialist(
    tools: ToolRegistry,
    *,
    finding_id: str,
    zone_id: str,
    title: str,
) -> SpecialistResult:
    args = {
        "match_lessons": {
            "zone_id": zone_id,
            "finding_id": finding_id,
            "title": title,
        }
    }
    facts, steps = _run_tools(tools, LESSONS_TOOLS, args)
    matched = facts.get("match_lessons") or {}
    lessons = matched.get("lessons") if isinstance(matched, dict) else []
    cards = matched.get("proactiveCards") if isinstance(matched, dict) else []
    if not isinstance(lessons, list):
        lessons = []
    if not isinstance(cards, list):
        cards = []
    digest = {
        "lessonCount": len(lessons),
        "lessons": _trim(lessons, max_list=5, max_str=320),
        "proactiveCards": _trim(cards, max_list=3, max_str=280),
    }
    refs: list[str] = []
    for lesson in lessons:
        if not isinstance(lesson, dict):
            continue
        if lesson.get("lessonId"):
            refs.append(str(lesson["lessonId"]))
        for r in lesson.get("sourceRefs") or []:
            refs.append(str(r))
    return SpecialistResult("lessons", digest, steps, refs=list(dict.fromkeys(refs)))


def run_multimodal_specialist(
    tools: ToolRegistry,
    *,
    zone_id: str,
) -> SpecialistResult:
    args = {
        "get_recent_voice_events": {"zone_id": zone_id},
        "get_recent_vision_events": {"zone_id": zone_id},
    }
    facts, steps = _run_tools(tools, MULTIMODAL_TOOLS, args)
    voice = facts.get("get_recent_voice_events") or {}
    vision = facts.get("get_recent_vision_events") or {}
    digest = {
        "voice": _trim(voice, max_list=5),
        "vision": _trim(vision, max_list=5),
    }
    refs: list[str] = []
    for ev in (voice.get("events") or []) if isinstance(voice, dict) else []:
        if not isinstance(ev, dict):
            continue
        eid = ev.get("eventId") or ev.get("source")
        if eid:
            refs.append(str(eid))
        elif ev.get("transcript"):
            refs.append(f"voice:{(ev.get('transcript') or '')[:40]}")
    for det in (vision.get("detections") or []) if isinstance(vision, dict) else []:
        if not isinstance(det, dict):
            continue
        label = det.get("label") or det.get("cameraId")
        if label:
            refs.append(f"vision:{label}")
    return SpecialistResult("multimodal", digest, steps, refs=refs[:12])


def run_all_specialists(
    tools: ToolRegistry,
    *,
    finding_id: str,
    zone_id: str,
    title: str,
    include_multimodal: bool = True,
) -> list[SpecialistResult]:
    results = [
        run_telemetry_specialist(tools, finding_id=finding_id, zone_id=zone_id),
        run_knowledge_specialist(
            tools, finding_id=finding_id, zone_id=zone_id, title=title
        ),
        run_compliance_specialist(tools, zone_id=zone_id),
    ]
    if tools.get("list_work_orders") or tools.get("similar_failures"):
        results.append(
            run_rca_specialist(
                tools, finding_id=finding_id, zone_id=zone_id, title=title
            )
        )
    if tools.get("match_lessons"):
        results.append(
            run_lessons_specialist(
                tools, finding_id=finding_id, zone_id=zone_id, title=title
            )
        )
    if include_multimodal and (
        tools.get("get_recent_voice_events") or tools.get("get_recent_vision_events")
    ):
        results.append(run_multimodal_specialist(tools, zone_id=zone_id))
    return results
