# Push to GitHub — Ticket Triage API (Project 2 of 3)

Prepared 2026-10-12. The scaffold is complete: FastAPI app, mock + OpenAI
classifiers, deterministic priority policy, tests (19 passed, re-verified
2026-10-12), README with quickstart, API table and design notes.
`.gitignore` already excludes `.env`, `.venv/`, `__pycache__/`,
`.pytest_cache/`. It is NOT a git repo yet — nothing has been pushed anywhere.

This is project 2 of the 3-project set from the Python refresher plan:
1. `rag-chatbot` — ready, push guide in its folder
2. `ticket-triage` — this repo
3. `llm-agent` — ready, push guide in its folder

## Suggested repo settings
- **Name:** `ticket-triage`
- **Description:** Support-ticket triage API — category, priority (P1–P4), saturating confidence and a review gate; classification is LLM/mock, priority is deterministic policy. FastAPI, runs offline in mock mode, switches to OpenAI with one env var.
- **Topics:** `fastapi`, `llm`, `ticket-triage`, `classification`, `python`, `openai`, `portfolio`
- **Visibility:** Public (portfolio piece)

## Commands (run inside this folder)
```bash
git init -b main
git add .
git commit -m "Ticket triage API: mock/OpenAI classification, deterministic priority policy, review gate"
git remote add origin https://github.com/Bhavya312/ticket-triage.git
git push -u origin main
```
(Create the empty repo on github.com first — no README/license, those are already here or can be added after.)

GitHub profile: https://github.com/Bhavya312

## After the push
- Pin all three projects on your GitHub profile.
- Once 1–2 projects are live, the paused Python/AI role applications can restart (paused 2026-09-26 until GitHub projects exist).
