from __future__ import annotations

import os

import uvicorn
from veem_invoice_mcp.logging import configure_logging
from veem_invoice_mcp.mcp_app import mcp


def main() -> None:
    configure_logging()
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    # Streamable HTTP transport app
    app = mcp.streamable_http_app()
    uvicorn.run(app, host=host, port=port, log_level=os.getenv("LOG_LEVEL", "info").lower())


if __name__ == "__main__":
    main()
