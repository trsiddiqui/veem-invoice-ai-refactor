from veem_invoice_mcp.domain.payments.models import PaymentDraft, ResolvedPayee

def test_payment_draft_schema_roundtrip():
    draft = PaymentDraft(
        draft_id="d1",
        idempotency_key="k1",
        payee=ResolvedPayee(contact_id="c1", name="Sam", email="sam@example.com", match_confidence=1.0),
        amount=10.0,
        currency="USD",
        purpose="Test",
        funding_method_id="fm_1",
        needs_confirmation=False,
        assumptions=[],
        missing_fields=[],
        proposed_payment_payload={"foo": "bar"},
    )
    dumped = draft.model_dump(mode="json")
    # Validate can be read back
    PaymentDraft.model_validate(dumped)
