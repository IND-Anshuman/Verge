"""Lessons match + proactive cards (Phase 3C)."""

from __future__ import annotations

from verge_lessons import default_corpus, match_lessons, proactive_cards


def test_corpus_loads_fixtures():
    corpus = default_corpus()
    assert len(corpus.lessons) >= 2
    ids = {lesson.lesson_id for lesson in corpus.lessons}
    assert "LL-2024-GAS-SEAL" in ids


def test_match_fires_for_b04_hot_work_gas():
    corpus = default_corpus()
    lessons = match_lessons(
        corpus,
        zone_id="B-04",
        title="hot work with radio gas smell near battery",
        lineage=["LEL-04"],
        permit_kinds=["hot-work"],
        hazards=["gas", "smell", "lel"],
    )
    assert lessons
    assert lessons[0]["lessonId"] == "LL-2024-GAS-SEAL"
    assert lessons[0]["matchScore"] >= 3


def test_proactive_card_requires_source_refs():
    cards = proactive_cards(
        [
            {
                "lessonId": "LL-X",
                "title": "uncited",
                "summary": "x",
                "sourceRefs": [],
                "matchScore": 9,
            },
            {
                "lessonId": "LL-2024-GAS-SEAL",
                "title": "cited",
                "summary": "y",
                "sourceRefs": ["WO-2024-142"],
                "matchScore": 8,
            },
        ],
        finding_id="F-1",
    )
    assert len(cards) == 1
    assert cards[0]["severity"] == "LESSON"
    assert cards[0]["sourceRefs"] == ["WO-2024-142"]


def test_summit_rehearsal_fires_at_least_one_card():
    corpus = default_corpus()
    lessons = match_lessons(
        corpus,
        zone_id="B-04",
        title="hot work with radio gas smell near battery",
        lineage=["LEL-04"],
        permit_kinds=["hot-work"],
        hazards=["gas", "smell"],
    )
    cards = proactive_cards(lessons, finding_id="F-DEMO-LESSON")
    assert len(cards) >= 1
