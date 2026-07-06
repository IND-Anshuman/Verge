"""Multilingual alert preview with deterministic fallback."""

from __future__ import annotations

from typing import Any

from verge_llm import LLMProvider, Message, NullProvider
from verge_schema.findings import RiskFinding


def _template(finding: RiskFinding) -> dict[str, str]:
    zone = finding.zone_id
    hazard = finding.title
    band = finding.lead_time_band
    action = "Pause affected work, verify source readings, and escalate to the shift lead."
    return {
        "en": f"{band} risk in {zone}: {hazard}. {action}",
        "hi": (
            f"{zone} mein {band} risk: {hazard}. Kaam rokein, readings verify karein, "
            "aur shift lead ko escalate karein."
        ),
    }


def alert_preview(
    finding: RiskFinding,
    *,
    provider: LLMProvider | None = None,
) -> dict[str, Any]:
    provider = provider or NullProvider()
    fallback = _template(finding)
    prompt = [
        Message(
            role="system",
            content=(
                "Draft concise industrial safety alert text in English and Hindi. "
                "Return exactly two lines: en: ... and hi: ..."
            ),
        ),
        Message(
            role="user",
            content=(
                f"Finding {finding.finding_id}, zone {finding.zone_id}, title {finding.title}, "
                f"lead-time band {finding.lead_time_band}, confidence {finding.confidence}."
            ),
        ),
    ]
    completion = provider.complete(prompt, max_tokens=180)
    if completion.degraded or not completion.text.strip():
        return {"languages": fallback, "degraded": True, "reason": completion.reason}

    languages = dict(fallback)
    for raw in completion.text.splitlines():
        line = raw.strip()
        if line.lower().startswith("en:"):
            languages["en"] = line[3:].strip()
        elif line.lower().startswith("hi:"):
            languages["hi"] = line[3:].strip()
    return {"languages": languages, "degraded": False}
