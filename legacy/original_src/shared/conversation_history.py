"""
Conversation History Management

This module handles persistent storage and retrieval of conversation history
for the Veem API MCP WebSocket server.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# Conversation history storage directory
CONVERSATION_HISTORY_DIR = Path("./conversation_history")
CONVERSATION_HISTORY_DIR.mkdir(exist_ok=True)


def get_history_file_path(account_id: str) -> Path:
    """Get the file path for a user's conversation history."""
    # Use account_id as the filename (sanitize it)
    safe_account_id = "".join(c for c in account_id if c.isalnum())
    return CONVERSATION_HISTORY_DIR / f"{safe_account_id}.json"


def save_conversation_history(account_id: str, history: List[Dict]) -> None:
    """Save conversation history to a file."""
    try:
        file_path = get_history_file_path(account_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                "account_id": account_id,
                "last_updated": datetime.now().isoformat(),
                "messages": history
            }, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved conversation history for account {account_id}")
    except Exception as e:
        logger.error(f"Error saving conversation history for {account_id}: {e}")


def load_conversation_history(account_id: str) -> List[Dict]:
    """Load conversation history from a file."""
    try:
        file_path = get_history_file_path(account_id)
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                messages = data.get("messages", [])
                logger.info(f"Loaded {len(messages)} messages from history for account {account_id}")
                return messages
        else:
            logger.debug(f"No existing history file for account {account_id}")
            return []
    except Exception as e:
        logger.error(f"Error loading conversation history for {account_id}: {e}")
        return []
