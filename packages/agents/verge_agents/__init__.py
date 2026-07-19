"""Verge agents — advisory orchestrator + specialists over platform data."""

from .investigator import investigate
from .loop import AgentResult, AgentStep, run_tool_loop
from .orchestrator import orchestrate
from .specialists import (
    COMPLIANCE_TOOLS,
    KNOWLEDGE_TOOLS,
    LESSONS_TOOLS,
    MULTIMODAL_TOOLS,
    RCA_TOOLS,
    TELEMETRY_TOOLS,
    run_all_specialists,
    run_compliance_specialist,
    run_lessons_specialist,
    run_rca_specialist,
)
from .tools import Tool, ToolRegistry
from .twin_catalog import TwinCatalog
from .validator import ValidationReport, extract_candidate_tags, validate_brief

__all__ = [
    "AgentResult",
    "AgentStep",
    "COMPLIANCE_TOOLS",
    "KNOWLEDGE_TOOLS",
    "LESSONS_TOOLS",
    "MULTIMODAL_TOOLS",
    "RCA_TOOLS",
    "TELEMETRY_TOOLS",
    "Tool",
    "ToolRegistry",
    "TwinCatalog",
    "ValidationReport",
    "extract_candidate_tags",
    "investigate",
    "orchestrate",
    "run_all_specialists",
    "run_compliance_specialist",
    "run_lessons_specialist",
    "run_rca_specialist",
    "run_tool_loop",
    "validate_brief",
]
__version__ = "0.5.0"
