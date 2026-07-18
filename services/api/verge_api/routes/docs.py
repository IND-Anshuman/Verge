"""Document intelligence API — ingest, list, entities, grounded ask."""

from __future__ import annotations

import os

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from verge_docintel import DocIntelStore, process_bytes
from verge_docintel.pipeline import chunk_text
from verge_docintel.resolve import resolve_entities
from verge_llm import Message, provider_from_env

from verge_api.doc_hooks import maybe_cognify_document, maybe_sync_entities_neo4j

router = APIRouter(tags=["knowledge"])
DOC_FILE = File(...)
TITLE_FORM = Form(None)
PLANT_PACK_FORM = Form(None)


def _store(request: Request) -> DocIntelStore:
    store = getattr(request.app.state, "docintel", None)
    if store is None:
        store = DocIntelStore()
        request.app.state.docintel = store
    return store


@router.get("/docs")
def list_docs(request: Request) -> dict:
    store = _store(request)
    docs = [d.model_dump(by_alias=True, mode="json") for d in store.list_documents()]
    return {"documents": docs, "count": len(docs)}


@router.get("/docs/{document_id}")
def get_doc(document_id: str, request: Request) -> dict:
    store = _store(request)
    doc = store.get(document_id)
    if doc is None:
        raise HTTPException(404, "document not found")
    chunks = [c.model_dump(by_alias=True, mode="json") for c in store.chunks.get(document_id, [])]
    entities = [
        e.model_dump(by_alias=True, mode="json") for e in store.entities.get(document_id, [])
    ]
    return {
        "document": doc.model_dump(by_alias=True, mode="json"),
        "chunks": chunks,
        "entities": entities,
    }


@router.post("/docs/ingest")
async def ingest_doc(
    request: Request,
    file: UploadFile = DOC_FILE,
    title: str | None = TITLE_FORM,
    plantPack: str | None = PLANT_PACK_FORM,
) -> dict:
    store = _store(request)
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty upload")
    asset = process_bytes(
        store,
        data,
        filename=file.filename or "upload.bin",
        mime_type=file.content_type or "application/octet-stream",
        title=title,
        plant_pack=plantPack,
    )
    plant = getattr(request.app.state, "plant", None)
    if plant is not None and asset.document_id in store.entities:
        store.entities[asset.document_id] = resolve_entities(
            store.entities[asset.document_id],
            zone_ids=set(plant.zones),
            sensor_ids=set(plant.sensors),
            equipment_ids=set(plant.equipment),
        )
    ents = store.entities.get(asset.document_id, [])
    resolved = sum(1 for e in ents if e.resolved_ref)
    return {
        "document": asset.model_dump(by_alias=True, mode="json"),
        "entityCount": len(ents),
        "chunkCount": len(store.chunks.get(asset.document_id, [])),
        "resolvedEntityCount": resolved,
        "hooks": {
            "cognee": maybe_cognify_document(store, asset),
            "neo4j": maybe_sync_entities_neo4j(store, asset),
        },
    }


class AskBody(BaseModel):
    query: str = Field(min_length=2)
    limit: int = Field(default=6, ge=1, le=20)


def _retrieve(store: DocIntelStore, query: str, *, limit: int) -> list[dict]:
    q = query.lower().split()
    scored: list[tuple[int, dict]] = []
    for doc_id, chunks in store.chunks.items():
        doc = store.documents.get(doc_id)
        for ch in chunks:
            text = ch.text.lower()
            score = sum(1 for tok in q if tok in text)
            if score:
                scored.append(
                    (
                        score,
                        {
                            "documentId": doc_id,
                            "title": doc.title if doc else doc_id,
                            "chunkId": ch.chunk_id,
                            "page": ch.page,
                            "excerpt": ch.text[:500],
                            "score": score,
                        },
                    )
                )
    scored.sort(key=lambda x: x[0], reverse=True)
    return [row for _, row in scored[:limit]]


