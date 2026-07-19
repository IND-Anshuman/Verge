"""Lessons-learned plane — mine corpus + match live context (Phase 3C)."""

from .corpus import Lesson, LessonCorpus, default_corpus
from .match import match_lessons, proactive_cards

__all__ = [
    "Lesson",
    "LessonCorpus",
    "default_corpus",
    "match_lessons",
    "proactive_cards",
]
__version__ = "0.1.0"
