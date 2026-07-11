"""Speechmatics batch transcription with structured handover extraction."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx
from verge_llm import LLMProvider, Message


@dataclass(frozen=True)
class SpeechmaticsSettings:
    api_key: str | None = None
    base_url: str = "https://eu1.asr.api.speechmatics.com/v2"
    language: str = "en"
    timeout_s: float = 30.0
    poll_interval_s: float = 0.25
    max_polls: int = 20

    @classmethod
    def from_env(cls, env: dict[str, str]) -> SpeechmaticsSettings:
        region = env.get("SPEECHMATICS_REGION", "eu1")
        base_url = env.get("SPEECHMATICS_BASE_URL") or (
            f"https://{region}.asr.api.speechmatics.com/v2"
        )
        return cls(
            api_key=env.get("SPEECHMATICS_API_KEY"),
            base_url=base_url.rstrip("/"),
            language=env.get("SPEECHMATICS_LANGUAGE", "en"),
            timeout_s=float(env.get("SPEECHMATICS_TIMEOUT_S", "30")),
            poll_interval_s=float(env.get("SPEECHMATICS_POLL_INTERVAL_S", "0.25")),
            max_polls=int(env.get("SPEECHMATICS_MAX_POLLS", "20")),
        )

    def missing_reason(self) -> str | None:
        if not self.api_key:
            return "missing SPEECHMATICS_API_KEY"
        return None


@dataclass(frozen=True)
class VoiceResult:
    transcript: str
    structured: dict[str, Any]
    degraded: bool = False
    reason: str | None = None
    provider: str = "speechmatics"
    job_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        body = {
            "transcript": self.transcript,
            "structured": self.structured,
            "degraded": self.degraded,
            "provider": self.provider,
        }
        if self.job_id:
            body["jobId"] = self.job_id
        if self.reason:
            body["reason"] = self.reason
        return body


def _empty_structured() -> dict[str, Any]:
    return {"summary": "", "hazards": [], "zones": [], "actions": []}


def _degraded(reason: str) -> VoiceResult:
    return VoiceResult(transcript="", structured=_empty_structured(), degraded=True, reason=reason)


def _headers(settings: SpeechmaticsSettings) -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.api_key}"}


def _job_id(data: dict[str, Any]) -> str | None:
    for key in ("id", "job_id", "jobId"):
        if value := data.get(key):
            return str(value)
    job = data.get("job")
    if isinstance(job, dict):
        for key in ("id", "job_id", "jobId"):
            if value := job.get(key):
                return str(value)
    return None


def _job_status(data: dict[str, Any]) -> str:
    job = data.get("job", data)
    if isinstance(job, dict):
        return str(job.get("status", "")).lower()
    return ""


def _transcript_text(data: Any) -> str:
    if isinstance(data, str):
        return data.strip()
    if isinstance(data, dict):
        if isinstance(data.get("transcript"), str):
            return data["transcript"].strip()
        if isinstance(data.get("text"), str):
            return data["text"].strip()
        results = data.get("results")
        if isinstance(results, list):
            parts: list[str] = []
            for item in results:
                if not isinstance(item, dict):
                    continue
                alternatives = item.get("alternatives") or []
                if alternatives and isinstance(alternatives[0], dict):
                    content = alternatives[0].get("content")
                    if content:
                        parts.append(str(content))
            return " ".join(parts).replace(" ,", ",").replace(" .", ".").strip()
    return ""


def structure_handover(transcript: str) -> dict[str, Any]:
    text = transcript.strip()
    lower = text.lower()
    hazards = [
        name
        for name, tokens in {
            "gas": ("gas", "lel", "co ", "carbon monoxide"),
            "hot-work": ("hot work", "welding", "cutting"),
            "confined-space": ("confined space", "vessel entry", "entry permit"),
            "sensor-health": ("stale", "missing sensor", "stuck"),
        }.items()
        if any(token in lower for token in tokens)
    ]
    zones = sorted(
        {word.strip(".,:;") for word in text.split() if word[:1].isalpha() and "-" in word}
    )
    actions = []
    for marker in ("pause", "evacuate", "inspect", "escalate", "close permit"):
        if marker in lower:
            actions.append(marker)
    summary = text[:240]
    return {"summary": summary, "hazards": hazards, "zones": zones, "actions": actions}


_EXTRACTION_SYSTEM_PROMPT = (
    "Extract structured facts from an industrial shift-handover or near-miss "
    "transcript. Reply with exactly four labeled lines, nothing else:\n"
    "summary: <one sentence>\n"
    "hazards: <comma-separated, from: gas, hot-work, confined-space, "
    "sensor-health, or none>\n"
    "zones: <comma-separated zone ids mentioned, or none>\n"
    "actions: <comma-separated, from: pause, evacuate, inspect, escalate, "
    "close permit, or none>\n"
    "Use only what the transcript actually says. Never invent a zone, hazard, "
    "or action that isn't there."
)


def _parse_extraction_lines(text: str) -> dict[str, Any] | None:
    """Parse the labeled-line format above; None if it doesn't look right."""
    fields: dict[str, str] = {}
    for raw in text.splitlines():
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        key = key.strip().lower()
        if key in {"summary", "hazards", "zones", "actions"}:
            fields[key] = value.strip()
    if "summary" not in fields:
        return None

    def _csv(key: str) -> list[str]:
        raw = fields.get(key, "")
        if not raw or raw.lower() == "none":
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]

    return {
        "summary": fields["summary"],
        "hazards": _csv("hazards"),
        "zones": _csv("zones"),
        "actions": _csv("actions"),
    }


