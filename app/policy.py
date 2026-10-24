"""Priority policy: deterministic rules on top of the classification.

Deliberate design split: the (possibly LLM) classifier decides *what* the
ticket is about; plain code decides *how urgent* it is. Priority is policy —
auditable, consistent, and cheap to change without re-prompting a model.
"""

from __future__ import annotations

from .taxonomy import (
    CRITICAL_SIGNALS,
    HIGH_SIGNALS,
    PRIORITY_ORDER,
    TAXONOMY,
)


def _bump(priority: str, steps: int) -> str:
    idx = PRIORITY_ORDER.index(priority)
    return PRIORITY_ORDER[max(0, min(len(PRIORITY_ORDER) - 1, idx - steps))]


def compute_priority(category: str, text: str, tier: str) -> str:
    """Category base priority, adjusted by severity signals and plan tier."""
    base = TAXONOMY.get(category, {}).get("base_priority", "P3")
    lowered = text.lower()

    if any(sig in lowered for sig in CRITICAL_SIGNALS):
        priority = "P1"
    elif any(sig in lowered for sig in HIGH_SIGNALS):
        priority = _bump(base, 1)
    else:
        priority = base

    # Enterprise customers get one urgency bump — contractual reality.
    if tier == "enterprise":
        priority = _bump(priority, 1)
    return priority


def review_priority() -> str:
    """Tickets flagged for human review default to P3: visible, not alarming."""
    return "P3"
