"""
Authentication service for Veem API MCP.

This module handles client authentication using OAuth 2.0 client credentials flow
with the Veem API.
"""

import json
import logging
import requests
from typing import Dict, Optional
from datetime import datetime
from requests.auth import HTTPBasicAuth


class AuthenticationService:
    """Handles client authentication using client_id and client_secret."""
    
    def __init__(self, oauth_url: str = "https://api.qa.veem.com/oauth/token"):
        """
        Initialize the authentication service.
        
        Args:
            oauth_url: The OAuth token endpoint URL (default: Veem QA environment)
        """
        self.oauth_url = oauth_url
        self.logger = logging.getLogger(f"{__name__}.AuthenticationService")
    
    async def authenticate(self, client_id: str, client_secret: str) -> Optional[Dict[str, str]]:
        """
        Authenticate client credentials with Veem OAuth API.
        
        Args:
            client_id: Client ID for authentication
            client_secret: Client secret for authentication
            
        Returns:
            Dictionary with account_id, access_token, and other auth info if successful, None otherwise
        """
        try:
            if not client_id or not client_secret:
                self.logger.warning("Missing client_id or client_secret")
                return None
            
            self.logger.info(f"Authenticating client: {client_id}")
            
            params = {
                "grant_type": "client_credentials",
                "scope": "all",
            }

            # Call Veem OAuth API
            self.logger.info(f"Calling Veem OAuth API: {self.oauth_url}")
            response = requests.post(
                self.oauth_url,
                params=params,
                auth=HTTPBasicAuth(client_id, client_secret),
                timeout=10
            )
            
            # Check response status
            if response.status_code != 200:
                self.logger.error(
                    f"Authentication failed with status {response.status_code}: {response.text}"
                )
                return None
            
            # Parse response
            auth_data = response.json()
            
            # Extract required fields
            auth_result = {
                "account_id": str(auth_data.get("account_id")),
                "access_token": auth_data.get("access_token"),
                "token_type": auth_data.get("token_type", "bearer"),
                "expires_in": auth_data.get("expires_in"),
                "scope": auth_data.get("scope"),
                "user_id": auth_data.get("user_id"),
                "user_name": auth_data.get("user_name"),
                "authenticated_at": datetime.now().isoformat()
            }
            
            self.logger.info(
                f"Authentication successful for client: {client_id}, "
                f"account_id: {auth_result['account_id']}, "
                f"user_id: {auth_result['user_id']}"
            )
            
            return auth_result
            
        except requests.RequestException as e:
            self.logger.error(f"Network error during authentication: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse authentication response: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected authentication error: {str(e)}")
            return None
    
    def validate_credentials(self, client_id: str, client_secret: str) -> bool:
        """
        Validate that credentials are properly formatted.
        
        Args:
            client_id: Client ID to validate
            client_secret: Client secret to validate
            
        Returns:
            True if credentials are valid format, False otherwise
        """
        return bool(client_id and client_secret and 
                   len(client_id) > 0 and len(client_secret) > 0)
