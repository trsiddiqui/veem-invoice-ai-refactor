"""
MCP Server Instance

This module contains the shared MCP server instance that all tool modules register with.
It's separated to avoid circular import issues.
"""

from mcp.server.fastmcp import FastMCP

# Initialize MCP server instance
mcp = FastMCP("veem_api_server")
