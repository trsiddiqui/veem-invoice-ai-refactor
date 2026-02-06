from __future__ import annotations

import logging
import uuid

from veem_invoice_mcp.domain.common.responses import ok, fail
from veem_invoice_mcp.domain.common.errors import ToolError
from veem_invoice_mcp.domain.invoice.models import InvoiceDocumentInput
from veem_invoice_mcp.runtime import DEPS

logger = logging.getLogger(__name__)


async def invoice_process(file_base64: str, mime_type: str, filename: str, request_id: str | None = None) -> dict:
    """Parse an invoice (PDF/image) into normalized payment fields.

    Returns `processable=false` when the document can't be used to create a payment.
    """
    tool = "invoice_process"
    request_id = request_id or str(uuid.uuid4())
    try:
        doc = InvoiceDocumentInput(filename=filename, mime_type=mime_type, file_base64=file_base64)
        extracted = await DEPS.invoice_extractor.extract(doc)
        return ok(tool, extracted.model_dump(mode="json"), request_id=request_id)
    except ToolError as e:
        return fail(tool, str(e), code=e.code, details=e.details, request_id=request_id)
    except Exception as e:
        logger.exception("Unhandled error in invoice_process")
        return fail(tool, "Unhandled error parsing invoice.", code="UNHANDLED", details={"error": str(e)}, request_id=request_id)
