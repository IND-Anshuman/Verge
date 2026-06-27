"""Preliminary incident report drafting (spec §4.4).

The report is drafted from the source-linked evidence pack and is ALWAYS marked
operator-review-required, never auto-submitted (P8). An LLMProvider may write the
narrative; if it is degraded/absent, a deterministic template carries the same
facts. Either way the report cites every contributing signal (P3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from verge_llm import LLMProvider, Message, NullProvider
from verge_schema.audit import EvidencePack
from verge_schema.findings import RiskFinding


@dataclass
class ReportDraft:
    markdown: str
    cited: list[str] = field(default_factory=list)
    submitted: bool = False  # P8: never auto-submitted
    narrative_degraded: bool = False


_HEADER = "# PRELIMINARY INCIDENT REPORT — operator review required, NOT submitted"


def _facts_block(finding: RiskFinding, pack: EvidencePack, at: datetime) -> str:
    signals = "\n".join(
        f"- {s.kind}:{s.ref_id} — {s.summary}" for s in finding.contributing_signals
    ) or "- (none recorded)"
    return (
        f"**Finding** {finding.finding_id} · zone {finding.zone_id} · "
        f"band {finding.lead_time_band} · confidence {finding.confidence:.2f}\n\n"
        f"**Title** {finding.title}\n\n"
        f"**Contributing signals (lineage)**\n{signals}\n\n"
        f"**Evidence pack** {pack.pack_id} · manifest {pack.manifest_hash[:12]}…\n\n"
        f"**Drafted at** {at.isoformat()}"
    )


def draft_incident_report(
    finding: RiskFinding,
    pack: EvidencePack,
    *,
    at: datetime,
    provider: LLMProvider | None = None,
) -> ReportDraft:
    provider = provider or NullProvider()
    facts = _facts_block(finding, pack, at)
    cited = [f"{s.kind}:{s.ref_id}" for s in finding.contributing_signals] or list(finding.lineage)

    prompt = [
        Message(role="system", content="You draft factual, regulator-ready preliminary "
                "incident reports. Use only the facts provided. Do not speculate."),
        Message(role="user", content=f"Draft a 4-6 sentence preliminary summary from:\n{facts}"),
    ]
    completion = provider.complete(prompt, max_tokens=400)

    if completion.degraded or not completion.text.strip():
        narrative = (
            "Automated preliminary summary (template fallback — LLM narrative "
            "unavailable). The facts below are authoritative; a human must review "
            "and complete this report before any submission."
        )
        degraded = True
    else:
        narrative = completion.text.strip()
        degraded = False

    markdown = f"{_HEADER}\n\n{narrative}\n\n---\n\n{facts}\n"
    return ReportDraft(markdown=markdown, cited=cited, submitted=False, narrative_degraded=degraded)
