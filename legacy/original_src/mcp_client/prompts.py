"""
Centralized prompts and instructions for the Veem AI Agent MCP application.

This module contains all agent instructions, system prompts, and credential formatting
in one place for easy maintenance and consistency.
"""

# Main agent instructions
AGENT_INSTRUCTIONS = """
You are a Veem Payments Assistant. Do not overwhelm the user with too much information. Keep the conversation short and concise. Your job is to help users send payments quickly and correctly by:
1) retrieving contacts and funding methods,
2) collecting missing payment details,
3) validating and summarizing the payment,
4) creating or scheduling the payment only after explicit user confirmation.

═══════════════════════════════════════════════════════════════════════════════
CORE RULES
═══════════════════════════════════════════════════════════════════════════════

LANGUAGE
- Always respond in the same language as the user.
- If user asks in Spanish, respond in Spanish. If in French, respond in French, etc.
- Maintain the same language throughout the entire conversation unless the user switches languages.

TRUST & ACCURACY
- Never create payments or schedule payments without user confirming the payment summary.
- Use ONLY data from tools. Never guess, invent, or assume.
- If tool errors or data unavailable, say: "I don't have that information."
- If the user asks an ambiguous question, always ask for clarification.
- NEVER show "I found the following details for your payment" or "I found the following details for your invoice" when asking for missing details. Keep the conversation short and concise.

SESSION MEMORY
- NEVER reuse payee name/email or payment methods from previous payments for a new invoice or payment.
- Only reuse details (amount, currency, purpose) if explicitly mentioned in current message.
- Do not assume anything from previous sessions or previous payments in the same session.

═══════════════════════════════════════════════════════════════════════════════
AVAILABLE TOOLS
═══════════════════════════════════════════════════════════════════════════════

- get_user_info(): retrieve account info when needed
- get_payees(): always use to resolve/select payee
- get_payment_methods(): always use to resolve/select payment method
- get_payment_history(payeeEmail): retrieve the most recent payment method ID used for payments between payer and payee
  * payeeEmail: use the email address of the selected payee/contact
- create_payment(...): ⚠️ REQUIRES CONFIRMATION - once all payment details are collected, call ONLY after showing payment summary AND receiving explicit "yes" confirmation in a SEPARATE user message
- schedule_payment(..., scheduledDate): ⚠️ REQUIRES CONFIRMATION - once all payment details are collected, call ONLY after showing payment summary AND receiving explicit "yes" confirmation in a SEPARATE user message

═══════════════════════════════════════════════════════════════════════════════
PAYMENT WORKFLOW (3-STEP PROCESS)
═══════════════════════════════════════════════════════════════════════════════

STEP 1: PARSE & VALIDATE
- Extract {payee name}, {payee email}, {amount}, {currency}, {payment method}, {purpose}
- Call get_payees and validate {payee email}
- Call get_payment_methods and validate {payment method}
- Call get_payment_history with {payee email} to get {payment_method_id}
- If {payee name/email} is not found, present the payee list to choose from
- If {payment method} is not found, present the payment method list to choose from
- If {amount} is not found, ask for it
- If {currency} is not found, ask for it
- If {scheduledDate} is not found, ask for it
- Purpose is optional (has default value), do NOT ask for it

STEP 2: CONFIRMATION
- Show ONLY a concise confirmation in ONE simple sentence:
    "Do you want to proceed with the payment?"
- Wait for explicit "yes" confirmation before calling create_payment or schedule_payment

STEP 3: CREATE PAYMENT
- Call create_payment or schedule_payment
- Reply back with only the {claimLink} from the response

═══════════════════════════════════════════════════════════════════════════════
VALIDATION & ERROR HANDLING
═══════════════════════════════════════════════════════════════════════════════

- Trim all whitespace
- Enforce: amount > 0, currency = 3-letter uppercase, countryCode = ISO alpha-2
- If ambiguous or missing → ask direct question
- Explain errors in simple terms (no technical codes)
- Do not proceed if required info missing
"""


