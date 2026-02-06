"""
Veem API MCP Client - WebSocket Application

This application provides a WebSocket interface for the Veem API MCP server,
allowing real-time communication with conversation memory.
"""

import os
import json
import logging
from typing import Dict, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from mcp_client.auth import AuthenticationService
from mcp_client.connection_manager import ConnectionManager
from mcp_client.prompts import (
    get_welcome_message,
    get_error_message,
    get_status_message,
    format_log
)

load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reduce httpx logging verbosity
logging.getLogger("httpx").setLevel(logging.WARNING)

# Initialize FastAPI app
application = FastAPI(title="Veem API MCP WebSocket Server")

# Add CORS middleware
application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize services
auth_service = AuthenticationService()
manager = ConnectionManager()


@application.get("/")
async def root():
    return {
        "message": "Veem API MCP WebSocket Server",
        "websocket_endpoint": "/ws/{session_id}?client_id=xxx&client_secret=yyy",
        "authentication": "OAuth 2.0 Client Credentials",
        "features": [
            "Real-time communication",
            "Conversation memory",
            "MCP tool integration",
            "OAuth authentication",
            "Payment creation"
        ],
        "tools": [
            "get_user_info",
            "get_payment_methods",
            "get_payees",
            "create_payment"
        ],
        "status": "running"
    }


@application.get("/health")
async def health_check():
    return {"status": "healthy"}


