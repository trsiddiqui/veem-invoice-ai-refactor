from __future__ import annotations

import httpx
from typing import Any

from veem_invoice_mcp.config import VeemConfig
from veem_invoice_mcp.domain.common.errors import ToolError


class VeemApiClient:
    """Thin HTTP client (adapter) around Veem APIs.

    NOTE: This is intentionally *not* exposed as MCP tools. Workflow tools call these methods internally.
    """

    def __init__(self, cfg: VeemConfig, *, timeout_s: float = 30.0):
        self._cfg = cfg
        self._timeout_s = timeout_s


    @property
    def account_id(self) -> str | None:
        return self._cfg.account_id

    def _require_auth(self) -> tuple[str, str]:
        if not self._cfg.account_id or not self._cfg.access_token:
            raise ToolError(
                "Missing VEEM_ACCOUNT_ID / VEEM_ACCESS_TOKEN.",
                code="MISSING_VEEM_CREDENTIALS",
                details={"required": ["VEEM_ACCOUNT_ID", "VEEM_ACCESS_TOKEN"]},
            )
        return self._cfg.account_id, self._cfg.access_token

    def _headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def request(self, method: str, path: str, *, json_body: dict | None = None, params: dict | None = None) -> dict[str, Any]:
        _account_id, token = self._require_auth()
        url = f"{self._cfg.base_url.rstrip('/')}/{path.lstrip('/')}"  # keep simple
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            resp = await client.request(method, url, headers=self._headers(token), json=json_body, params=params)
        # Handle errors deterministically
        if resp.status_code >= 400:
            try:
                payload = resp.json()
            except Exception:
                payload = {"text": resp.text}
            raise ToolError(
                f"Veem API error {resp.status_code} for {method} {path}",
                code="VEEM_API_ERROR",
                details={"status": resp.status_code, "payload": payload},
            )
        return resp.json()

    # High-level helpers
    async def get_account(self) -> dict[str, Any]:
        account_id, _ = self._require_auth()
        return await self.request("GET", f"account/{account_id}")

    async def list_contacts(self) -> dict[str, Any]:
        return await self.request("GET", "contacts")

    async def list_funding_methods(self) -> dict[str, Any]:
        return await self.request("GET", "funding-methods")

    async def create_payment(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.request("POST", "payments", json_body=payload)
