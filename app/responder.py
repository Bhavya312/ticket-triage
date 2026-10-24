"""Suggested first responses: templates in mock mode, LLM-drafted otherwise.

Templates keep mock mode dependency-free and deterministic; in OpenAI mode
the model personalises the reply while staying inside the same tone and
SLA promise. Either way the output is a *draft* — a human agent sends it.
"""

from __future__ import annotations

from .config import Settings
from .taxonomy import SLA_BY_PRIORITY

TEMPLATES = {
    "billing": (
        "Thanks for flagging the billing issue — I've escalated this to our "
        "billing team and we'll follow up {sla}. If you have an invoice number "
        "or receipt handy, replying with it will speed things up."
    ),
    "technical_bug": (
        "Sorry about that — I've logged this as a bug for our engineering team "
        "and we'll update you {sla}. If you can share the exact steps or a "
        "screenshot, it helps us reproduce it faster."
    ),
    "account_access": (
        "Let's get you back in — I've prioritised this and our support team "
        "will reach out {sla}. Meanwhile, please don't share passwords or "
        "2FA codes over email."
    ),
    "outage": (
        "We're aware of the disruption and our engineers are on it right now — "
        "I'll personally update you {sla}. Apologies for the impact."
    ),
    "feature_request": (
        "Thanks for the suggestion — I've added it to our feature backlog for "
        "the product team to review. We'll update you {sla} if it gets "
        "roadmapped."
    ),
    "general_inquiry": (
        "Good question — here's the short answer, and I've linked our docs "
        "below for the details. Anything else, just reply to this thread."
    ),
    "uncategorized": (
        "Thanks for writing in — a support specialist will read your message "
        "and get back to you {sla}."
    ),
}


def _template_reply(category: str, priority: str, name: str | None) -> str:
    greeting = f"Hi {name}, " if name else "Hi, "
    sla = SLA_BY_PRIORITY.get(priority, "soon")
    return greeting + TEMPLATES.get(category, TEMPLATES["uncategorized"]).format(sla=sla)


def draft_reply(
    category: str,
    priority: str,
    subject: str,
    body: str,
    name: str | None,
    settings: Settings,
) -> str:
    """Draft a first response. Deterministic template in mock mode."""
    if settings.mode != "openai":
        return _template_reply(category, priority, name)
    try:
        from openai import OpenAI  # local import: mock mode needs no install
        client = OpenAI(api_key=settings.openai_api_key)
        tone = _template_reply(category, priority, name)
        resp = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system",
                 "content": "You write short, warm customer-support first replies. "
                            "2-3 sentences max. Match the tone and SLA promise of the "
                            "template, personalise it to the ticket, never invent "
                            "facts or timelines beyond the SLA."},
                {"role": "user",
                 "content": f"Template:\n{tone}\n\nTicket subject: {subject}\n"
                            f"Ticket body: {body[:1500]}"},
            ],
            temperature=0.4,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return _template_reply(category, priority, name)  # safe fallback
