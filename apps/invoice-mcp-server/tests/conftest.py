import pytest
from dataclasses import dataclass
from typing import Any, Optional

from veem_invoice_mcp.domain.invoice.models import ExtractedInvoice, PayeeHint, Money


class FakeVeemApi:
    def __init__(self):
        self._account_id = "acct_test"

    @property
    def account_id(self) -> str:
        return self._account_id

    async def list_contacts(self) -> dict[str, Any]:
        return {
            "contacts": [
                {"id": "c1", "name": "Sam Example", "email": "sam@example.com"},
                {"id": "c2", "name": "Samantha Vendor", "email": "vendor@biz.com"},
            ]
        }

    async def list_funding_methods(self) -> dict[str, Any]:
        return {
            "fundingMethods": [
                {"id": "fm_1", "type": "bank", "currency": "USD"},
                {"id": "fm_2", "type": "card", "currency": "USD"},
            ]
        }

    async def create_payment(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"id": "pmt_123", "status": "created", "echo": payload}


class FakeHistoryStore:
    async def last_funding_method_id_for_payee(self, payee_email: str) -> Optional[str]:
        if payee_email == "sam@example.com":
            return "fm_2"
        return None


class FakeScheduleStore:
    async def create(self, *, draft: dict[str, Any], run_at_utc: str) -> dict[str, Any]:
        return {"schedule_id": "sch_1", "status": "scheduled", "run_at_utc": run_at_utc, "draft": draft}


class FakeInvoiceExtractor:
    async def extract(self, doc):
        return ExtractedInvoice(
            processable=True,
            payee=PayeeHint(name="Sam Example", email="sam@example.com"),
            money=Money(amount=50.0, currency="USD"),
            purpose="Lunch reimbursement",
            confidence={"money.amount": 0.9, "payee.name": 0.8},
        )


@dataclass
class FakeDeps:
    veem: Any
    history_store: Any
    schedule_store: Any
    invoice_extractor: Any


@pytest.fixture()
def fake_deps(monkeypatch):
    deps = FakeDeps(
        veem=FakeVeemApi(),
        history_store=FakeHistoryStore(),
        schedule_store=FakeScheduleStore(),
        invoice_extractor=FakeInvoiceExtractor(),
    )
    # Patch the global dependencies used by tools
    import veem_invoice_mcp.runtime as runtime
    monkeypatch.setattr(runtime, "DEPS", deps)
    # Also patch modules that imported DEPS directly
    import veem_invoice_mcp.domain.invoice.tools as invoice_tools
    import veem_invoice_mcp.domain.payments.tools as payment_tools
    monkeypatch.setattr(invoice_tools, "DEPS", deps)
    monkeypatch.setattr(payment_tools, "DEPS", deps)
    return deps
