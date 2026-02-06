"""Shared response helpers."""

from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ToolMeta(BaseModel):
    tool: str
    request_id: str | None = None
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ToolOk(BaseModel):
    ok: bool = True
    meta: ToolMeta
    data: Any


class ToolFail(BaseModel):
    ok: bool = False
    meta: ToolMeta
    error: dict


def ok(tool: str, data: Any, request_id: str | None = None) -> dict:
    return ToolOk(meta=ToolMeta(tool=tool, request_id=request_id), data=data).model_dump(mode="json")


def fail(tool: str, message: str, *, code: str = "TOOL_ERROR", details: dict | None = None, request_id: str | None = None) -> dict:
    return ToolFail(
        meta=ToolMeta(tool=tool, request_id=request_id),
        error={"code": code, "message": message, "details": details or {}},
    ).model_dump(mode="json")
