"""
Payment history tools for Veem API MCP Server
"""

import json
import logging
import requests
import urllib.parse
import mysql.connector
from mcp_server.server_instance import mcp
from mcp_server.utils import (
    get_session_credentials,
    create_api_headers,
    create_success_response,
    create_error_response
)
from mcp_server.config import MY_SQL_PAYMENT_PARAMS, VEEM_API_BASE_URL

logger = logging.getLogger(__name__)


@mcp.tool()
def get_payment_history(payeeEmail: str) -> str:
    """
    Retrieve the most recent funding method used for payments between the authenticated user and a payee.
    
    This tool first fetches the payee's account ID from their email using the Veem API,
    then queries the MySQL database to find the most recent payment's funding method ID.
    
    Args:
        payeeEmail: The email address of the payee
    
    Returns:
        JSON string containing the payer_funding_method_id from the most recent payment
    
    Example:
        get_payment_history(payeeEmail="christopher.terrell+xyz@veem.com")
    """
    account_id, access_token = get_session_credentials()
    logger.info(f"[get_payment_history] payerAccountId={account_id}, payeeEmail={payeeEmail}")
    try:
        # First, get the payee's account ID from their email using Veem API
        encoded_email = urllib.parse.quote(payeeEmail)
        customer_url = f"{VEEM_API_BASE_URL}/customers?email={encoded_email}"
        
        headers = create_api_headers(access_token)
        logger.info(f"[get_payment_history] Fetching customer info for email: {payeeEmail}")
        
        response = requests.get(customer_url, headers=headers)
        logger.info(f"[get_payment_history] Customer API Status: {response.status_code}")
        
        if response.status_code != 200:
            return json.dumps(create_error_response(
                f"Failed to fetch customer info: {response.status_code}",
                "get_payment_history"
            ))
        
        customer_data = response.json()
        
        # Extract payee account ID from response
        # The response structure is: {"content": [{"id": ..., ...}], ...}
        content = customer_data.get('content', [])
        if not content or len(content) == 0:
            return json.dumps(create_error_response(
                f"No customer found with email: {payeeEmail}",
                "get_payment_history"
            ))
        
        payeeAccountId = content[0].get('id')
        if not payeeAccountId:
            return json.dumps(create_error_response(
                "Customer ID not found in API response",
                "get_payment_history"
            ))
        
        logger.info(f"[get_payment_history] Found payeeAccountId={payeeAccountId} for email={payeeEmail}")
        
        # Connect to MySQL database
        connection = mysql.connector.connect(**MY_SQL_PAYMENT_PARAMS)
        cursor = connection.cursor(dictionary=True)
        
        # Execute query
        query = """
            SELECT payer_funding_method_id 
            FROM payment.payment 
            WHERE payer_account_id = %s AND payee_account_id = %s 
            ORDER BY time_created DESC 
            LIMIT 1
        """
        cursor.execute(query, (account_id, payeeAccountId))
        
        # Fetch result
        result = cursor.fetchone()
        
        # Close connection
        cursor.close()
        connection.close()
        
        if result:
            return json.dumps(create_success_response(
                {
                    "payment_method_id": result['payer_funding_method_id'],
                    "payer_account_id": account_id,
                    "payee_account_id": payeeAccountId
                },
                "get_payment_history"
            ))
        else:
            return json.dumps(create_success_response(
                {
                    "payment_method_id": None,
                    "message": "No payment history found between these accounts"
                },
                "get_payment_history"
            ))
            
    except mysql.connector.Error as db_error:
        logger.error(f"Database error in get_payment_history: {str(db_error)}")
        return json.dumps(create_error_response(
            f"Database error: {str(db_error)}",
            "get_payment_history"
        ))
    except Exception as e:
        logger.error(f"Error in get_payment_history: {str(e)}")
        return json.dumps(create_error_response(
            f"Failed to retrieve payment history: {str(e)}",
            "get_payment_history"
        ))
