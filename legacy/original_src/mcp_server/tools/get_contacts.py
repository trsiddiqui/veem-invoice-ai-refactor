"""
Contact-related tools for Veem API MCP Server
"""

from mcp_server.server_instance import mcp
from mcp_server.utils import get_session_credentials, make_api_request


@mcp.tool()
async def get_payees() -> str:
    """
    Get user's payees information.
    
    Returns:
        JSON string containing standardized response with payees information
    """
    _, access_token = get_session_credentials()
    return make_api_request(
        method="GET",
        endpoint="contacts",
        access_token=access_token,
        tool_name="get_payees"
    )
