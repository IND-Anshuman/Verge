"""Metrics for advisory brief gold sets."""

from __future__ import annotations

from collections.abc import Iterable

from verge_agents import TwinCatalog, validate_brief
from verge_agents.validator import brief_text_blobs, extract_candidate_tags


def invented_tag_rate(
    briefs: Iterable[dict],
    catalog: TwinCatalog,
) -> dict[str, float]:
    """Fraction of briefs that mention a twin tag not on the plant (target: 0)."""
    briefs = list(briefs)
    if not briefs:
        return {"rate": 0.0, "n": 0.0, "violations": 0.0}
    violations = 0
    for brief in briefs:
        tags: set[str] = set()
        for blob in brief_text_blobs(brief):
            for tag in extract_candidate_tags(blob, catalog):
                if catalog.all_ids() and not catalog.contains(tag):
                    tags.add(tag)
        if tags:
            violations += 1
    return {
        "rate": round(violations / len(briefs), 4),
        "n": float(len(briefs)),
        "violations": float(violations),
    }


def citation_precision(
    barriers: Iterable[dict],
    allowed_refs: set[str],
) -> dict[str, float]:
    """Share of barriers whose supportedBy intersects allowed tool/ref ids."""
    barriers = [b for b in barriers if isinstance(b, dict)]
    if not barriers:
        return {"precision": 1.0, "n": 0.0, "hit": 0.0}
    allowed_l = {a.lower() for a in allowed_refs}
    hit = 0
    for b in barriers:
        hay = " ".join(
            str(b.get(k) or "") for k in ("supportedBy", "rationale", "action")
        ).lower()
        if any(ref in hay for ref in allowed_l if ref):
            hit += 1
    return {
        "precision": round(hit / len(barriers), 4),
        "n": float(len(barriers)),
        "hit": float(hit),
    }


def groundedness_proxy(
    summary: str,
    digest_blob: str,
    *,
    min_overlap: int = 2,
) -> dict[str, float | bool]:
    """Cheap groundedness: summary shares content tokens with specialist digests."""
    if not (summary or "").strip():
        return {"grounded": False, "overlap": 0.0}
    s_toks = {t for t in summary.lower().split() if len(t) > 3}
    d_toks = {t for t in digest_blob.lower().split() if len(t) > 3}
    overlap = len(s_toks & d_toks)
    return {"grounded": overlap >= min_overlap, "overlap": float(overlap)}


def validator_clears_gold(
    brief: dict,
    catalog: TwinCatalog,
    *,
    evidence_tools: list[str],
) -> bool:
    """True when validate_brief reports ok on a gold (already-clean) brief."""
    _, report = validate_brief(brief, catalog, evidence_tools=evidence_tools)
    return report.ok