def _cognee_citations(query: str, *, llm, limit: int) -> tuple[list[dict], dict | None]:
    """Best-effort Cognee memory citations; never raises."""
    try:
        from verge_memory.client import cognee_enabled_from_env
        from verge_memory.query import query_memory

        env = dict(os.environ)
        if not cognee_enabled_from_env(env):
            return [], None
        mem = query_memory(query, provider=llm, env=env)
        if mem.get("degraded") and not mem.get("citations"):
            return [], {"degraded": True, "reason": mem.get("reason") or "cognee-empty"}
        rows: list[dict] = []
        for c in mem.get("citations") or []:
            if not isinstance(c, dict):
                continue
            excerpt = (c.get("excerpt") or "").strip()
            if not excerpt:
                continue
            rows.append(
                {
                    "documentId": str(c.get("id") or "cognee"),
                    "title": str(c.get("title") or "Plant memory"),
                    "chunkId": None,
                    "page": None,
                    "excerpt": excerpt[:500],
                    "score": 0,
                    "source": "cognee",
                }
            )
            if len(rows) >= limit:
                break
        return rows, {
            "degraded": bool(mem.get("degraded")),
            "reason": mem.get("reason") or "",
            "narrativeDegraded": bool(mem.get("narrativeDegraded")),
            "answer": mem.get("answer") or "",
        }
    except Exception as exc:  # noqa: BLE001
        return [], {"degraded": True, "reason": f"cognee:{type(exc).__name__}"}


@router.post("/knowledge/ask")
def knowledge_ask(body: AskBody, request: Request) -> dict:
    """Hybrid grounded ask: DocIntel chunks + Cognee plant memory when configured."""
    store = _store(request)
    llm = getattr(request.app.state, "llm", None) or provider_from_env()
    doc_citations = _retrieve(store, body.query, limit=body.limit)
    for c in doc_citations:
        c.setdefault("source", "docintel")
    cognee_rows, cognee_meta = _cognee_citations(
        body.query, llm=llm, limit=max(2, body.limit // 2)
    )

    # Prefer DocIntel first, then Cognee — cap total for the prompt.
    citations = list(doc_citations) + list(cognee_rows)
    citations = citations[: max(body.limit, len(doc_citations))]
    sources = sorted({str(c.get("source") or "docintel") for c in citations})

    if not citations:
        reason = "empty-corpus"
        if store.documents:
            reason = "no-matching-chunks"
        if cognee_meta and cognee_meta.get("degraded"):
            reason = cognee_meta.get("reason") or reason
        return {
            "answer": "",
            "citations": [],
            "degraded": True,
            "reason": reason,
            "sources": [],
            "cognee": cognee_meta,
        }

    # If DocIntel empty but Cognee synthesized an answer, reuse it (still cited).
    if (
        not doc_citations
        and cognee_meta
        and (cognee_meta.get("answer") or "").strip()
        and not cognee_meta.get("degraded")
    ):
        return {
            "answer": cognee_meta["answer"].strip(),
            "citations": citations,
            "degraded": False,
            "reason": "",
            "sources": sources,
            "cognee": {k: v for k, v in cognee_meta.items() if k != "answer"},
        }

    facts = "\n\n".join(
        f"[{i + 1}] ({c.get('source', 'docintel')}:{c['title']}) {c['excerpt']}"
        for i, c in enumerate(citations)
    )
    prompt = (
        "Answer ONLY from the numbered facts (plant docs and memory). "
        "If insufficient, say you cannot answer from the corpus. "
        "Cite fact numbers like [1].\n\n"
        f"Question: {body.query}\n\nFacts:\n{facts}"
    )
    completion = llm.complete([Message(role="user", content=prompt)])
    if completion.degraded or not (completion.text or "").strip():
        answer = "Based on retrieved documents:\n" + "\n".join(
            f"- [{i + 1}] {c['excerpt'][:240]}" for i, c in enumerate(citations[:3])
        )
        return {
            "answer": answer,
            "citations": citations,
            "degraded": True,
            "reason": "llm-degraded",
            "sources": sources,
            "cognee": (
                {k: v for k, v in cognee_meta.items() if k != "answer"}
                if cognee_meta
                else None
            ),
        }
    return {
        "answer": completion.text.strip(),
        "citations": citations,
        "degraded": False,
        "reason": "",
        "sources": sources,
        "cognee": (
            {k: v for k, v in cognee_meta.items() if k != "answer"}
            if cognee_meta
            else None
        ),
    }


# Keep chunk_text imported for potential future reprocess route.
_ = chunk_text
