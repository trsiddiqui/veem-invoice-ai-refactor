from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Optional, List


class ResolvedPayee(BaseModel):
    contact_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    match_confidence: float = 0.0
    candidates: List[dict[str, Any]] = Field(default_factory=list)


class PaymentDraft(BaseModel):
    draft_id: str
    idempotency_key: str

    payee: ResolvedPayee = Field(default_factory=ResolvedPayee)
    amount: Optional[float] = None
    currency: Optional[str] = None
    purpose: Optional[str] = None
    funding_method_id: Optional[str] = None

    needs_confirmation: bool = True
    assumptions: List[str] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)

    # Raw payload that would be sent to Veem API on submit (for Review & Confirm)
    proposed_payment_payload: dict[str, Any] = Field(default_factory=dict)


class PaymentSubmitResult(BaseModel):
    payment_id: Optional[str] = None
    status: Optional[str] = None
    raw: dict[str, Any] = Field(default_factory=dict)


class PaymentScheduleResult(BaseModel):
    schedule_id: str
    status: str
    run_at_utc: str
