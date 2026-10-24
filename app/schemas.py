"""Pydantic v2 request/response models for the triage API."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Category(str, Enum):
    BILLING = "billing"
    TECHNICAL_BUG = "technical_bug"
    ACCOUNT_ACCESS = "account_access"
    OUTAGE = "outage"
    FEATURE_REQUEST = "feature_request"
    GENERAL_INQUIRY = "general_inquiry"
    UNCATEGORIZED = "uncategorized"


class Priority(str, Enum):
    P1 = "P1"  # urgent: outage, security, money movement
    P2 = "P2"  # high: broken functionality, access blocked
    P3 = "P3"  # normal: default, or needs human review
    P4 = "P4"  # low: feature requests, general questions


Tier = Literal["free", "pro", "enterprise"]


class TriageRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1, max_length=5000)
    tier: Tier = "free"
    customer_name: str | None = Field(default=None, max_length=100)


class TriageResponse(BaseModel):
    category: Category
    priority: Priority
    confidence: float = Field(ge=0.0, le=1.0)
    needs_review: bool
    rationale: str
    suggested_response: str
    mode: str


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class StatsResponse(BaseModel):
    mode: str
    categories: int
    sample_tickets: int


class LabelInfo(BaseModel):
    category: Category
    description: str
    base_priority: Priority
