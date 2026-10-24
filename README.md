# Ticket Triage API

A support-ticket triage service: send a ticket's subject + body, get back a
**category**, a **priority (P1–P4)**, a **confidence score**, an honest
**needs-review flag** when the classifier isn't sure, and a **draft first
response** for the support agent. Built as a portfolio project for Python +
LLM roles: the whole thing runs **offline in mock mode** (no API keys, no
cost), and switches to a real OpenAI classifier with one environment variable.

```
subject + body ──▶ classify (mock keywords | OpenAI JSON)
                        │
                   confidence < threshold? ──▶ needs_review (best guess kept for routing)
                        │
                   priority = policy(category, severity signals, plan tier)
                        │
                   reply draft (template | LLM-personalised)
```

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# CLI demo (no server needed)
python scripts/demo.py

# labelled eval set
python scripts/eval.py

# API server
uvicorn app.main:app --reload
# interactive docs: http://127.0.0.1:8000/docs
```

## API

```bash
curl -s -X POST http://127.0.0.1:8000/triage \
  -H 'Content-Type: application/json' \
  -d '{"subject": "Locked out of my account",
       "body": "I can'"'"'t sign in and the password reset email never arrives.",
       "tier": "pro"}' | python -m json.tool
```

```json
{
  "category": "account_access",
  "priority": "P1",
  "confidence": 0.68,
  "needs_review": false,
  "rationale": "keyword signals 'locked out', 'can't sign in', 'password reset' -> account_access",
  "suggested_response": "Hi, Let's get you back in — I've prioritised this and our support team will reach out within 1 hour...",
  "mode": "mock"
}
```

| Endpoint       | What it does                                              |
|----------------|-----------------------------------------------------------|
| `GET /`        | service info                                              |
| `GET /health`  | liveness probe                                            |
| `GET /stats`   | mode, category count, sample-ticket count                 |
| `GET /labels`  | the taxonomy: category → description + base priority      |
| `POST /triage` | `{"subject", "body", "tier", "customer_name?"}` → triage  |

## Design: classifier decides *what*, policy decides *how urgent*

Priority is **deterministic policy, not an LLM judgment** — auditable and
consistent:

- Each category has a base priority (`outage` → P1, `feature_request` → P4…).
- Severity signals override: `data loss`, `breach`, `is down` → P1 outright;
  `payment failed`, `charged twice`, `locked out` → one level up.
- Plan tier matters: `enterprise` bumps one level (contractual reality).
- Low-confidence tickets default to P3 with `needs_review: true` — visible,
  not alarming.

## Mock vs OpenAI mode

|                    | Mock (default)                              | OpenAI (`OPENAI_API_KEY` set)              |
|--------------------|---------------------------------------------|--------------------------------------------|
| Classification     | weighted keyword scoring, saturating confidence `hits/(hits+k)` | chat completions, `temperature=0`, `response_format=json_object` |
| First response     | per-category templates with SLA promise     | LLM personalises the template's tone       |
| Cost               | free, offline, deterministic                | ~1 chat call per ticket                    |

The OpenAI path validates everything: unknown categories and unparseable
JSON degrade to `uncategorized` / 0 confidence instead of raising — the
service never 500s because the model got creative.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

Covers keyword scoring, the review-gate threshold, priority policy
(escalations, tier bumps, review default), the safe-degradation path for bad
LLM JSON, the HTTP contract via TestClient, and all 12 labelled fixtures in
`data/tickets.json`.

## Project structure

```
app/
  main.py        FastAPI app (factory pattern — easy to test)
  service.py     TriageService: classify -> review gate -> policy -> reply
  classifier.py  MockClassifier / OpenAIClassifier (same interface)
  policy.py      deterministic priority rules
  responder.py   template + LLM reply drafting
  taxonomy.py    categories, keyword weights, severity signals (plain data)
  schemas.py     Pydantic v2 request/response models
  config.py      env-driven Settings dataclass
data/tickets.json   12 labelled tickets (eval + fixtures)
scripts/demo.py     CLI demo
scripts/eval.py     accuracy report over the labelled set
tests/              pytest suite (offline, mock mode)
```

## Design notes (interview talking points)

- **Why split classification from priority?** Priority is policy: it must be
  explainable ("P1 because: outage + enterprise tier"), stable across
  re-runs, and changeable without re-prompting. LLMs are bad at all three.
- **Why structured JSON output?** Free-text parsing is the #1 source of
  flaky LLM integrations. `response_format=json_object` + validation turns a
  probabilistic output into a typed contract, with a safe default on failure.
- **Why a review gate instead of a refusal?** Unlike the RAG bot (which can
  say "I don't know"), triage must route *something* — so low confidence
  returns the best guess **plus** `needs_review`, keeping the human in the
  loop without dropping the ticket.
- **Why a saturating confidence?** `hits/(hits+k)` rises fast on the first
  strong signal and can't be gamed by keyword stuffing — one more matched
  word barely moves it.
- **Production upgrades:** train a real classifier on labelled tickets,
  calibrate confidence (Platt/isotonic), persist triage decisions for audit,
  add per-category SLA timers and auto-escalation.

## Roadmap

- [x] Project 1 — RAG chatbot (support answers with citations)
- [x] Project 2 — ticket triage API (this repo)
- [x] Project 3 — LLM agent with tools (function calling)
