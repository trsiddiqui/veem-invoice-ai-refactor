from veem_invoice_mcp.domain.payments.workflow import parse_payment_command

def test_parse_payment_command_basic():
    parsed = parse_payment_command("Pay $50 to Sam for lunch")
    assert parsed["amount"] == 50.0
    assert parsed["payee_name"].lower() == "sam"
    assert parsed["purpose"].lower() == "lunch"
