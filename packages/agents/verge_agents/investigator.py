"""Finding investigation entrypoint (advisory plane).

Phase 2.5: ``investigate`` delegates to the advisory orchestrator
(specialists → merge → validate). Kept as the stable public API so routes
and tests keep working. Read-only; degrades to a specialist fact sheet (P4/P8).
"""

from __future__ import annotations

from verge_llm import LLMProvider

from .orchestrator import orchestrate
from .tools import ToolRegistry
from .twin_catalog import TwinCatalog


def investigate(
    provider: LLMProvider,
    *,
    finding_id: str,
    zone_id: str,
    title: str,
    tools: ToolRegistry,
    model: str | None = None,
    max_steps: int = 6,  # retained for API compat; orchestrator does not loop
    catalog: TwinCatalog | None = None,
) -> dict:
    """Run the investigation; always returns a wire-shaped brief."""
    _ = max_steps
    return orchestrate(
        provider,
        finding_id=finding_id,
        zone_id=zone_id,
        title=title,
        tools=tools,
        catalog=catalog,
        model=model,
    )
