"""Ticket classifiers: rule-based mock (offline) and OpenAI (structured JSON).

Both implement the same interface so the service layer never branches on
mode. The mock classifier exists for three reasons: zero-cost development,
deterministic tests, and a graceful fallback if the LLM call fails.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .config import Settings
from .taxonomy import TAXONOMY

CATEGORIES = [c for c in TAXONOMY] + ["uncategorized"]


@dataclass
class ClassifyResult:
    category: str
    confidence: float  # 0.0 - 1.0
    rationale: str


def _saturating_confidence(hits: float, k: float) -> float:
    """hits / (hits + k): rises fast, saturates toward 1. One strong keyword
    (~1.0) with k=2.0 gives 0.33 — above the default 0.25 review threshold."""
    if hits <= 0:
        return 0.0
    return round(hits / (hits + k), 4)


class MockClassifier:
    """Weighted keyword scoring. Explainable, deterministic, free."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def classify(self, text: str) -> ClassifyResult:
        lowered = text.lower()
        best_category = "uncategorized"
        best_hits = 0.0
        best_matched: list[str] = []

        for category, spec in TAXONOMY.items():
            hits = 0.0
            matched: list[str] = []
            for keyword, weight in spec["keywords"]:
                # word-boundary match so "error" doesn't fire inside "terror"
                if re.search(r"\b" + re.escape(keyword) + r"\b", lowered):
                    hits += weight
                    matched.append(keyword)
            if hits > best_hits:
                best_hits = hits
                best_category = category
                best_matched = matched

        confidence = _saturating_confidence(best_hits, self.settings.saturation_k)
        if best_hits == 0:
            rationale = "no taxonomy keywords matched"
        else:
            shown = ", ".join(f"'{m}'" for m in best_matched[:4])
            rationale = f"keyword signals {shown} -> {best_category}"
        return ClassifyResult(best_category, confidence, rationale)


def _taxonomy_prompt_block() -> str:
    lines = []
    for name, spec in TAXONOMY.items():
        kws = ", ".join(k for k, _ in spec["keywords"][:6])
        lines.append(f"- {name}: {spec['description']} (e.g. {kws})")
    return "\n".join(lines)


SYSTEM_PROMPT = """You triage customer support tickets. Classify the ticket into exactly one category:

""" + _taxonomy_prompt_block() + """

Reply with JSON ONLY, no other text:
{"category": "<one of the categories above, or 'uncategorized'>",
 "confidence": <0.0 to 1.0>,
 "rationale": "<one short sentence>"}
"""


class OpenAIClassifier:
    """LLM classifier with structured JSON output, validated before use.

    response_format=json_object keeps the model honest; the Pydantic-free
    manual validation below is the last line of defence — anything that
    doesn't parse or names an unknown category degrades to 'uncategorized'
    with 0 confidence instead of raising.
    """

    def __init__(self, settings: Settings) -> None:
        from openai import OpenAI  # local import: mock mode needs no install
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.llm_model

    def classify(self, text: str) -> ClassifyResult:
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text[:4000]},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            category = str(data.get("category", "uncategorized"))
            confidence = float(data.get("confidence", 0.0))
            rationale = str(data.get("rationale", "llm classification"))
        except Exception as exc:  # network, JSON, or schema failure -> safe default
            return ClassifyResult("uncategorized", 0.0, f"classifier error: {exc}")

        if category not in CATEGORIES:
            return ClassifyResult("uncategorized", 0.0,
                                   f"unknown category '{category}' rejected")
        confidence = max(0.0, min(1.0, confidence))
        return ClassifyResult(category, round(confidence, 4), rationale)


def build_classifier(settings: Settings):
    """Factory: OpenAI when a key is configured, mock otherwise."""
    if settings.mode == "openai":
        return OpenAIClassifier(settings)
    return MockClassifier(settings)
