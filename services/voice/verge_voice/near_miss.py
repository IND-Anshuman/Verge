"""Near-miss voice evidence extraction."""

from __future__ import annotations

from typing import Any

from .transcribe import VoiceResult, transcribe_audio


def near_miss_from_audio(
    audio: bytes,
    *,
    filename: str = "near-miss.wav",
    content_type: str = "application/octet-stream",
    finding_id: str | None = None,
) -> dict[str, Any]:
    result = transcribe_audio(audio, filename=filename, content_type=content_type)
    body = result.to_dict()
    body["kind"] = "voice-near-miss"
    body["findingId"] = finding_id
    return body


def near_miss_from_transcript(
    transcript: str,
    *,
    finding_id: str | None = None,
) -> dict[str, Any]:
    from .transcribe import structure_handover

    result = VoiceResult(transcript=transcript, structured=structure_handover(transcript))
    body = result.to_dict()
    body["kind"] = "voice-near-miss"
    body["findingId"] = finding_id
    return body