def enrich_structured_with_llm(
    transcript: str, baseline: dict[str, Any], *, provider: LLMProvider | None
) -> dict[str, Any]:
    """Layer an LLM extraction pass on top of the deterministic regex
    ``baseline`` -- never a replacement. Any failure (no provider, degraded,
    or an answer that doesn't parse) returns ``baseline`` unchanged, tagged
    ``source: "regex"``; a well-formed LLM answer is tagged ``source: "llm"``
    so callers can see which path produced it (P3/P4 — the regex path is the
    permanent safety net, never silently dropped)."""
    tagged_baseline = {**baseline, "source": "regex"}
    if provider is None or not transcript.strip():
        return tagged_baseline
    messages = [
        Message(role="system", content=_EXTRACTION_SYSTEM_PROMPT),
        Message(role="user", content=transcript),
    ]
    completion = provider.complete(messages, max_tokens=200)
    if completion.degraded or not completion.text.strip():
        return tagged_baseline
    parsed = _parse_extraction_lines(completion.text)
    if parsed is None:
        return tagged_baseline
    return {**parsed, "source": "llm"}


def transcribe_audio(
    audio: bytes,
    *,
    filename: str = "handover.wav",
    content_type: str = "application/octet-stream",
    provider: LLMProvider | None = None,
    env: dict[str, str] | None = None,
    client: httpx.Client | None = None,
    settings: SpeechmaticsSettings | None = None,
) -> VoiceResult:
    env = env or dict(os.environ)
    settings = settings or SpeechmaticsSettings.from_env(env)
    if reason := settings.missing_reason():
        return _degraded(reason)
    if not audio:
        return _degraded("empty audio upload")

    close_after = False
    http = client
    if http is None:
        http = httpx.Client(
            base_url=settings.base_url,
            headers=_headers(settings),
            timeout=settings.timeout_s,
        )
        close_after = True

    config = {
        "type": "transcription",
        "transcription_config": {
            "language": settings.language,
            "diarization": "speaker",
        },
    }
    try:
        create = http.post(
            "/jobs",
            data={"config": json.dumps(config)},
            files={"data_file": (filename, audio, content_type)},
        )
        create.raise_for_status()
        job_id = _job_id(create.json())
        if not job_id:
            return _degraded("speechmatics response missing job id")

        for _ in range(settings.max_polls):
            detail = http.get(f"/jobs/{job_id}")
            detail.raise_for_status()
            status = _job_status(detail.json())
            if status == "done":
                transcript = http.get(f"/jobs/{job_id}/transcript", params={"format": "json-v2"})
                transcript.raise_for_status()
                text = _transcript_text(transcript.json())
                structured = enrich_structured_with_llm(
                    text, structure_handover(text), provider=provider
                )
                return VoiceResult(
                    transcript=text,
                    structured=structured,
                    degraded=False,
                    job_id=job_id,
                )
            if status in {"rejected", "error", "failed"}:
                return _degraded(f"speechmatics job {job_id} {status}")
            time.sleep(settings.poll_interval_s)
        return _degraded(f"speechmatics job {job_id} did not complete before timeout")
    except Exception as exc:
        return _degraded(f"speechmatics failed: {type(exc).__name__}")
    finally:
        if close_after:
            http.close()
