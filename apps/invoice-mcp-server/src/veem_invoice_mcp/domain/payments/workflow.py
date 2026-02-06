from __future__ import annotations

import re
import uuid
from typing import Any, Optional
import logging

from veem_invoice_mcp.domain.common.errors import ToolError
from veem_invoice_mcp.domain.invoice.models import ExtractedInvoice
from veem_invoice_mcp.domain.payments.models import PaymentDraft, ResolvedPayee, PaymentSubmitResult
from veem_invoice_mcp.runtime import Dependencies

logger = logging.getLogger(__name__)


_AMOUNT_RE = re.compile(r"\$?\s*([0-9]+(?:\.[0-9]{1,2})?)")
_TO_RE = re.compile(r"\bto\b\s+([A-Za-z0-9 .,'"\-]+)", re.IGNORECASE)


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _best_contact_match(contacts_payload: dict[str, Any], *, name: str | None, email: str | None) -> ResolvedPayee:
    # Veem contacts payload can vary; treat as list-ish
    items = contacts_payload.get("contacts") or contacts_payload.get("data") or contacts_payload.get("items") or contacts_payload
    if not isinstance(items, list):
        # fallback: try common key
        items = contacts_payload.get("results") if isinstance(contacts_payload, dict) else []
    candidates: list[dict[str, Any]] = []
    if isinstance(items, list):
        for c in items:
            if isinstance(c, dict):
                candidates.append(c)

    # Exact email match wins
    if email:
        for c in candidates:
            if _normalize(str(c.get("email", ""))) == _normalize(email):
                return ResolvedPayee(
                    contact_id=str(c.get("id") or c.get("contactId") or ""),
                    name=c.get("name") or c.get("displayName"),
                    email=c.get("email"),
                    match_confidence=1.0,
                    candidates=[c],
                )

    # Name fuzzy match
    if name:
        n = _normalize(name)
        scored: list[tuple[float, dict[str, Any]]] = []
        for c in candidates:
            cn = _normalize(str(c.get("name") or c.get("displayName") or ""))
            if not cn:
                continue
            score = 0.0
            if cn == n:
                score = 0.95
            elif n in cn or cn in n:
                score = 0.8
            elif any(tok in cn for tok in n.split()):
                score = 0.6
            if score > 0:
                scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        if scored:
            top_score, top = scored[0]
            top_candidates = [c for _, c in scored[:5]]
            return ResolvedPayee(
                contact_id=str(top.get("id") or top.get("contactId") or ""),
                name=top.get("name") or top.get("displayName"),
                email=top.get("email"),
                match_confidence=float(top_score),
                candidates=top_candidates,
            )

    # No match
    return ResolvedPayee(
        contact_id=None,
        name=name,
        email=email,
        match_confidence=0.0,
        candidates=candidates[:5],
    )


def _pick_funding_method_id(fm_payload: dict[str, Any], preferred_id: str | None) -> str | None:
    items = fm_payload.get("fundingMethods") or fm_payload.get("data") or fm_payload.get("items") or fm_payload
    methods: list[dict[str, Any]] = [m for m in items] if isinstance(items, list) else []
    ids = {str(m.get("id")) for m in methods if isinstance(m, dict) and m.get("id") is not None}

    if preferred_id and preferred_id in ids:
        return preferred_id
    # default to first
    for m in methods:
        if isinstance(m, dict) and m.get("id") is not None:
            return str(m.get("id"))
    return None


def parse_payment_command(command: str) -> dict[str, Any]:
    """Deterministic parsing for simple commands like: 'Pay $50 to Sam for lunch'."""
    amt = None
    m = _AMOUNT_RE.search(command)
    if m:
        amt = float(m.group(1))

    payee_name = None
    m2 = _TO_RE.search(command)
    if m2:
        payee_name = m2.group(1).strip().strip("\"'")

    # crude purpose: anything after 'for'
    purpose = None
    if " for " in command.lower():
        purpose = command.split(" for ", 1)[1].strip()

    return {"amount": amt, "payee_name": payee_name, "purpose": purpose}