@application.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    client_id: Optional[str] = Query(None, description="Client ID for authentication"),
    client_secret: Optional[str] = Query(None, description="Client secret for authentication")
):
    """
    WebSocket endpoint for real-time communication with the MCP agent.
    
    Authentication:
    - client_id and client_secret must be provided as query parameters
    - Example: ws://localhost:8000/ws/{session_id}?client_id=xxx&client_secret=yyy
    - Server calls Veem OAuth API to authenticate and obtain account_id and access_token
    
    Expected message format from client:
    {
        "type": "message",
        "content": "user's question here"
    }
    
    Response format to client:
    {
        "type": "response",
        "content": "AI's response here",
        "session_id": "session_id",
        "account_id": "account_id"
    }
    
    Error format:
    {
        "type": "error",
        "message": "error description",
        "error_code": "ERROR_CODE"
    }
    """
    # Validate credentials
    if not auth_service.validate_credentials(client_id, client_secret):
        await websocket.accept()
        await websocket.send_json(get_error_message(
            "auth_failed",
            error="Invalid or missing credentials"
        ))
        await websocket.close()
        logger.warning(f"Connection rejected for session {session_id}: Invalid credentials")
        return
    
    # Authenticate client with Veem OAuth API
    auth_info = await auth_service.authenticate(client_id, client_secret)
    if not auth_info:
        await websocket.accept()
        await websocket.send_json(get_error_message(
            "auth_failed",
            error="Unable to authenticate credentials with Veem API"
        ))
        await websocket.close()
        logger.warning(f"Connection rejected for session {session_id}: Authentication failed")
        return
    
    # Log connection attempt
    logger.info("="*80)
    logger.info(f"NEW WEBSOCKET CONNECTION")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Account ID: {auth_info.get('account_id')}")
    logger.info(f"Client: {websocket.client.host}:{websocket.client.port}" if websocket.client else "Client: Unknown")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("="*80)
    
    await manager.connect(websocket, session_id, auth_info)
    
    try:
        # Initialize agent for this session
        logger.info(f"[{session_id}] Initializing MCP agent...")
        await manager.initialize_agent(session_id)
        logger.info(f"[{session_id}] Agent initialized successfully")
        
        # Send welcome message with authentication confirmation
        await manager.send_message(
            session_id,
            get_welcome_message(session_id, auth_info.get("account_id"))
        )
        
        logger.info(f"[{session_id}] Welcome message sent. Connection established.")
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "message")

                # Get authentication info
                auth_info = manager.get_auth_info(session_id)
                account_id = auth_info.get("account_id") if auth_info else None
                access_token = auth_info.get("access_token") if auth_info else None
                
                # Handle document upload
                if message_type == "document_upload":
                    document_data = message_data.get("document_data", "")
                    filename = message_data.get("filename", "document.pdf")
                    
                    logger.info(f"[{session_id}] Received document upload: {filename}")
                    
                    upload_result = await manager.handle_document_upload(session_id, document_data, filename)
                    
                    if upload_result["success"]:
                        extracted_details = upload_result["extracted_details"]
                        
                        # Format structured extraction data as user message
                        payee_name = extracted_details.get("payee", {}).get("name") or "Unknown"
                        payee_email = extracted_details.get("payee", {}).get("email") or "Not provided"
                        amount_value = extracted_details.get("amount", {}).get("value") or "Unknown"
                        amount_currency = extracted_details.get("amount", {}).get("currency") or "USD"
                        invoice_number = extracted_details.get("invoice", {}).get("invoice_number") or "N/A"
                        invoice_date = extracted_details.get("invoice", {}).get("invoice_date") or "N/A"
                        due_date = extracted_details.get("invoice", {}).get("due_date") or "N/A"
                        
                        # Create user message with extracted details
                        user_message = (
                            f"I uploaded an invoice with the following details:\n"
                            f"Payee: {payee_name}\n"
                            f"Email: {payee_email}\n"
                            f"Amount: {amount_value} {amount_currency}\n"
                            f"Invoice Number: {invoice_number}\n"
                            f"Invoice Date: {invoice_date}\n"
                            f"Due Date: {due_date}"
                        )
                        
                        # Add user message to history
                        manager.add_to_history(session_id, "user", user_message)
                    else:
                        await manager.send_message(session_id, get_error_message(
                            "upload_failed",
                            error=upload_result.get("error", "Unknown error")
                        ))
                        continue
                
                else:
                    # Regular message handling
                    user_message = message_data.get("content", "")
                    
                    # Validate message content
                    if not user_message:
                        await manager.send_message(
                            session_id,
                            get_error_message("processing_error", error="Empty message received")
                        )
                        continue
                    
                    # Add user message to history
                    manager.add_to_history(session_id, "user", user_message)
                
                # Log incoming message
                logger.info(f"[{session_id}] Processing message: {user_message[:100]}..." if len(user_message) > 100 else f"[{session_id}] Processing message: {user_message}")
                
                # Send acknowledgment
                await manager.send_message(session_id, get_status_message("processing"))
                
                # Run agent with conversation history
                response_content = await manager.run_agent(
                    session_id=session_id,
                    user_message=user_message
                )
                
                # Add assistant response to history
                manager.add_to_history(session_id, "assistant", response_content)
                
                # Log response
                logger.info(f"[{session_id}] Sending response: {response_content[:100]}..." if len(response_content) > 100 else f"[{session_id}] Sending response: {response_content}")
                
                # Send the AI response back to the client
                await manager.send_message(session_id, {
                    "type": "response",
                    "content": response_content,
                    "session_id": session_id,
                    "account_id": account_id
                })
                
            except json.JSONDecodeError:
                await manager.send_message(
                    session_id,
                    get_error_message("invalid_json")
                )
            except Exception as e:
                logger.error(f"Error processing message for {session_id}: {str(e)}")
                await manager.send_message(
                    session_id,
                    get_error_message("processing_error", error=str(e))
                )
    
    except WebSocketDisconnect:
        logger.info("="*80)
        logger.info(f"WEBSOCKET DISCONNECTED")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"Duration: {datetime.now() - manager.session_created.get(session_id, datetime.now())}")
        logger.info(f"Messages exchanged: {len(manager.conversation_history.get(session_id, []))}")
        
        # Show what will be cleared
        has_credentials = session_id in manager.session_credentials
        if has_credentials:
            logger.info(format_log("oauth_clearing"))
        
        logger.info("="*80)
        await manager.disconnect(session_id)
    except Exception as e:
        logger.error("="*80)
        logger.error(f"WEBSOCKET ERROR")
        logger.error(f"Session ID: {session_id}")
        logger.error(f"Error: {str(e)}")
        logger.error("="*80)
        await manager.disconnect(session_id)


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Veem API MCP WebSocket Server")
    logger.info("WebSocket endpoint: ws://localhost:8000/ws/{session_id}")
    logger.info("Health check: http://localhost:8000/health")
    uvicorn.run(application, host="0.0.0.0", port=8000, log_level="info")
