"""Pytest suite (offline, mock mode): classifier, policy, and HTTP contract."""

from __future__ import annotations

import json
import sys

import pytest
from fastapi.testclient import TestClient

from app import policy
from app.classifier import MockClassifier, OpenAIClassifier
from app.config import Settings
from app.main import create_app
from app.schemas import TriageRequest
from app.service import TriageService


@pytest.fixture()
def settings() -> Settings:
    return Settings()  # no API key -> mock mode


@pytest.fixture()
def service(settings: Settings) -> TriageService:
    return TriageService(settings)


@pytest.fixture()
def client(service: TriageService):
    # entering the context runs the lifespan, which wires app.state.service
    with TestClient(create_app(service)) as c:
        yield c


# --- classifier -----------------------------------------------------------

def test_billing_ticket_classified(settings: Settings):
    c = MockClassifier(settings)
    r = c.classify("I was charged twice, please refund the duplicate charge")
    assert r.category == "billing"
    assert r.confidence >= settings.confidence_threshold


def test_outage_ticket_classified(settings: Settings):
    c = MockClassifier(settings)
    r = c.classify("The site is down, service unavailable for all users")
    assert r.category == "outage"


def test_vague_ticket_gets_zero_confidence(settings: Settings):
    c = MockClassifier(settings)
    r = c.classify("It is not working.")
    # weak signal only -> below the review threshold
    assert r.confidence < settings.confidence_threshold


def test_empty_signal_ticket_is_uncategorized(settings: Settings):
    c = MockClassifier(settings)
    r = c.classify("asdf qwerty zxcv")
    assert r.category == "uncategorized"
    assert r.confidence == 0.0


def test_openai_classifier_rejects_unknown_category(monkeypatch):
    """A fake client returning a bad category must degrade safely."""

    class FakeCompletions:
        @staticmethod
        def create(**kwargs):
            class Message:
                content = '{"category": "teleportation", "confidence": 0.99, "rationale": "x"}'
            class Choice:
                message = Message()
            class Resp:
                choices = [Choice()]
            return Resp()

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAI:
        def __init__(self, api_key=None):
            self.chat = FakeChat()

    import types
    fake_mod = types.ModuleType("openai")
    fake_mod.OpenAI = FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", fake_mod)

    clf = OpenAIClassifier(Settings(openai_api_key="test"))
    r = clf.classify("my bill is wrong")
    assert r.category == "uncategorized"
    assert r.confidence == 0.0


# --- priority policy ------------------------------------------------------

def test_outage_is_p1():
    assert policy.compute_priority("outage", "dashboard is down", "free") == "P1"


def test_double_charge_bumps_billing_to_p1():
    assert policy.compute_priority("billing", "I was charged twice", "pro") == "P1"


def test_plain_billing_stays_p2():
    assert policy.compute_priority("billing", "send me my invoice", "free") == "P2"


def test_enterprise_feature_request_bumped():
    assert policy.compute_priority("feature_request", "please add SSO", "enterprise") == "P3"


def test_free_feature_request_stays_p4():
    assert policy.compute_priority("feature_request", "please add dark mode", "free") == "P4"


def test_security_breach_is_p1():
    assert policy.compute_priority("account_access", "possible security breach", "pro") == "P1"


def test_review_defaults_to_p3():
    assert policy.review_priority() == "P3"


# --- service: the review gate ---------------------------------------------

def test_low_confidence_ticket_needs_review(service: TriageService):
    res = service.triage(TriageRequest(subject="Help please", body="It is not working."))
    assert res.needs_review is True
    assert res.priority.value == "P3"
    assert res.mode == "mock"


def test_confident_ticket_not_flagged(service: TriageService):
    res = service.triage(TriageRequest(
        subject="Export fails with error 500",
        body="Every CSV export ends in error 500.",
        tier="pro",
    ))
    assert res.needs_review is False
    assert res.category.value == "technical_bug"
    assert res.priority.value == "P2"
    assert res.suggested_response  # a draft is always produced


# --- HTTP contract --------------------------------------------------------

def test_health(client: TestClient):
    assert client.get("/health").json() == {"status": "ok"}


def test_labels_lists_taxonomy(client: TestClient):
    labels = client.get("/labels").json()
    names = {l["category"] for l in labels}
    assert {"billing", "outage", "feature_request"} <= names
    by_name = {l["category"]: l for l in labels}
    assert by_name["outage"]["base_priority"] == "P1"


def test_triage_endpoint(client: TestClient):
    r = client.post("/triage", json={
        "subject": "Locked out of my account",
        "body": "I can't sign in, the password reset email never arrives.",
        "tier": "pro",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["category"] == "account_access"
    assert data["priority"] == "P1"
    assert data["mode"] == "mock"


def test_triage_rejects_empty_body(client: TestClient):
    r = client.post("/triage", json={"subject": "x", "body": ""})
    assert r.status_code == 422


# --- eval fixtures --------------------------------------------------------

def test_eval_fixtures_all_pass(service: TriageService):
    """The labelled set in data/tickets.json must triage as expected."""
    from pathlib import Path
    path = Path(__file__).resolve().parent.parent / "data" / "tickets.json"
    tickets = json.loads(path.read_text())
    assert len(tickets) >= 10
    for t in tickets:
        res = service.triage(TriageRequest(
            subject=t["subject"], body=t["body"], tier=t["tier"]))
        assert res.category.value == t["expected_category"], t["subject"]
        assert res.priority.value == t["expected_priority"], t["subject"]
        assert res.needs_review == t.get("expected_needs_review", False), t["subject"]
