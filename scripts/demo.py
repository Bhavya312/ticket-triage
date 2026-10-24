"""CLI demo: triage a ticket without starting the server."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas import TriageRequest
from app.service import build_service

SAMPLES = [
    TriageRequest(
        subject="Charged twice this month",
        body="I was charged twice for my Pro subscription. Please refund the duplicate.",
        tier="pro",
        customer_name="Priya",
    ),
    TriageRequest(
        subject="Dashboard is down for our whole team",
        body="Nobody can load the dashboard since 9am, it shows service unavailable.",
        tier="enterprise",
    ),
    TriageRequest(
        subject="Help please",
        body="It is not working.",
        tier="free",
    ),
]


def main() -> None:
    svc = build_service()
    print(f"mode: {svc.settings.mode}\n")
    for req in SAMPLES:
        res = svc.triage(req)
        print(f"> {req.subject}")
        print(f"  category={res.category.value}  priority={res.priority.value}  "
              f"confidence={res.confidence}  needs_review={res.needs_review}")
        print(f"  rationale: {res.rationale}")
        print(f"  reply: {res.suggested_response}\n")


if __name__ == "__main__":
    main()
