"""Advisory orchestrator — specialists fan-out + merge + validate (Phase 2.5).

Flow:
  1. Run Telemetry / Knowledge / Compliance (/ Multimodal) specialists
  2. Merge digests with one LLM call into a JSON brief (or degraded fact sheet)
  3. Deterministic validator strips invented twin tags / uncited barriers

Replaces the single generalist investigator loop for production paths while
keeping ``investigate()`` as the stable public entrypoint.
"""

from __future__ import annotations

import json

from verge_llm import LLMProvider, Message

from .specialists import SpecialistResult, run_all_specialists
from .tools import ToolRegistry
from .twin_catalog import TwinCatalog
from .validator import validate_brief

BRIEF_KEYS = ("summary", "hypotheses", "recommendedBarriers", "regulatoryRefs", "openQuestions")

ORCHESTRATOR_SYSTEM = """You are the Verge advisory orchestrator for an Indian \
heavy-industry plant. Specialists have already gathered evidence digests. \
Synthesize ONLY from those digests — never invent sensor readings, equipment \
IDs, zones, permits, work-order IDs, lesson IDs, or clause IDs that do not \
appear in the digests.

Return STRICT JSON (no markdown fence) with keys:
  summary            one-paragraph situation assessment
  hypotheses         array of {cause, likelihood: high|medium|low, supportedBy}
  recommendedBarriers array of {action, urgency: immediate|this-shift|planned, \
rationale, supportedBy}
  regulatoryRefs     array of {clauseId, relevance}
  openQuestions      array of strings — what digests could NOT verify

Every hypothesis and recommendedBarrier MUST set supportedBy to a specialist \
name or tool/ref id from the digests. Prefer hierarchy of controls. If \
telemetry or knowledge is degraded/empty, say so in openQuestions."""


def _parse_brief(text: str) -> dict | None:
    """Parse model JSON; tolerate fences and leading/trailing prose."""
    raw = (text or "").strip()
    if not raw:
        return None
    if raw.startswith("```"):
        # Drop opening fence line (``` or ```json), then closing fence.
        parts = raw.split("\n", 1)
        raw = parts[1] if len(parts) > 1 else ""
        if "```" in raw:
            raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()
    # If the model wrapped the object in prose, take the outermost JSON object.
    if not raw.startswith("{"):
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            raw = raw[start : end + 1]
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict) or "summary" not in data:
        return None
    return {k: data.get(k, [] if k != "summary" else "") for k in BRIEF_KEYS}


def _degraded_brief(
    finding_id: str,
    zone_id: str,
    specialists: list[SpecialistResult],
) -> dict:
    tel = next((s for s in specialists if s.name == "telemetry"), None)
    comp = next((s for s in specialists if s.name == "compliance"), None)
    permits = 0
    if tel and isinstance(tel.digest.get("activePermitCount"), int):
        permits = tel.digest["activePermitCount"]
    clauses = []
    if comp and isinstance(comp.digest.get("clauses"), list):
        clauses = [
            {"clauseId": c.get("clauseId", ""), "relevance": c.get("title", "")}
            for c in comp.digest["clauses"]
            if isinstance(c, dict)
        ][:5]
    return {
        "summary": (
            f"Deterministic fact sheet for {finding_id} (no LLM — specialists "
            f"only, no synthesis). Zone {zone_id}: {permits} active permit(s). "
            "Telemetry, knowledge, compliance, RCA, and lessons digests "
            "attached as evidence when tools were available."
        ),
        "hypotheses": [],
        "recommendedBarriers": [],
        "regulatoryRefs": clauses,
        "openQuestions": [
            "LLM synthesis unavailable — hypotheses and barrier recommendations "
            "require the intelligence plane or a safety engineer's review."
        ],
    }


def _merge_with_llm(
    provider: LLMProvider,
    *,
    finding_id: str,
    zone_id: str,
    title: str,
    specialists: list[SpecialistResult],
    model: str | None,
) -> tuple[dict, bool, str | None, str]:
    digest_blob = json.dumps(
        {s.name: s.digest for s in specialists},
        default=str,
    )
    user = (
        f"Finding {finding_id} in zone {zone_id}: \"{title}\".\n"
        f"Specialist digests (JSON):\n{digest_blob}\n\n"
        "Produce the JSON brief."
    )
    completion = provider.chat(
        [Message("system", ORCHESTRATOR_SYSTEM), Message("user", user)],
        tools=None,
        model=model,
        max_tokens=2400,
    )
    if completion.degraded:
        return (
            _degraded_brief(finding_id, zone_id, specialists),
            True,
            completion.reason,
            completion.model,
        )
    brief = _parse_brief(completion.text)
    if brief is None:
        brief = {
            "summary": (completion.text or "")[:2000],
            "hypotheses": [],
            "recommendedBarriers": [],
            "regulatoryRefs": [],
            "openQuestions": ["response was not valid JSON"],
        }
    return brief, False, None, completion.model


def orchestrate(
    provider: LLMProvider,
    *,
    finding_id: str,
    zone_id: str,
    title: str,
    tools: ToolRegistry,
    catalog: TwinCatalog | None = None,
    model: str | None = None,
    include_multimodal: bool = True,
) -> dict:
    """Run specialists → merge → validate. Always returns a wire-shaped dict."""
    catalog = catalog or TwinCatalog.empty()
    specialists = run_all_specialists(
        tools,
        finding_id=finding_id,
        zone_id=zone_id,
        title=title,
        include_multimodal=include_multimodal,
    )
    evidence: list[dict] = []
    for s in specialists:
        evidence.extend(s.evidence)

    brief, degraded, reason, used_model = _merge_with_llm(
        provider,
        finding_id=finding_id,
        zone_id=zone_id,
        title=title,
        specialists=specialists,
        model=model,
    )

    known_refs: list[str] = []
    for s in specialists:
        known_refs.extend(s.refs)
    evidence_tools = [e["tool"] for e in evidence if e.get("tool")]

    brief, report = validate_brief(
        brief,
        catalog,
        evidence_tools=evidence_tools,
        known_refs=known_refs,
        extra_known=[finding_id, zone_id, *known_refs],
    )

    return {
        "findingId": finding_id,
        "brief": brief,
        "evidence": evidence,
        "specialists": [s.to_wire() for s in specialists],
        "validation": report.to_wire(),
        "degraded": degraded,
        "reason": reason,
        "model": used_model,
        "orchestrator": "advisory-v1",
    }
