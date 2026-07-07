"""Human-readable compliance report (for the safety officer + the regulator)."""

from __future__ import annotations

from .evidence import CompliancePack
from .gaps import ComplianceReport

_ICON = {"satisfied": "✅", "gap": "❌"}


def render_markdown(report: ComplianceReport, pack: CompliancePack | None = None) -> str:
    lines = [
        f"# Compliance report — {report.plant}",
        "",
        "> OISD / Factory Act / DGMS gap assessment (spec §5). Deterministic and "
        "LLM-free — a gap is a legal claim, reproduced not generated.",
        "",
        f"**Coverage: {report.coverage_ratio:.0%}** "
        f"({report.satisfied}/{len(report.results)} clauses satisfied, "
        f"{len(report.gaps)} gaps)",
        "",
        "| Clause | Standard | Requirement | Status |",
        "|--------|----------|-------------|--------|",
    ]
    for r in report.results:
        icon = _ICON.get(r.status, r.status)
        req = r.clause.requirement
        lines.append(f"| {r.clause.id} | {r.clause.standard} | {req} | {icon} {r.reason} |")
    if report.gaps:
        lines += ["", "## Gaps to close before go-live", ""]
        for r in report.gaps:
            lines.append(f"- **{r.clause.id}** ({r.clause.standard}) — {r.clause.requirement}")
    if pack is not None:
        lines += [
            "",
            "## Evidence pack",
            "",
            f"- Pack: `{pack.pack_id}`",
            f"- Manifest hash: `{pack.hash}`",
            f"- Audit head at assessment: `{pack.audit_head}`",
            f"- Supporting findings: {len(pack.finding_ids)}",
            "",
            "_The manifest hash covers the assessment content, supporting finding "
            "ids, and audit head — reproducible and tamper-evident (P6)._",
        ]
    lines.append("")
    return "\n".join(lines)
