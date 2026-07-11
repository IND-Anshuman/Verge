"""Near-miss voice evidence extraction."""

from __future__ import annotations

from typing import Any

from verge_llm import LLMProvider

from .transcribe import (
    VoiceResult,
    enrich_structured_with_llm,
    structure_handover,
    transcribe_audio,
)


def near_miss_from_audio(
    audio: bytes,
    *,
    filename: str = "near-miss.wav",
    content_type: str = "application/octet-stream",
    finding_id: str | None = None,
    provider: LLMProvider | None = None,
) -> dict[str, Any]:
    result = transcribe_audio(
        audio, filename=filename, content_type=content_type, provider=provider
    )
    body = result.to_dict()
    body["kind"] = "voice-near-miss"
    body["findingId"] = finding_id
    return body


def near_miss_from_transcript(
    transcript: str,
    *,
    finding_id: str | None = None,
    provider: LLMProvider | None = None,
) -> dict[str, Any]:
    structured = enrich_structured_with_llm(
        transcript, structure_handover(transcript), provider=provider
    )
    result = VoiceResult(transcript=transcript, structured=structured)
    body = result.to_dict()
    body["kind"] = "voice-near-miss"
    body["findingId"] = finding_id
    return body
