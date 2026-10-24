"""Triage service: classifier -> review gate -> priority policy -> reply draft.

The review gate is the honesty mechanism (same idea as the RAG bot's
"I don't know"): when confidence is below threshold we still return our
best guess for routing, but flag needs_review so a human looks first.
"""

from __future__ import annotations

from . import policy
from .classifier import build_classifier
from .config import Settings, load_settings
from .responder import draft_reply
from .schemas import Priority, TriageRequest, TriageResponse


class TriageService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        self.classifier = build_classifier(self.settings)

    def triage(self, req: TriageRequest) -> TriageResponse:
        text = f"{req.subject}\n{req.body}"
        result = self.classifier.classify(text)

        needs_review = (
            result.confidence < self.settings.confidence_threshold
            or result.category == "uncategorized"
        )
        priority = (
            policy.review_priority()
            if needs_review
            else policy.compute_priority(result.category, text, req.tier)
        )
        reply = draft_reply(
            result.category, priority, req.subject, req.body,
            req.customer_name, self.settings,
        )
        return TriageResponse(
            category=result.category,  # type: ignore[arg-type]
            priority=priority,  # type: ignore[arg-type]
            confidence=result.confidence,
            needs_review=needs_review,
            rationale=result.rationale,
            suggested_response=reply,
            mode=self.settings.mode,
        )


def build_service(settings: Settings | None = None) -> TriageService:
    return TriageService(settings)
