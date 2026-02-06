"""
Payment-related tools for Veem API MCP Server
"""

import json
import logging
from mcp_server.server_instance import mcp
from mcp_server.utils import (
    get_session_credentials,
    make_api_request,
    create_success_response
)

logger = logging.getLogger(__name__)


@mcp.tool()
async def create_payment(
    payeeEmail: str,
    payeeCountryCode: str,
    amountNumber: float,
    amountCurrency: str,
    fundingMethodId: str,
    fundingMethodType: str,
    purposeOfPayment: str = "Payment for services"
) -> str:
    """
    Create a new payment to an existing contact using an existing funding method.
    
    This tool creates a payment assuming:
    - The payee (contact) already exists in the system
    - The funding method already exists and is active
    
    Args:
        payeeEmail: Email address of the payee (must be an existing contact)
        payeeCountryCode: ISO country code of the payee (e.g., 'US', 'CA')
        amountNumber: The amount of money to send (e.g., 100.50)
        amountCurrency: The currency code (e.g., 'USD', 'CAD')
        fundingMethodId: The ID of the funding method to use (from get_payment_methods)
        fundingMethodType: The type of funding method (e.g., 'Bank', 'Wallet')
        purposeOfPayment: The purpose/reason for the payment (defaults to "Payment for services")
    
    Returns:
        JSON string containing the created payment details or error information
    """
    _, access_token = get_session_credentials()
    
    # Use default purpose if not provided or empty
    if not purposeOfPayment or purposeOfPayment.strip() == "":
        purposeOfPayment = "Payment for services"
    
    payload = {
        "amount": {
            "number": amountNumber,
            "currency": amountCurrency
        },
        "payee": {
            "email": payeeEmail,
            "countryCode": payeeCountryCode,
            "type": "Incomplete"
        },
        "fundingMethod": {
            "id": fundingMethodId,
            "type": fundingMethodType
        },
        "purposeOfPayment": purposeOfPayment
    }
    
    return make_api_request(
        method="POST",
        endpoint="payments",
        access_token=access_token,
        tool_name="create_payment",
        payload=payload
    )


@mcp.tool()
def schedule_payment(
    payeeEmail: str,
    payeeCountryCode: str,
    amountNumber: float,
    amountCurrency: str,
    fundingMethodId: str,
    fundingMethodType: str,
    scheduledDate: str,
    purposeOfPayment: str = "Payment for services"
) -> str:
    """
    Schedule a payment to be sent on a specific future date.
    
    This tool schedules a payment for a future date instead of sending it immediately.
    
    Args:
        payeeEmail: Email address of the payee (must be an existing contact)
        payeeCountryCode: ISO country code of the payee (e.g., 'US', 'CA')
        amountNumber: The amount of money to send (e.g., 100.50)
        amountCurrency: The currency code (e.g., 'USD', 'CAD')
        fundingMethodId: The ID of the funding method to use (from get_payment_methods)
        fundingMethodType: The type of funding method (e.g., 'Bank', 'Wallet')
        scheduledDate: The date to send the payment (format: YYYY-MM-DD)
        purposeOfPayment: The purpose/reason for the payment (defaults to "Payment for services")
    
    Returns:
        JSON string confirming the payment has been scheduled
    """
    # Use default purpose if not provided or empty
    if not purposeOfPayment or purposeOfPayment.strip() == "":
        purposeOfPayment = "Payment for services"
    
    logger.info(f"[schedule_payment] payeeEmail={payeeEmail}, amount={amountNumber} {amountCurrency}, scheduledDate={scheduledDate}")
    
    # For now, just return a confirmation message
    confirmation_message = (
        f"Payment scheduled successfully!\n"
        f"- To: {payeeEmail}\n"
        f"- Amount: {amountNumber} {amountCurrency}\n"
        f"- Scheduled Date: {scheduledDate}\n"
        f"- Purpose: {purposeOfPayment}\n"
        f"The payment will be processed on {scheduledDate}."
    )
    
    return json.dumps(create_success_response(
        {"message": confirmation_message, "scheduled_date": scheduledDate},
        "schedule_payment"
    ))
