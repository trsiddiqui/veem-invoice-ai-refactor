import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

/**
 * MCP client wrapper.
 *
 * In CustApp you'll likely use Streamable HTTP transport instead of stdio.
 * This wrapper keeps the graph nodes clean.
 */
export class McpToolClient {
  private client: Client;

  constructor(private serverCommand: string, private serverArgs: string[] = []) {
    const transport = new StdioClientTransport({
      command: serverCommand,
      args: serverArgs,
      env: process.env as Record<string, string>,
    });
    this.client = new Client(
      { name: "custapp-agent", version: "0.1.0" },
      { transport }
    );
  }

  async connect() {
    await this.client.connect();
  }

  async call(toolName: string, args: Record<string, unknown>) {
    return this.client.callTool({ name: toolName, arguments: args });
  }

  async close() {
    await this.client.close();
  }
}
