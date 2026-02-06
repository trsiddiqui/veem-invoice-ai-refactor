from __future__ import annotations

import logging
import uuid

from veem_invoice_mcp.domain.common.responses import ok, fail
from veem_invoice_mcp.domain.common.errors import ToolError
from veem_invoice_mcp.domain.invoice.models import ExtractedInvoice
from veem_invoice_mcp.domain.payments.models import PaymentDraft
from veem_invoice_mcp.domain.payments.workflow import prepare_payment as _prepare_payment, submit_payment as _submit_payment
from veem_invoice_mcp.runtime import DEPS

logger = logging.getLogger(__name__)


async def payment_prepare(
    command: str | None = None,
    invoice: dict | None = None,
    currency_hint: str | None = None,
    request_id: str | None = None,
) -> dict:
    """Infer entities and create a PaymentDraft suitable for Review & Confirm."""
    tool = "payment_prepare"
    request_id = request_id or str(uuid.uuid4())
    try:
        invoice_model = ExtractedInvoice.model_validate(invoice) if invoice else None
        draft = await _prepare_payment(DEPS, command=command, invoice=invoice_model, currency_hint=currency_hint)
        return ok(tool, draft.model_dump(mode="json"), request_id=request_id)
    except ToolError as e:
        return fail(tool, str(e), code=e.code, details=e.details, request_id=request_id)
    except Exception as e:
        logger.exception("Unhandled error in payment_prepare")
        return fail(tool, "Unhandled error preparing payment.", code="UNHANDLED", details={"error": str(e)}, request_id=request_id)


async def payment_submit(draft: dict, request_id: str | None = None) -> dict:
    """Submit a prepared draft to Veem."""
    tool = "payment_submit"
    request_id = request_id or str(uuid.uuid4())
    try:
        draft_model = PaymentDraft.model_validate(draft)
        result = await _submit_payment(DEPS, draft_model)
        return ok(tool, result.model_dump(mode="json"), request_id=request_id)
    except ToolError as e:
        return fail(tool, str(e), code=e.code, details=e.details, request_id=request_id)
    except Exception as e:
        logger.exception("Unhandled error in payment_submit")
        return fail(tool, "Unhandled error submitting payment.", code="UNHANDLED", details={"error": str(e)}, request_id=request_id)


async def payment_schedule(draft: dict, run_at_utc: str, request_id: str | None = None) -> dict:
    """Schedule a payment (POC).

    In production, swap to an agent-optimized scheduling API.
    """
    tool = "payment_schedule"
    request_id = request_id or str(uuid.uuid4())
    try:
        draft_model = PaymentDraft.model_validate(draft)
        payload = draft_model.model_dump(mode="json")
        scheduled = await DEPS.schedule_store.create(draft=payload, run_at_utc=run_at_utc)
        return ok(tool, scheduled, request_id=request_id)
    except ToolError as e:
        return fail(tool, str(e), code=e.code, details=e.details, request_id=request_id)
    except Exception as e:
        logger.exception("Unhandled error in payment_schedule")
        return fail(tool, "Unhandled error scheduling payment.", code="UNHANDLED", details={"error": str(e)}, request_id=request_id)
