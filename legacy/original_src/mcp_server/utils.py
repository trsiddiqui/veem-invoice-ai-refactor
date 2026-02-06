"""
Shared utilities for Veem API MCP Server

This module contains common functions used across all tool modules.
"""

import os
import json
import logging
import uuid
import requests
from typing import Dict, Optional
from mcp_server.config import VEEM_API_BASE_URL

logger = logging.getLogger(__name__)

# Session credentials (set via environment by parent process)
SESSION_ACCOUNT_ID = None
SESSION_ACCESS_TOKEN = None


def get_session_credentials():
    """Get session credentials from environment variables."""
    global SESSION_ACCOUNT_ID, SESSION_ACCESS_TOKEN
    if SESSION_ACCOUNT_ID is None:
        SESSION_ACCOUNT_ID = os.getenv('VEEM_SESSION_ACCOUNT_ID')
        SESSION_ACCESS_TOKEN = os.getenv('VEEM_SESSION_ACCESS_TOKEN')
    return SESSION_ACCOUNT_ID, SESSION_ACCESS_TOKEN


def create_api_headers(access_token: str) -> Dict[str, str]:
    """Create headers for Veem API requests."""
    return {
        'X-REQUEST-ID': str(uuid.uuid4()),
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }


def create_success_response(data: any, tool_name: str) -> Dict:
    """Create a standardized success response."""
    return {
        "data": {"status": "success", "response": data},
        "errors": [],
        "tool": tool_name
    }


def create_error_response(error: str, tool_name: str) -> Dict:
    """Create a standardized error response."""
    return {
        "data": None,
        "errors": [error],
        "tool": tool_name
    }


def make_api_request(method: str, endpoint: str, access_token: str, tool_name: str, payload: Optional[Dict] = None) -> str:
    """
    Make an API request and return standardized JSON response.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        access_token: OAuth access token
        tool_name: Name of the tool making the request
        payload: Optional request payload for POST requests
    
    Returns:
        JSON string containing standardized response
    """
    headers = create_api_headers(access_token)
    url = f"{VEEM_API_BASE_URL}/{endpoint}"
    
    # Log only tool call with inputs
    log_msg = f"[{tool_name}] {method.upper()} /{endpoint}"
    if payload:
        log_msg += f" | Payload: {json.dumps(payload)}"
    logger.info(log_msg)
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=payload)
        else:
            logger.error(f"[{tool_name}] Unsupported HTTP method: {method}")
            result = create_error_response(f"Unsupported HTTP method: {method}", tool_name)
            return json.dumps(result, indent=2)
        
        # Log only status code
        logger.info(f"[{tool_name}] Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            result = create_success_response(response.json(), tool_name)
        else:
            logger.error(f"[{tool_name}] API request failed with status {response.status_code}")
            result = create_error_response(str(response.content), tool_name)
        
        return json.dumps(result, indent=2)
            
    except Exception as e:
        logger.error(f"[{tool_name}] Request failed with exception: {str(e)}")
        result = create_error_response(f"Request failed: {str(e)}", tool_name)
        return json.dumps(result, indent=2)
