import { z } from "zod";

export const AgentStateSchema = z.object({
  userMessage: z.string().optional(),
  // Raw invoice upload (base64) if provided
  invoice: z
    .object({
      fileBase64: z.string(),
      mimeType: z.string(),
      filename: z.string(),
    })
    .optional(),

  // Outputs from MCP
  extractedInvoice: z.any().optional(),
  paymentDraft: z.any().optional(),
  paymentResult: z.any().optional(),

  // UI artifact for Review & Confirm
  reviewAndConfirm: z
    .object({
      title: z.string(),
      summaryLines: z.array(z.string()),
      draft: z.any(),
      needsConfirmation: z.boolean(),
      assumptions: z.array(z.string()),
    })
    .optional(),
});

export type AgentState = z.infer<typeof AgentStateSchema>;
