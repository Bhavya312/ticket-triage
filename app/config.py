"""Runtime configuration.

Every knob comes from the environment so the same code runs locally,
in tests, and in production without edits. Copy `.env.example` to `.env`
for local development. With nothing set, the service runs fully offline
in mock mode (rule-based classifier, template replies).
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    """All tunables. Frozen so startup config can't drift."""

    openai_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    confidence_threshold: float = 0.25  # below this -> needs_review
    saturation_k: float = 2.0  # confidence = hits / (hits + k)

    @property
    def mode(self) -> str:
        """'openai' when a key is configured, otherwise free offline 'mock'."""
        return "openai" if self.openai_api_key else "mock"


def load_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        confidence_threshold=_get_float("CONFIDENCE_THRESHOLD", 0.25),
        saturation_k=_get_float("SATURATION_K", 2.0),
    )
