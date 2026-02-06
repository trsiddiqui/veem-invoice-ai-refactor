from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any


class VeemContact(BaseModel):
    id: str | None = None
    email: str | None = None
    name: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class VeemFundingMethod(BaseModel):
    id: str | None = None
    type: str | None = None
    currency: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
