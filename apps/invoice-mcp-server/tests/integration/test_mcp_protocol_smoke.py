import pytest
import asyncio
import os

pytestmark = pytest.mark.integration

@pytest.mark.asyncio
async def test_mcp_streamable_http_protocol_smoke(fake_deps):
    # Optional smoke test that exercises the MCP transport.
    # Skips automatically if the MCP python client APIs are not available.
    try:
        from mcp import ClientSession  # type: ignore
        from mcp.client.streamable_http import streamablehttp_client  # type: ignore
    except Exception:
        pytest.skip("MCP client not available in environment")

    import uvicorn
    from veem_invoice_mcp.mcp_app import mcp

    # Start server in the background on an ephemeral port
    config = uvicorn.Config(mcp.streamable_http_app(), host="127.0.0.1", port=0, log_level="warning")
    server = uvicorn.Server(config)

    # uvicorn doesn't expose the chosen port before startup; use a fixed port for this smoke test
    # (in CI you can reserve a free port).
    port = 8765
    config = uvicorn.Config(mcp.streamable_http_app(), host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    task = asyncio.create_task(server.serve())
    await asyncio.sleep(0.5)

    try:
        async with streamablehttp_client(url=f"http://127.0.0.1:{port}/mcp") as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                tool_names = [t.name for t in tools.tools]
                assert "payment_prepare" in tool_names
    finally:
        server.should_exit = True
        await asyncio.sleep(0.2)
        task.cancel()
