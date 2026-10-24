"""Eval harness: run the mock classifier over data/tickets.json and report.

A tiny labelled set is the cheapest honest check that the taxonomy and
thresholds do what the README claims. Run: python scripts/eval.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas import TriageRequest
from app.service import build_service

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    tickets = json.loads((ROOT / "data" / "tickets.json").read_text())
    svc = build_service()
    assert svc.settings.mode == "mock", "eval runs against the mock classifier"

    correct = 0
    for t in tickets:
        req = TriageRequest(subject=t["subject"], body=t["body"], tier=t["tier"])
        res = svc.triage(req)
        ok_cat = res.category.value == t["expected_category"]
        ok_pri = res.priority.value == t["expected_priority"]
        ok_rev = res.needs_review == t.get("expected_needs_review", False)
        ok = ok_cat and ok_pri and ok_rev
        correct += ok
        mark = "OK " if ok else "FAIL"
        print(f"[{mark}] {t['subject'][:45]:45} -> {res.category.value:16} "
              f"{res.priority.value} review={res.needs_review} (conf {res.confidence})")

    total = len(tickets)
    print(f"\naccuracy: {correct}/{total}")
    return 0 if correct == total else 1


if __name__ == "__main__":
    sys.exit(main())