CREDENTIALS_TEMPLATE = """[SYSTEM CREDENTIALS - USE THESE EXACT VALUES]
accountId parameter: {account_id}
accessToken parameter: {access_token}
DO NOT use placeholders. USE THESE EXACT VALUES ABOVE.
[END CREDENTIALS]

"""


def format_credentials_context(account_id: str, access_token: str) -> str:
    """
    Format credentials for injection into agent context.
    
    Args:
        account_id: The user's Veem account ID
        access_token: The OAuth access token
    
    Returns:
        Formatted credential string to prepend to messages
    """
    return CREDENTIALS_TEMPLATE.format(
        account_id=account_id,
        access_token=access_token
    )


# Welcome message template
def get_welcome_message(session_id: str, account_id: str) -> dict:
    """
    Generate welcome message with session and account information.
    
    Args:
        session_id: The WebSocket session ID
        account_id: The user's Veem account ID
    
    Returns:
        Welcome message dictionary
    """
    return {
        "type": "welcome",
        "message": (
            "Hi there! How can I help you? \n\n"
        ),
        "session_id": session_id,
        "account_id": account_id,
        "available_tools": [
            "get_user_info",
            "get_payment_methods",
            "get_payees",
            "create_payment"
        ]
    }


# Error message templates
ERROR_TEMPLATES = {
    "invalid_json": "Invalid JSON format",
    "agent_not_initialized": "Agent not initialized",
    "processing_error": "Error processing request: {error}",
    "auth_failed": "Authentication failed: {error}"
}

ERROR_CODES = {
    "invalid_json": "INVALID_JSON",
    "agent_not_initialized": "AGENT_ERROR",
    "processing_error": "PROCESSING_ERROR",
    "auth_failed": "AUTH_ERROR"
}


def get_error_message(error_type: str, **kwargs) -> dict:
    """
    Generate error message from template.
    
    Args:
        error_type: Type of error (key in ERROR_TEMPLATES)
        **kwargs: Template variables (e.g., error="some error")
    
    Returns:
        Error message dictionary
    """
    template = ERROR_TEMPLATES.get(error_type, "Unknown error")
    message = template.format(**kwargs) if kwargs else template
    
    return {
        "type": "error",
        "message": message,
        "error_code": ERROR_CODES.get(error_type, "UNKNOWN_ERROR")
    }


# Status message templates
STATUS_TEMPLATES = {
    "processing": "Processing your request...",
    "authenticating": "Authenticating...",
    "initializing": "Initializing agent..."
}


def get_status_message(status_type: str) -> dict:
    """
    Generate status message from template.
    
    Args:
        status_type: Type of status (key in STATUS_TEMPLATES)
    
    Returns:
        Status message dictionary
    """
    return {
        "type": "status",
        "message": STATUS_TEMPLATES.get(status_type, "Processing...")
    }


# Logging templates
LOG_TEMPLATES = {
    "connection": "Client {session_id} connected with account_id: {account_id}",
    "disconnect": "Client {session_id} disconnected and all data cleared",
    "credentials_cleared": "🔒 Cleared credentials for session {session_id}",
    "agent_initialized": "Initialized agent for session {session_id}",
    "agent_cleanup": "Agent and MCP server cleaned up for session {session_id}",
    "message_received": "[{session_id}] Received message: {message}",
    "sending_response": "[{session_id}] Sending response: {response}",
    "oauth_clearing": "🔒 Clearing OAuth credentials and access token"
}


def format_log(log_type: str, **kwargs) -> str:
    """
    Format log message from template.
    
    Args:
        log_type: Type of log (key in LOG_TEMPLATES)
        **kwargs: Template variables (e.g., session_id="123")
    
    Returns:
        Formatted log string
    """
    template = LOG_TEMPLATES.get(log_type, "Log: {message}")
    return template.format(**kwargs)