async def prepare_payment(
    deps: Dependencies,
    *,
    command: str | None = None,
    invoice: ExtractedInvoice | None = None,
    currency_hint: str | None = None,
) -> PaymentDraft:
    if not command and not invoice:
        raise ToolError("Provide either 'command' or 'invoice'.", code="BAD_REQUEST")

    draft_id = str(uuid.uuid4())
    idem_key = str(uuid.uuid4())

    assumptions: list[str] = []
    missing: list[str] = []

    # --- Extract core fields
    payee_name: str | None = None
    payee_email: str | None = None
    amount: float | None = None
    currency: str | None = None
    purpose: str | None = None

    if invoice:
        if not invoice.processable:
            raise ToolError("Invoice is not processable.", code="UNPROCESSABLE_DOCUMENT", details={"reason": invoice.reason})
        payee_name = invoice.payee.name
        payee_email = invoice.payee.email
        amount = invoice.money.amount
        currency = invoice.money.currency
        purpose = invoice.purpose
    if command:
        parsed = parse_payment_command(command)
        amount = amount or parsed.get("amount")
        payee_name = payee_name or parsed.get("payee_name")
        purpose = purpose or parsed.get("purpose")

    if currency_hint and not currency:
        currency = currency_hint
        assumptions.append(f"Used currency hint '{currency_hint}'.")

    if not amount:
        missing.append("amount")
    if not (payee_name or payee_email):
        missing.append("payee")

    # Currency defaulting
    if not currency:
        currency = "USD"
        assumptions.append("Defaulted currency to USD.")

    # --- Resolve Veem entities
    contacts = await deps.veem.list_contacts()
    resolved = _best_contact_match(contacts, name=payee_name, email=payee_email)

    if resolved.match_confidence < 0.8:
        assumptions.append("Payee match is uncertain; please confirm.")

    funding_methods = await deps.veem.list_funding_methods()

    preferred_fm = None
    if resolved.email:
        preferred_fm = await deps.history_store.last_funding_method_id_for_payee(resolved.email)
        if preferred_fm:
            assumptions.append("Inferred funding method from past payments.")
    fm_id = _pick_funding_method_id(funding_methods, preferred_fm)
    if not fm_id:
        missing.append("funding_method_id")

    if not purpose:
        purpose = "Invoice payment"
        assumptions.append("Defaulted purpose to 'Invoice payment'.")

    payload = {
        "accountId": deps.veem.account_id,  # POC: uses private field; in prod expose getter
        "recipient": {"email": resolved.email or payee_email, "name": resolved.name or payee_name},
        "amount": {"number": amount, "currency": currency},
        "purpose": purpose,
        "fundingMethod": {"id": fm_id},
        "description": "Payment created by Invoice AI (POC)",
        "idempotencyKey": idem_key,
    }

    needs_confirmation = bool(assumptions or missing or resolved.match_confidence < 0.95)

    return PaymentDraft(
        draft_id=draft_id,
        idempotency_key=idem_key,
        payee=resolved,
        amount=amount,
        currency=currency,
        purpose=purpose,
        funding_method_id=fm_id,
        needs_confirmation=needs_confirmation,
        assumptions=assumptions,
        missing_fields=missing,
        proposed_payment_payload=payload,
    )


async def submit_payment(deps: Dependencies, draft: PaymentDraft) -> PaymentSubmitResult:
    # Gate: ensure required fields are present
    required = []
    if not draft.amount:
        required.append("amount")
    if not draft.currency:
        required.append("currency")
    if not (draft.payee.email or draft.payee.name):
        required.append("payee")
    if not draft.funding_method_id:
        required.append("funding_method_id")

    if required:
        raise ToolError("Draft missing required fields.", code="MISSING_FIELDS", details={"missing": required})

    payload = dict(draft.proposed_payment_payload)
    payload["amount"] = {"number": draft.amount, "currency": draft.currency}
    payload["fundingMethod"] = {"id": draft.funding_method_id}
    payload["purpose"] = draft.purpose or payload.get("purpose")
    payload["recipient"] = {
        "email": draft.payee.email,
        "name": draft.payee.name,
        "contactId": draft.payee.contact_id,
    }

    raw = await deps.veem.create_payment(payload)
    payment_id = str(raw.get("id") or raw.get("paymentId") or "").strip() or None
    status = raw.get("status") or raw.get("state")

    return PaymentSubmitResult(payment_id=payment_id, status=status, raw=raw)
