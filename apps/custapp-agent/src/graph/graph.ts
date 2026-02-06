import { StateGraph } from "langgraph";
import type { AgentState } from "./state.js";
import { AgentStateSchema } from "./state.js";
import { McpToolClient } from "../mcp/client.js";

/**
 * Minimal graph demonstrating the flow:
 * - invoice upload OR command
 * - payment_prepare
 * - build Review & Confirm payload
 *
 * Submission is intentionally left as a UI-triggered step (user confirmation).
 */
export function buildPaymentGraph() {
  const graph = new StateGraph<AgentState>({
    channels: AgentStateSchema.shape,
  });

  graph.addNode("maybe_parse_invoice", async (state) => {
    if (!state.invoice) return state;

    const client = new McpToolClient("veem-invoice-mcp", []);
    await client.connect();
    const res = await client.call("invoice_process", {
      file_base64: state.invoice.fileBase64,
      mime_type: state.invoice.mimeType,
      filename: state.invoice.filename,
    });
    await client.close();

    return {
      ...state,
      extractedInvoice: (res as any).content?.[0]?.json ?? (res as any),
    };
  });

  graph.addNode("prepare_payment", async (state) => {
    const client = new McpToolClient("veem-invoice-mcp", []);
    await client.connect();

    const res = await client.call("payment_prepare", {
      command: state.userMessage,
      invoice: state.extractedInvoice,
    });

    await client.close();
    return { ...state, paymentDraft: (res as any).content?.[0]?.json ?? (res as any) };
  });

  graph.addNode("review_confirm", async (state) => {
    const draft = state.paymentDraft?.data ?? state.paymentDraft;
    const assumptions = draft?.assumptions ?? [];
    const needsConfirmation = Boolean(draft?.needs_confirmation ?? true);

    return {
      ...state,
      reviewAndConfirm: {
        title: "Review & Confirm",
        summaryLines: [
          `Payee: ${draft?.payee?.name ?? "Unknown"} (${draft?.payee?.email ?? "no email"})`,
          `Amount: ${draft?.amount ?? "?"} ${draft?.currency ?? ""}`,
          `Funding method: ${draft?.funding_method_id ?? "?"}`,
          `Purpose: ${draft?.purpose ?? ""}`,
        ],
        draft,
        needsConfirmation,
        assumptions,
      },
    };
  });

  graph.setEntryPoint("maybe_parse_invoice");
  graph.addEdge("maybe_parse_invoice", "prepare_payment");
  graph.addEdge("prepare_payment", "review_confirm");
  graph.setFinishPoint("review_confirm");

  return graph.compile();
}
