# Veem Invoice AI (POC)

Flow Diagram here (Agent + LangGraph + MCP) --> https://drive.google.com/file/d/1dBR_v_DPKAxuON1gYXfGGoBnjN_nXV6q/view?usp=sharing

This repo contains **two deployable units**:

1. **Invoice MCP Server (Python)** — exposes *workflow* MCP tools:

   - `invoice_process` — parse an invoice (PDF/image) into normalized payment fields, or return `processable=false`
   - `payment_prepare` — infer/payee+funding method+currency+purpose and produce an in memory *draft* requiring minimal user input
   - `payment_submit` — create/submit the payment in Veem
   - `payment_schedule` — schedule a payment
2. **CustApp Agent (TypeScript, LangGraph)** — a thin host/orchestrator that calls MCP tools, drives the chat flow,
   and renders a final **Review & Confirm** step.


## Repo layout

```
apps/
  invoice-mcp-server/      # Python MCP server + tests
  custapp-agent/           # TypeScript LangGraph host (skeleton)
```

---

## Environment variables (server)

Create `apps/invoice-mcp-server/.env`:

```
OPENAI_API_KEY=...
VEEM_API_BASE_URL=https://api.qa.veem.com/veem/v1.2
VEEM_ACCOUNT_ID=...
VEEM_ACCESS_TOKEN=...

# Optional: payment history inference store
VEEM_MYSQL_HOST=...
VEEM_MYSQL_USER=...
VEEM_MYSQL_PASSWORD=...
VEEM_MYSQL_DATABASE=...
```

---

## Notes on design

- **Pattern: E2E workflow tools**
  Each MCP tool is a complete workflow step (parse → infer → validate → draft/submit), rather than a 1:1 wrapper around Veem’s REST endpoints.
- **Ports & adapters**
  All external dependencies are behind interfaces (Veem API, history store, schedule store, LLM extractor) so we can test deterministically.
- **Testing**
  Using `pytest` + `pytest-asyncio` for unit/contract/integration/E2E tests. See `apps/invoice-mcp-server/README.md`.

---


### Quick start

### 1) Run the MCP server locally

```bash
cd apps/invoice-mcp-server

# Recommended: uv
uv sync
uv run python -m veem_invoice_mcp.server
```

Then connect with the MCP Inspector:

```bash
# From the same folder:
uv run mcp dev src/veem_invoice_mcp/server.py
# or:
npx -y @modelcontextprotocol/inspector
```

### 2) Run tests

```bash
cd apps/invoice-mcp-server
uv run pytest
```

### 3) Run the LangGraph agent (skeleton)

```bash
cd apps/custapp-agent
npm install
npm run dev
```

---
