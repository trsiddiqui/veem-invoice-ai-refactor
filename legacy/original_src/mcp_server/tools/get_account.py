"""
Account-related tools for Veem API MCP Server
"""

from mcp_server.server_instance import mcp
from mcp_server.utils import get_session_credentials, make_api_request


@mcp.tool()
async def get_account() -> str:
    """
    Get user information for the authenticated session.
    
    Returns:
        JSON string containing standardized response with user information
    """
    account_id, access_token = get_session_credentials()
    return make_api_request(
        method="GET",
        endpoint=f"account/{account_id}",
        access_token=access_token,
        tool_name="get_account"
    )
