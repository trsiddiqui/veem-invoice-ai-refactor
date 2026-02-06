import pytest

from veem_invoice_mcp.domain.invoice.tools import invoice_process
from veem_invoice_mcp.domain.payments.tools import payment_prepare, payment_submit, payment_schedule

@pytest.mark.asyncio
async def test_tools_smoke_invoice_to_submit(fake_deps):
    inv_res = await invoice_process(file_base64="ZmFrZQ==", mime_type="image/png", filename="invoice.png")
    assert inv_res["ok"] is True
    invoice = inv_res["data"]
    prep_res = await payment_prepare(invoice=invoice)
    assert prep_res["ok"] is True
    draft = prep_res["data"]
    submit_res = await payment_submit(draft=draft)
    assert submit_res["ok"] is True
    assert submit_res["data"]["payment_id"] == "pmt_123"

@pytest.mark.asyncio
async def test_tools_smoke_schedule(fake_deps):
    prep_res = await payment_prepare(command="Pay $50 to Sam for lunch")
    draft = prep_res["data"]
    sch = await payment_schedule(draft=draft, run_at_utc="2030-01-01T00:00:00Z")
    assert sch["ok"] is True
    assert sch["data"]["schedule_id"] == "sch_1"
