"""Multi-channel, multilingual alert drafting (spec §4.4).

Deterministic templates are the floor — they work with no LLM and no network
(P1). An LLMProvider, if configured, may *refine* the phrasing, but the alert is
always producible from the template alone. Alerts are drafted, then fired by a
human on Approve (P8); nothing here writes to a PA/SMS/IVR system itself.
"""

from __future__ import annotations

from datetime import datetime

from verge_schema.findings import RiskFinding

# Short, operationally-plain templates. {zone} and {action} are filled per finding.
TEMPLATES: dict[str, str] = {
    "en": "SAFETY ALERT — zone {zone}: {title}. Recommended: {action}. Lead-time band {band}.",
    "hi": "सुरक्षा चेतावनी — क्षेत्र {zone}: {title}। अनुशंसा: {action}। समय-सीमा {band}।",
    "te": "భద్రతా హెచ్చరిక — జోన్ {zone}: {title}. సిఫార్సు: {action}. లీడ్-టైమ్ {band}.",
}

DEFAULT_LANGS = ["en", "hi", "te"]
DEFAULT_CHANNELS = ["console", "app", "sms", "ivr", "pa"]


def draft_messages(
    finding: RiskFinding, action: str, languages: list[str] | None = None
) -> dict[str, str]:
    langs = languages or DEFAULT_LANGS
    out: dict[str, str] = {}
    for lang in langs:
        tmpl = TEMPLATES.get(lang, TEMPLATES["en"])
        out[lang] = tmpl.format(
            zone=finding.zone_id, title=finding.title, action=action,
            band=finding.lead_time_band,
        )
    return out


def draft_alert(
    finding: RiskFinding,
    action: str,
    *,
    issued_at: datetime,
    channels: list[str] | None = None,
    languages: list[str] | None = None,
):
    """Return a verge_schema.Alert with a multilingual body. Drafted, not sent."""
    from verge_schema.audit import Alert  # local import keeps schema import surface tight

    msgs = draft_messages(finding, action, languages)
    body = "\n".join(f"[{lang}] {text}" for lang, text in msgs.items())
    return Alert(
        alert_id=f"AL-{finding.finding_id}",
        finding_id=finding.finding_id,
        channels=channels or DEFAULT_CHANNELS,
        languages=list(msgs.keys()),
        body=body,
        issued_at=issued_at,
    )
