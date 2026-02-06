import pytest
from veem_invoice_mcp.domain.payments.workflow import prepare_payment
from veem_invoice_mcp.domain.invoice.models import ExtractedInvoice, PayeeHint, Money

@pytest.mark.asyncio
async def test_prepare_payment_infers_funding_method_from_history(fake_deps):
    inv = ExtractedInvoice(
        processable=True,
        payee=PayeeHint(name="Sam Example", email="sam@example.com"),
        money=Money(amount=50.0, currency="USD"),
        purpose="Lunch reimbursement",
    )
    draft = await prepare_payment(fake_deps, invoice=inv)
    assert draft.funding_method_id == "fm_2"
    assert draft.payee.contact_id == "c1"
    assert draft.amount == 50.0
