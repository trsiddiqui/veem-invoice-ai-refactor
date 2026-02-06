from __future__ import annotations

import base64
import json
import logging
from typing import Protocol

from pydantic import ValidationError
from veem_invoice_mcp.config import OpenAIConfig
from veem_invoice_mcp.domain.common.errors import ToolError
from veem_invoice_mcp.domain.invoice.models import InvoiceDocumentInput, ExtractedInvoice

logger = logging.getLogger(__name__)


class InvoiceExtractor(Protocol):
    async def extract(self, doc: InvoiceDocumentInput) -> ExtractedInvoice:
        ...


class NullInvoiceExtractor:
    async def extract(self, doc: InvoiceDocumentInput) -> ExtractedInvoice:
        raise ToolError(
            "OPENAI_API_KEY not configured; cannot parse invoices.",
            code="MISSING_OPENAI_API_KEY",
            details={"required": ["OPENAI_API_KEY"]},
        )


class OpenAIInvoiceExtractor:
    """LLM-based invoice extraction using OpenAI.

    Strategy:
    - If PDF: extract text with pypdf, then ask the model to normalize into JSON.
    - If image: send the image to the model (vision) and ask for JSON.

    This avoids Assistants/file_search complexity in the POC, and makes test doubles easy.
    """

    def __init__(self, cfg: OpenAIConfig):
        self._cfg = cfg
        from openai import AsyncOpenAI  # lazy import
        self._client = AsyncOpenAI(api_key=cfg.api_key)

    async def extract(self, doc: InvoiceDocumentInput) -> ExtractedInvoice:
        if doc.mime_type == "application/pdf" or doc.filename.lower().endswith(".pdf"):
            text = self._extract_pdf_text(doc.file_base64)
            return await self._extract_from_text(text, filename=doc.filename)
        else:
            # assume image
            return await self._extract_from_image(doc.file_base64, mime_type=doc.mime_type, filename=doc.filename)

    def _extract_pdf_text(self, b64: str) -> str:
        from pypdf import PdfReader  # lazy import
        raw = base64.b64decode(b64)
        reader = PdfReader(io_bytes := __import__("io").BytesIO(raw))
        chunks: list[str] = []
        for page in reader.pages[:25]:  # protect from huge PDFs
            try:
                chunks.append(page.extract_text() or "")
            except Exception:
                continue
        text = "\n".join(chunks).strip()
        if not text:
            raise ToolError("Could not extract text from PDF.", code="UNPROCESSABLE_DOCUMENT")
        # trim to reduce token cost
        return text[:25_000]

    async def _extract_from_text(self, text: str, *, filename: str) -> ExtractedInvoice:
        prompt = self._prompt(filename=filename)
        resp = await self._client.chat.completions.create(
            model=self._cfg.model,
            temperature=self._cfg.temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You extract structured invoice/payment data."},
                {"role": "user", "content": prompt + "\n\nINVOICE_TEXT:\n" + text},
            ],
        )
        content = resp.choices[0].message.content or "{}"
        return self._parse_output(content)

    async def _extract_from_image(self, b64: str, *, mime_type: str, filename: str) -> ExtractedInvoice:
        prompt = self._prompt(filename=filename)
        data_url = f"data:{mime_type};base64,{b64}"
        resp = await self._client.chat.completions.create(
            model=self._cfg.model,
            temperature=self._cfg.temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You extract structured invoice/payment data."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ]},
            ],
        )
        content = resp.choices[0].message.content or "{}"
        return self._parse_output(content)

    def _prompt(self, *, filename: str) -> str:
        return f"""Parse this invoice document and return a SINGLE JSON object with these keys:

- processable: boolean
- reason: string|null (why not processable)
- payee: {{ name: string|null, email: string|null }}
- money: {{ amount: number|null, currency: string|null }}   # currency should be ISO-4217 like USD/CAD/EUR
- purpose: string|null
- invoice_number: string|null
- invoice_date: string|null  # ISO date if you can
- due_date: string|null      # ISO date if you can
- confidence: object mapping field name -> number 0..1
- warnings: array of strings

Rules:
- If this is NOT an invoice or you cannot find an amount, set processable=false and explain in reason.
- Never hallucinate emails or invoice numbers.
- Currency: infer from symbol only if unambiguous, otherwise null + warning.
- Amount: numeric value only.

Filename: {filename}
"""

    def _parse_output(self, content: str) -> ExtractedInvoice:
        try:
            data = json.loads(content)
        except Exception as e:
            logger.warning("LLM returned non-JSON: %s", e)
            raise ToolError("Invoice extractor returned invalid JSON.", code="LLM_BAD_OUTPUT")

        # Validate + coerce
        try:
            result = ExtractedInvoice.model_validate({**data, "raw": data})
        except ValidationError as e:
            raise ToolError("Invoice extractor output failed schema validation.", code="LLM_BAD_OUTPUT", details={"errors": e.errors()})

        # Minimal gate: amount is required for processable invoices
        if result.processable and (result.money.amount is None):
            result.processable = False
            result.reason = result.reason or "Missing amount."
            result.warnings.append("Amount not found; marked unprocessable.")
        return result
