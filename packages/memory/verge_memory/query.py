"""Free-text memory query over Cognee."""

from __future__ import annotations

import os
from typing import Any

from verge_llm import LLMProvider, Message
from verge_schema.findings import RiskFinding

from .client import CogneeClient
from .datasets import dataset_name
from .retrieve import _result_items, _text_from_result, ensure_seeded

_SYNTHESIS_SYSTEM_PROMPT = (
    "You answer a question using ONLY the numbered excerpts provided. Write "
    "1-3 sentences and cite excerpts inline like [1], [2]. If the excerpts do "
    "not contain enough to answer, say so plainly instead of guessing."
)


def _empty(*, degraded: bool, reason: str | None = None) -> dict:
    body = {"answer": "", "citations": [], "degraded": degraded}
    if reason:
        body["reason"] = reason
    return body


def _citation_from_item(item: Any, index: int) -> dict:
    if isinstance(item, dict):
        source = (
            item.get("source")
            or item.get("file_name")
            or item.get("filename")
            or item.get("document")
            or "cognee"
        )
        title = item.get("title") or item.get("name") or f"Memory result {index}"
        excerpt = _text_from_result(item)
        return {"id": str(source), "title": str(title), "excerpt": excerpt[:280]}
    text = _text_from_result(item)
    return {"id": f"cognee-{index}", "title": f"Memory result {index}", "excerpt": text[:280]}


def _answer_from_items(items: list[Any]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return _text_from_result(items[0])
    parts = [_text_from_result(item) for item in items[:3]]
    return "\n\n".join(part for part in parts if part)


def _synthesize_answer(
    provider: LLMProvider | None, query: str, citations: list[dict]
) -> tuple[str, bool]:
    """A real grounded answer over the retrieved citations when an LLM is
    reachable (same "use only the provided facts" pattern as
    ``orchestrator/report.py``); the caller's raw-snippet answer is the
    fallback, never a crash or a fabricated claim (P1/P4)."""
    if provider is None or not citations:
        return "", True
    excerpts = "\n".join(f"[{c['id']}] {c['title']}: {c['excerpt']}" for c in citations)
    messages = [
        Message(role="system", content=_SYNTHESIS_SYSTEM_PROMPT),
        Message(role="user", content=f"Question: {query}\n\nExcerpts:\n{excerpts}"),
    ]
    completion = provider.complete(messages, max_tokens=220)
    if completion.degraded or not completion.text.strip():
        return "", True
    return completion.text.strip(), False


def query_memory(
    query: str,
    *,
    finding: RiskFinding | None = None,
    client: CogneeClient | None = None,
    provider: LLMProvider | None = None,
    env: dict[str, str] | None = None,
) -> dict:
    if env is None:
        env = dict(os.environ)
    dataset = dataset_name(env)
    client = client or CogneeClient.from_env(env)

    cleaned = " ".join(query.split())
    if not cleaned:
        return _empty(degraded=True, reason="empty query")

    seeded = ensure_seeded(client, dataset)
    if not seeded.ok:
        return _empty(degraded=True, reason=seeded.reason)

    scoped_query = cleaned
    if finding is not None:
        scoped_query = (
            f"{cleaned}\n\n"
            f"Finding context: {finding.finding_id} in zone {finding.zone_id}. "
            f"Title: {finding.title}. Lineage: {', '.join(finding.lineage)}."
        )

    result = client.search(dataset, scoped_query, top_k=6)
    if not result.ok:
        return _empty(degraded=True, reason=result.reason)

    items = _result_items(result)
    citations = [_citation_from_item(item, i) for i, item in enumerate(items[:5], start=1)]

    answer, narrative_degraded = _synthesize_answer(provider, cleaned, citations)
    if narrative_degraded:
        answer = _answer_from_items(items)  # raw-snippet fallback -- always available

    return {
        "answer": answer,
        "citations": citations,
        "degraded": False,
        "narrativeDegraded": narrative_degraded,
    }
