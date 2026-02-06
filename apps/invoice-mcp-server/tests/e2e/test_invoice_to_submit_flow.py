import pytest

from veem_invoice_mcp.domain.invoice.tools import invoice_process
from veem_invoice_mcp.domain.payments.tools import payment_prepare, payment_submit

@pytest.mark.asyncio
async def test_e2e_invoice_to_draft_to_submit(fake_deps):
    # 1) parse invoice (fake extractor)
    inv_res = await invoice_process(file_base64="ZmFrZQ==", mime_type="image/png", filename="invoice.png")
    invoice = inv_res["data"]

    # 2) infer entities + create draft
    prep = await payment_prepare(invoice=invoice)
    draft = prep["data"]

    # 3) simulate user edit (change purpose)
    draft["purpose"] = "Updated purpose from user"
    draft["proposed_payment_payload"]["purpose"] = draft["purpose"]

    # 4) submit
    submit = await payment_submit(draft=draft)
    assert submit["data"]["raw"]["echo"]["purpose"] == "Updated purpose from user"
