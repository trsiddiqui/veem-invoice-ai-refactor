"""
Agent Manager Module

Handles agent initialization, lifecycle, and execution.
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from agents import Agent, Runner, trace, ModelSettings
from agents.mcp import MCPServerStdio
from mcp_client.prompts import AGENT_INSTRUCTIONS, format_credentials_context, format_log
from mcp_client.config import MCP_SERVER_CONFIG, MODEL_CONFIG


class AgentManager:
    """Manages agent instances and their associated MCP servers."""
    
    def __init__(self):
        self.session_agents: Dict[str, Agent] = {}
        self.session_mcp_servers: Dict[str, MCPServerStdio] = {}
        self.logger = logging.getLogger(f"{__name__}.AgentManager")
    
    async def initialize_agent(self, session_id: str, account_id: str = None, access_token: str = None) -> Agent:
        """
        Initialize MCP server and agent for a session.
        
        Args:
            session_id: Unique session identifier
            account_id: User's account ID (passed to MCP server via env)
            access_token: OAuth access token (passed to MCP server via env)
            
        Returns:
            Agent: Initialized agent instance
        """
        if session_id not in self.session_mcp_servers:
            # Prepare environment variables for MCP server subprocess
            import os
            mcp_env = os.environ.copy()
            if account_id:
                mcp_env['VEEM_SESSION_ACCOUNT_ID'] = str(account_id)
            if access_token:
                mcp_env['VEEM_SESSION_ACCESS_TOKEN'] = access_token
            
            # Create MCP server config with environment
            mcp_config = MCP_SERVER_CONFIG.copy()
            mcp_config['env'] = mcp_env
            
            # Create MCP server context
            mcp_server = MCPServerStdio(
                params=mcp_config,
                client_session_timeout_seconds=60
            )
            await mcp_server.__aenter__()
            
            # Create agent with model settings
            model_settings = ModelSettings(**MODEL_CONFIG.get("model_kwargs", {}))
            agent = Agent(
                name="veem_api_agent",
                instructions=AGENT_INSTRUCTIONS,
                model=MODEL_CONFIG["name"],
                mcp_servers=[mcp_server],
                model_settings=model_settings
            )
            
            self.session_mcp_servers[session_id] = mcp_server
            self.session_agents[session_id] = agent
            
            self.logger.info(format_log("agent_initialized", session_id=session_id))
            
            return agent
        
        return self.session_agents[session_id]
    
    def get_agent(self, session_id: str) -> Optional[Agent]:
        """
        Get agent for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Optional[Agent]: Agent instance or None if not found
        """
        return self.session_agents.get(session_id)
    
    async def run_agent(
        self,
        session_id: str,
        user_message: str,
        conversation_history: list
    ) -> str:
        """
        Run agent with context and return response.
        
        Args:
            session_id: Unique session identifier
            user_message: User's input message
            conversation_history: List of previous messages
            
        Returns:
            str: Agent's response
        """
        agent = self.get_agent(session_id)
        
        if not agent:
            raise ValueError(f"Agent not initialized for session {session_id}")
        
        # Build context message with conversation history
        context_parts = []
        
        # Add conversation history
        if conversation_history:
            context_parts.append("Previous conversation:")
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                context_parts.append(f"{role}: {content}")
        
        # Add current message
        context_parts.append(f"\nCurrent message: {user_message}")
        
        context_message = "\n".join(context_parts)
        
        with trace("user_query"):
            result = await Runner.run(
                starting_agent=agent,
                input=context_message
            )
            
            return result.final_output
    
    async def cleanup_session(self, session_id: str):
        """
        Clean up agent and MCP server for a session.
        
        Args:
            session_id: Unique session identifier
        """
        # Close MCP server if exists
        if session_id in self.session_mcp_servers:
            try:
                await self.session_mcp_servers[session_id].__aexit__(None, None, None)
                self.logger.info(f"[{session_id}] MCP server closed")
            except Exception as e:
                self.logger.error(f"Error closing MCP server for {session_id}: {e}")
        
        # Remove from tracking
        if session_id in self.session_agents:
            del self.session_agents[session_id]
        if session_id in self.session_mcp_servers:
            del self.session_mcp_servers[session_id]
        
        self.logger.info(format_log("agent_cleanup", session_id=session_id))
