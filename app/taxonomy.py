"""Triage taxonomy: categories, keyword signals, and priority policy data.

The taxonomy is plain data, not code branching — adding a category means
adding entries here, which is exactly what the OpenAI classifier consumes
when we build its prompt.
"""

from __future__ import annotations

# category -> (description, base priority, [(keyword, weight), ...])
# Weights: 1.0 = near-certain signal, 0.5-0.8 = suggestive.
TAXONOMY: dict[str, dict] = {
    "billing": {
        "description": "Charges, invoices, refunds, subscriptions, payment failures.",
        "base_priority": "P2",
        "keywords": [
            ("charged twice", 1.0), ("double charged", 1.0),
            ("payment failed", 1.0), ("refund", 1.0), ("invoice", 1.0),
            ("receipt", 1.0), ("overcharged", 1.0), ("billing", 0.8),
            ("charged", 0.7), ("subscription", 0.6), ("payment", 0.6),
            ("prorated", 0.6),
        ],
    },
    "technical_bug": {
        "description": "Something broken for one user: errors, crashes, failed actions.",
        "base_priority": "P2",
        "keywords": [
            ("error 500", 1.0), ("crash", 1.0), ("blank screen", 1.0),
            ("broken", 0.7), ("bug", 0.7), ("glitch", 0.7),
            ("timeout", 0.7), ("error", 0.6), ("fails", 0.6),
            ("not working", 0.6),
        ],
    },
    "account_access": {
        "description": "Login, password, 2FA, lockouts, SSO, suspicious access.",
        "base_priority": "P2",
        "keywords": [
            ("locked out", 1.0), ("can't sign in", 1.0),
            ("cannot sign in", 1.0), ("password reset", 1.0),
            ("account locked", 1.0), ("breach", 1.0), ("hacked", 1.0),
            ("2fa", 0.8), ("two-factor", 0.8), ("sso", 0.8), ("saml", 0.8),
            ("suspicious", 0.8), ("locked", 0.7), ("login", 0.6),
            ("sign in", 0.5),
        ],
    },
    "outage": {
        "description": "Service down or degraded for many users at once.",
        "base_priority": "P1",
        "keywords": [
            ("outage", 1.0), ("service unavailable", 1.0),
            ("is down", 1.0), ("site is down", 1.0),
            ("dashboard is down", 1.0), ("all users", 0.8), ("503", 0.8),
            ("whole team", 0.7), ("nobody can", 0.7),
        ],
    },
    "feature_request": {
        "description": "New functionality or improvement the customer wants.",
        "base_priority": "P4",
        "keywords": [
            ("feature request", 1.0), ("please add", 1.0),
            ("dark mode", 1.0), ("would love", 0.7),
            ("it would be great if", 0.7), ("wish list", 0.7),
            ("roadmap", 0.6), ("suggestion", 0.6), ("support for", 0.5),
        ],
    },
    "general_inquiry": {
        "description": "How-to questions, docs, pricing info — nothing broken.",
        "base_priority": "P4",
        "keywords": [
            ("where can i find", 1.0), ("api docs", 1.0),
            ("how do i", 0.8), ("documentation", 0.8),
            ("rate limits", 0.8), ("do you offer", 0.8),
            ("pricing", 0.7), ("question about", 0.6),
        ],
    },
}

# Signals that override the base priority. Critical -> P1 outright;
# high -> one level up. Kept as plain substring lists for the mock path;
# the OpenAI prompt describes the same policy in words.
CRITICAL_SIGNALS = [
    "data loss", "breach", "hacked", "hijacked", "outage",
    "service unavailable", "is down", "all users", "whole team",
    "production down",
]
HIGH_SIGNALS = [
    "payment failed", "charged twice", "double charged", "money deducted",
    "locked out", "can't sign in", "cannot sign in", "deadline",
    "urgent", "asap",
]

PRIORITY_ORDER = ["P1", "P2", "P3", "P4"]

SLA_BY_PRIORITY = {
    "P1": "within 1 hour",
    "P2": "within 4 business hours",
    "P3": "within 1 business day",
    "P4": "within 2 business days",
}
