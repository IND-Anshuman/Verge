"""Curated lessons corpus (closed findings / near-miss / NCR). Honest fixtures."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures"
DEFAULT_JSON = FIXTURES / "vizag-lessons.json"


@dataclass(frozen=True)
class Lesson:
    lesson_id: str
    title: str
    summary: str
    zone_ids: tuple[str, ...]
    hazard_tags: tuple[str, ...]
    permit_kinds: tuple[str, ...]
    source_refs: tuple[str, ...]
    severity: str = "LESSON"

    def to_dict(self) -> dict[str, Any]:
        return {
            "lessonId": self.lesson_id,
            "title": self.title,
            "summary": self.summary,
            "zoneIds": list(self.zone_ids),
            "hazardTags": list(self.hazard_tags),
            "permitKinds": list(self.permit_kinds),
            "sourceRefs": list(self.source_refs),
            "severity": self.severity,
        }


@dataclass
class LessonCorpus:
    lessons: list[Lesson] = field(default_factory=list)

    @classmethod
    def from_json(cls, path: Path | str | None = None) -> LessonCorpus:
        p = Path(path) if path else DEFAULT_JSON
        if not p.exists():
            return cls([])
        raw = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return cls([])
        lessons: list[Lesson] = []
        for row in raw:
            if not isinstance(row, dict) or not row.get("lessonId"):
                continue
            lessons.append(
                Lesson(
                    lesson_id=str(row["lessonId"]),
                    title=str(row.get("title") or ""),
                    summary=str(row.get("summary") or ""),
                    zone_ids=tuple(row.get("zoneIds") or []),
                    hazard_tags=tuple(t.lower() for t in (row.get("hazardTags") or [])),
                    permit_kinds=tuple(row.get("permitKinds") or []),
                    source_refs=tuple(row.get("sourceRefs") or []),
                    severity=str(row.get("severity") or "LESSON"),
                )
            )
        return cls(lessons)


_DEFAULT: LessonCorpus | None = None


def default_corpus() -> LessonCorpus:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = LessonCorpus.from_json()
    return _DEFAULT
