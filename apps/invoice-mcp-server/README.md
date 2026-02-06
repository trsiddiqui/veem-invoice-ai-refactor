# Invoice MCP Server (Veem) — Workflow Tools

This MCP server is designed around **Pattern A: “Full E2E workflow tools”**.

Instead of exposing dozens of thin REST wrappers, it exposes a small set of **workflow** tools that match how the agent works:

## Tools

### `invoice_process`
- Input: invoice bytes (base64) + mime type + filename
- Output: `processable` boolean + normalized extraction (payee, amount, currency, invoice number/date, memo, etc.)
- Behavior: If the document is unreadable / not an invoice / missing critical fields → returns `processable=false` with a reason.

### `payment_prepare`
- Input: either a natural language command or the output of `invoice_process`
- Output: a **PaymentDraft** containing:
  - resolved Veem entities (payee/contact)
  - inferred currency & funding method (from history when possible)
  - a list of **assumptions** and `needs_confirmation=true|false`

### `payment_submit`
- Input: PaymentDraft (+ any user modifications)
- Output: Veem payment creation/submission result + idempotency key

### `payment_schedule`
- Input: PaymentDraft + scheduled datetime
- Output: scheduled job id (POC uses SQLite). In production, swap the adapter to the PaymentDomain schedule API.

---

## Running locally

```bash
uv sync
uv run python -m veem_invoice_mcp.server
```

Inspector:

```bash
uv run mcp dev src/veem_invoice_mcp/server.py
```

---

## Testing

We use `pytest` with 4 layers:

1. **Unit**: pure functions + model validation
2. **Contract**: tool outputs conform to schemas
3. **Integration**: MCP server running in-process and invoked through a client session (no external Veem calls; mocked)
4. **E2E**: invoice → draft → submit using test doubles

Run:

```bash
uv run pytest
```

---

## Configuration

See root README for `.env` keys.

