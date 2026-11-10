from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowDecision(StrEnum):
    CONFIRMED = "confirmed"
    PRODUCTION_REQUIRED = "production_required"
    PROCUREMENT_REQUIRED = "procurement_required"
    MANUAL_REVIEW = "manual_review"


class EventLevel(StrEnum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class OrderRequest(BaseModel):
    customer_id: str = Field(min_length=1, max_length=30)
    product_id: str = Field(min_length=1, max_length=30)
    quantity: int = Field(gt=0, le=10_000)
    requested_date: date


class WorkflowEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    step: int = Field(ge=1)
    agent: str
    action: str
    message: str
    level: EventLevel = EventLevel.INFO
    details: dict[str, Any] = Field(default_factory=dict)


class WorkflowResult(BaseModel):
    order: OrderRequest
    decision: WorkflowDecision
    explanation: str
    customer: dict[str, Any]
    stock: dict[str, Any]
    capacity: dict[str, Any] | None = None
    procurement: dict[str, Any] | None = None
    price: dict[str, Any]
    delivery: dict[str, Any]
    events: list[WorkflowEvent]
    processing_seconds: float = Field(ge=0)
    metagpt_used: bool = False
    metagpt_summary: str | None = None
    metagpt_messages: dict[str, str] = Field(default_factory=dict)

