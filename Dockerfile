# Container for the Invoice MCP Server (Streamable HTTP)
FROM python:3.11-slim

WORKDIR /app

# System deps (optional; keep minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY apps/invoice-mcp-server/pyproject.toml apps/invoice-mcp-server/README.md /app/
COPY apps/invoice-mcp-server/src /app/src

RUN pip install --no-cache-dir "mcp[cli]" "uvicorn[standard]" && \
    pip install --no-cache-dir -e .

EXPOSE 8000

# Streamable HTTP transport default endpoint is /mcp
CMD ["python", "-m", "veem_invoice_mcp.server"]
