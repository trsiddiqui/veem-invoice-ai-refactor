from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Any, List


class PayeeHint(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


class Money(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None  # ISO 4217 (e.g. USD)


class ExtractedInvoice(BaseModel):
    processable: bool = True
    reason: Optional[str] = None

    payee: PayeeHint = Field(default_factory=PayeeHint)
    money: Money = Field(default_factory=Money)

    purpose: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None  # ISO date string if available
    due_date: Optional[str] = None      # ISO date string if available

    confidence: dict[str, float] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)

    raw: dict[str, Any] = Field(default_factory=dict)


class InvoiceDocumentInput(BaseModel):
    filename: str
    mime_type: str
    file_base64: str
