"""
MCP Client Configuration

Settings for the WebSocket client, AI agent, and MCP server connection.
"""

from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# MCP Server configuration - points to the MCP server
MCP_SERVER_CONFIG = {
    "command": "python",
    "args": ["mcp_server/veem_api_server.py"],
    "timeout_seconds": 60
}

# Model configuration
MODEL_CONFIG = {
    "name": "gpt-4o-mini",
    "tracing_enabled": False,
    "model_kwargs": {
        "temperature": 0,
        "top_p": 0.1
    }
}

# Extraction model configuration
EXTRACTION_MODEL_CONFIG = {
    "name": "gpt-4o",
    "temperature": 0.3
}

# Tool descriptions for documentation
TOOL_DESCRIPTIONS = {
    "get_user_info": {
        "name": "get_user_info",
        "description": "Retrieve user account information using account ID and access token",
        "parameters": ["accountId", "accessToken"],
        "returns": "User account details including business name, email, country, etc."
    },
    "get_payment_methods": {
        "name": "get_payment_methods",
        "description": "Retrieve user's payment methods using access token",
        "parameters": ["accessToken"],
        "returns": "List of payment methods (banks, wallets) with IDs, types, currencies"
    },
    "get_payees": {
        "name": "get_payees",
        "description": "Retrieve user's payees using access token",
        "parameters": ["accessToken"],
        "returns": "List of payees with emails, names, countries, payment status"
    },
    "create_payment": {
        "name": "create_payment",
        "description": "Create a payment to an existing payee using an existing payment method",
        "parameters": [
            "accessToken",
            "payeeEmail",
            "payeeCountryCode",
            "amountNumber",
            "amountCurrency",
            "fundingMethodId",
            "fundingMethodType",
            "purposeOfPayment"
        ],
        "returns": "Payment creation result with payment ID and status"
    }
}

# Conversation history configuration
CONVERSATION_CONFIG = {
    "max_history_messages": 6,
    "include_credentials_in_every_message": True
}
