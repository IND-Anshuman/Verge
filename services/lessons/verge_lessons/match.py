"""Rule-feature matcher vs live finding context. No invented lessons."""

from __future__ import annotations

from typing import Any

from .corpus import Lesson, LessonCorpus


def _score_lesson(
    lesson: Lesson,
    *,
    zone_id: str,
    title: str,
    lineage: list[str],
    permit_kinds: list[str],
    hazards: list[str],
) -> int:
    score = 0
    title_l = (title or "").lower()
    blob = f"{title_l} {' '.join(lineage)}".lower()
    if zone_id and zone_id in lesson.zone_ids:
        score += 3
    for pk in permit_kinds:
        if pk in lesson.permit_kinds:
            score += 2
    for tag in lesson.hazard_tags:
        if tag in blob or tag in {h.lower() for h in hazards}:
            score += 2
    return score


def match_lessons(
    corpus: LessonCorpus,
    *,
    zone_id: str,
    title: str = "",
    lineage: list[str] | None = None,
    permit_kinds: list[str] | None = None,
    hazards: list[str] | None = None,
    min_score: int = 3,
    limit: int = 5,
) -> list[dict[str, Any]]:
    scored: list[tuple[int, Lesson]] = []
    for lesson in corpus.lessons:
        sc = _score_lesson(
            lesson,
            zone_id=zone_id,
            title=title,
            lineage=list(lineage or []),
            permit_kinds=list(permit_kinds or []),
            hazards=list(hazards or []),
        )
        if sc >= min_score:
            scored.append((sc, lesson))
    scored.sort(key=lambda x: (-x[0], x[1].lesson_id))
    out = []
    for sc, lesson in scored[:limit]:
        row = lesson.to_dict()
        row["matchScore"] = sc
        out.append(row)
    return out


def proactive_cards(
    matches: list[dict[str, Any]],
    *,
    finding_id: str | None = None,
) -> list[dict[str, Any]]:
    """Mission Control cards — severity LESSON, always cited via sourceRefs."""
    cards = []
    for m in matches:
        refs = m.get("sourceRefs") or []
        if not refs:
            continue  # never push uncited lessons
        cards.append({
            "severity": "LESSON",
            "lessonId": m.get("lessonId"),
            "title": m.get("title"),
            "summary": m.get("summary"),
            "findingId": finding_id,
            "sourceRefs": refs,
            "matchScore": m.get("matchScore"),
        })
    return cards
