"""Lessons-learned API — match + proactive Mission Control cards (Phase 3C)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from verge_lessons import default_corpus, match_lessons, proactive_cards

router = APIRouter(tags=["lessons"])


def _corpus(request: Request):
    return getattr(request.app.state, "lessons", None) or default_corpus()


class MatchBody(BaseModel):
    zoneId: str = "B-04"
    title: str = "hot work gas smell"
    findingId: str | None = None
    lineage: list[str] = Field(default_factory=list)
    permitKinds: list[str] = Field(default_factory=lambda: ["hot-work"])
    hazards: list[str] = Field(default_factory=lambda: ["gas", "smell"])


@router.get("/lessons")
def list_lessons(request: Request) -> dict:
    corpus = _corpus(request)
    rows = [lesson.to_dict() for lesson in corpus.lessons]
    return {"lessons": rows, "count": len(rows)}


@router.post("/lessons/match")
def match_body(body: MatchBody, request: Request) -> dict:
    corpus = _corpus(request)
    lessons = match_lessons(
        corpus,
        zone_id=body.zoneId,
        title=body.title,
        lineage=body.lineage,
        permit_kinds=body.permitKinds,
        hazards=body.hazards,
    )
    cards = proactive_cards(lessons, finding_id=body.findingId)
    return {
        "lessons": lessons,
        "proactiveCards": cards,
        "count": len(lessons),
        "demoBeat": "lessons" if cards else "lessons-no-card",
    }


@router.get("/lessons/proactive")
def proactive_demo(request: Request, zoneId: str = "B-04") -> dict:
    """Summit rehearsal: fire at least one LESSON card for B-04 hot-work gas."""
    corpus = _corpus(request)
    lessons = match_lessons(
        corpus,
        zone_id=zoneId,
        title="hot work with radio gas smell near battery",
        lineage=["LEL-04"],
        permit_kinds=["hot-work"],
        hazards=["gas", "smell", "lel"],
    )
    cards = proactive_cards(lessons, finding_id="F-DEMO-LESSON")
    return {
        "zoneId": zoneId,
        "proactiveCards": cards,
        "count": len(cards),
        "fired": len(cards) >= 1,
        "demoBeat": "lessons",
    }
