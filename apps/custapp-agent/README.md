# CustApp Agent (LangGraph) — Skeleton

This folder contains a minimal LangGraph host that calls the **Invoice MCP Server** workflow tools.

> This is a scaffold to show the **graph shape** and state management.
> To be wired into CustApp UI + auth/session as needed.

## Run

```bash
npm install
npm run dev
```

## What it does

- Creates a LangGraph `StateGraph`
- Nodes call MCP tools:
  - `invoice_process` (when user uploads an invoice)
  - `payment_prepare`
  - `payment_submit` / `payment_schedule`
- Produces a `review_and_confirm` object your UI can render as a structured message.

## Where to edit

- `src/graph/graph.ts` — overall flow
- `src/graph/state.ts` — state schema
- `src/mcp/client.ts` — MCP client wrapper

