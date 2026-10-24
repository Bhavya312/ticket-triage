"""FastAPI service exposing the ticket triage API over HTTP.

Endpoints:
    GET  /         service info
    GET  /health   liveness probe
    GET  /stats    mode, category count, sample ticket count
    GET  /labels   the triage taxonomy (category, description, base priority)
    POST /triage   subject + body -> category, priority, reply draft

Run locally:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from .schemas import (
    Category,
    HealthResponse,
    LabelInfo,
    Priority,
    StatsResponse,
    TriageRequest,
    TriageResponse,
)
from .service import TriageService, build_service
from .taxonomy import TAXONOMY

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _sample_ticket_count() -> int:
    path = PROJECT_ROOT / "data" / "tickets.json"
    try:
        return len(json.loads(path.read_text()))
    except (OSError, ValueError):
        return 0


def create_app(service: TriageService | None = None) -> FastAPI:
    """App factory. Pass a service in tests to skip env reads."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.service = service if service is not None else build_service()
        yield

    app = FastAPI(title="Ticket Triage API", version="1.0.0", lifespan=lifespan)

    @app.get("/")
    def root() -> dict:
        return {"name": "ticket-triage", "docs": "/docs", "health": "/health"}

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse()

    @app.get("/stats", response_model=StatsResponse)
    def stats() -> StatsResponse:
        svc: TriageService = app.state.service
        return StatsResponse(
            mode=svc.settings.mode,
            categories=len(TAXONOMY),
            sample_tickets=_sample_ticket_count(),
        )

    @app.get("/labels", response_model=list[LabelInfo])
    def labels() -> list[LabelInfo]:
        return [
            LabelInfo(
                category=Category(name),
                description=spec["description"],
                base_priority=Priority(spec["base_priority"]),
            )
            for name, spec in TAXONOMY.items()
        ]

    @app.post("/triage", response_model=TriageResponse)
    def triage(req: TriageRequest) -> TriageResponse:
        svc: TriageService = app.state.service
        return svc.triage(req)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
