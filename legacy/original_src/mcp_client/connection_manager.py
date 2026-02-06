"""
Connection Manager Module

Handles WebSocket connections, session management, conversation history,
and document upload processing.
"""

import os
import base64
import logging
import tempfile
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from fastapi import WebSocket
from openai import OpenAI

from shared.payment_extraction import extract_payment_details
from mcp_client.prompts import format_log
from mcp_client.agent_manager import AgentManager

load_dotenv(override=True)

# Initialize OpenAI client for file uploads
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ConnectionManager:
    """Manages WebSocket connections and session state."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.conversation_history: Dict[str, list] = {}
        self.session_created: Dict[str, datetime] = {}
        self.session_credentials: Dict[str, Dict[str, str]] = {}
        self.session_extracted_details: Dict[str, str] = {}
        self.agent_manager = AgentManager()
        self.logger = logging.getLogger(f"{__name__}.ConnectionManager")

    async def connect(self, websocket: WebSocket, session_id: str, auth_info: Dict[str, str]):
        """Accept and register a new WebSocket connection with authentication."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        # Initialize empty conversation history for this session
        self.conversation_history[session_id] = []
        
        self.session_created[session_id] = datetime.now()
        self.session_credentials[session_id] = auth_info
        
        self.logger.info(format_log(
            "connection",
            session_id=session_id,
            account_id=auth_info.get('account_id')
        ))

    async def disconnect(self, session_id: str):
        """Clean up connection data for a disconnected session."""
        # Clean up agent and MCP server
        await self.agent_manager.cleanup_session(session_id)
        
        # Explicitly clear sensitive credentials from memory
        if session_id in self.session_credentials:
            credentials = self.session_credentials[session_id]
            if 'access_token' in credentials:
                credentials['access_token'] = None
            if 'account_id' in credentials:
                credentials['account_id'] = None
            self.logger.info(format_log("credentials_cleared", session_id=session_id))
        
        # Clean up all session data
        cleanup_dicts = [
            self.active_connections,
            self.conversation_history,
            self.session_created,
            self.session_credentials
        ]
        
        for tracking_dict in cleanup_dicts:
            if session_id in tracking_dict:
                del tracking_dict[session_id]
        
        self.logger.info(format_log("disconnect", session_id=session_id))

    async def send_message(self, session_id: str, message: dict):
        """Send a JSON message to a specific session."""
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

    async def initialize_agent(self, session_id: str):
        """Initialize MCP server and agent for a session."""
        # Get credentials for this session
        credentials = self.session_credentials.get(session_id, {})
        account_id = credentials.get('account_id')
        access_token = credentials.get('access_token')
        
        # Pass credentials to agent manager (will be set in MCP subprocess env)
        await self.agent_manager.initialize_agent(session_id, account_id, access_token)

    def get_agent(self, session_id: str):
        """Get the agent for a session."""
        return self.agent_manager.get_agent(session_id)

    async def run_agent(
        self,
        session_id: str,
        user_message: str
    ) -> str:
        """Run agent with conversation history."""
        conversation_history = self.conversation_history.get(session_id, [])
        return await self.agent_manager.run_agent(
            session_id=session_id,
            user_message=user_message,
            conversation_history=conversation_history
        )

    def add_to_history(self, session_id: str, role: str, content: str):
        """Add a message to conversation history. Only saves user and assistant messages."""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        # Only save user questions and assistant responses (not system/status messages)
        if role in ["user", "assistant"]:
            self.conversation_history[session_id].append({"role": role, "content": content})
    
    def get_auth_info(self, session_id: str) -> Optional[Dict[str, str]]:
        """Get authentication information for a session."""
        return self.session_credentials.get(session_id)
    
    async def handle_document_upload(self, session_id: str, document_data: str, filename: str) -> dict:
        """Handle document upload and extract payment details."""
        try:
            # Decode base64 document data
            file_bytes = base64.b64decode(document_data)
            
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            temp_path = Path(temp_dir) / f"{session_id}_{filename}"
            
            with open(temp_path, 'wb') as f:
                f.write(file_bytes)
            
            self.logger.info(f"[{session_id}] Extracting payment details from: {filename}")
            
            # Extract payment details
            extraction_result = extract_payment_details(str(temp_path))
            
            # Clean up temp file
            temp_path.unlink()
            
            # Store extracted details
            self.session_extracted_details[session_id] = extraction_result
            
            self.logger.info(f"[{session_id}] Extraction successful: {extraction_result}")
            
            return {
                "success": True,
                "filename": filename,
                "extracted_details": extraction_result
            }
        
        except Exception as e:
            self.logger.error(f"[{session_id}] Document upload error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_extracted_details(self, session_id: str) -> Optional[str]:
        """Get extracted payment details for a session."""
        return self.session_extracted_details.get(session_id)
