from __future__ import annotations

from mcp.server.fastmcp import FastMCP

# The MCP server instance
mcp = FastMCP(
    "Veem Invoice AI",
    # Force structured JSON responses (recommended for agentic workflows)
    json_response=True,
)

# Register workflow tools (Pattern A)
from veem_invoice_mcp.domain.invoice.tools import invoice_process
from veem_invoice_mcp.domain.payments.tools import payment_prepare, payment_submit, payment_schedule

mcp.tool()(invoice_process)
mcp.tool()(payment_prepare)
mcp.tool()(payment_submit)
mcp.tool()(payment_schedule)

__all__ = ["mcp"]
