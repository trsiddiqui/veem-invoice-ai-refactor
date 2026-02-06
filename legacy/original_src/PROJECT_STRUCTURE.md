# Project Structure

This document describes the organization of the Veem AI Agent codebase.

## Directory Layout

```
src/
├── application.py              # Main FastAPI application entry point
│
├── mcp_client/                 # MCP Client Package
│   ├── __init__.py
│   ├── agent_manager.py       # AI agent lifecycle management
│   ├── connection_manager.py  # WebSocket connection handling
│   ├── auth.py                # OAuth 2.0 authentication
│   ├── config.py              # Client configuration (model, MCP server)
│   └── prompts.py             # Agent instructions and templates
│
├── mcp_server/                 # MCP Server Package
│   ├── __init__.py
│   ├── veem_api_server.py     # FastMCP server with Veem API tools
│   └── config.py              # Server configuration (API, database)
│
├── shared/                     # Shared Utilities Package
│   ├── __init__.py
│   ├── payment_extraction.py  # Extract payment details from documents
│   ├── file_extraction.py     # File processing utilities
│   └── conversation_history.py # Conversation state management
│
├── tests/                      # Tests Package
│   ├── __init__.py
│   ├── test_oauth_connection.py
│   └── websocket_test_client.py
│
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
└── websocket_client*.html      # Web-based test clients
```

## Package Descriptions

### `mcp_client/` - MCP Client Logic

Handles the WebSocket server, AI agent management, and user interactions.

**Files:**
- `agent_manager.py` - Manages AI agent instances and MCP server connections
- `connection_manager.py` - WebSocket connection lifecycle and session management
- `auth.py` - OAuth 2.0 client credentials flow for Veem API
- `config.py` - Client settings (OpenAI model, MCP server path, conversation config)
- `prompts.py` - Agent instructions, message templates, and formatting utilities

**Key Responsibilities:**
- Accept WebSocket connections from users
- Authenticate users via OAuth
- Initialize and manage AI agents per session
- Process user messages and document uploads
- Maintain conversation history
- Send responses back to users

### `mcp_server/` - MCP Server Logic

Provides Veem API tools via the Model Context Protocol (MCP).

**Files:**
- `veem_api_server.py` - FastMCP server exposing Veem API tools
- `config.py` - Server settings (Veem API URL, MySQL database config)

**Available Tools:**
- `get_user_info` - Retrieve user account information
- `get_payees` - Get user's contacts/payees
- `get_payment_methods` - Get user's payment methods (banks, wallets)
- `get_payment_history` - Query payment history between payer and payee
- `create_payment` - Create a new payment
- `schedule_payment` - Schedule a payment for a future date

**Key Responsibilities:**
- Expose Veem API functionality as MCP tools
- Handle API authentication and requests
- Query MySQL database for payment history
- Standardize API responses
- Log all API interactions

### `shared/` - Shared Utilities

Common utilities used by both client and server.

**Files:**
- `payment_extraction.py` - Extract payment details from invoices/documents using OpenAI
- `file_extraction.py` - Process uploaded files (PDF, images)
- `conversation_history.py` - Manage conversation state and history

**Key Responsibilities:**
- Document processing and data extraction
- Conversation state management
- Shared utility functions

### `tests/` - Test Suite

Test files for various components.

**Files:**
- `test_oauth_connection.py` - Test OAuth authentication flow
- `websocket_test_client.py` - Test WebSocket connections

## Import Patterns

### From `application.py` (root level):
```python
from mcp_client.auth import AuthenticationService
from mcp_client.connection_manager import ConnectionManager
from mcp_client.prompts import get_welcome_message
```

### From `mcp_client/` modules:
```python
from mcp_client.config import MCP_SERVER_CONFIG, MODEL_CONFIG
from mcp_client.prompts import AGENT_INSTRUCTIONS
from mcp_client.agent_manager import AgentManager
from shared.payment_extraction import extract_payment_details
```

### From `mcp_server/` modules:
```python
from mcp_server.config import MY_SQL_PAYMENT_PARAMS, VEEM_API_BASE_URL
```

## Configuration Files

### `mcp_client/config.py`
- `MCP_SERVER_CONFIG` - Path to MCP server script
- `MODEL_CONFIG` - OpenAI model settings (name, temperature, etc.)
- `EXTRACTION_MODEL_CONFIG` - Model for document extraction
- `TOOL_DESCRIPTIONS` - Documentation for available tools
- `CONVERSATION_CONFIG` - Conversation history settings

### `mcp_server/config.py`
- `MY_SQL_PAYMENT_PARAMS` - MySQL database connection settings
- `VEEM_API_BASE_URL` - Veem API endpoint

## Data Flow

1. **User connects** → `application.py` → `ConnectionManager`
2. **OAuth authentication** → `AuthenticationService` → Veem OAuth API
3. **Agent initialization** → `AgentManager` → MCP Server subprocess
4. **User message** → `ConnectionManager` → `AgentManager` → AI Agent
5. **Tool call** → MCP Server → `veem_api_server.py` → Veem API
6. **Document upload** → `payment_extraction.py` → OpenAI API
7. **Response** → Agent → `ConnectionManager` → User

## Running the Application

```bash
cd src
python application.py
```

The application will:
1. Start the FastAPI WebSocket server on port 8000
2. Automatically spawn MCP server subprocesses as needed
3. Accept WebSocket connections at `ws://localhost:8000/ws/{session_id}`

## Environment Variables

Required in `.env`:
```env
# OpenAI (for AI agent and document extraction)
OPENAI_API_KEY=your_openai_api_key

# Veem OAuth (for testing)
VEEM_CLIENT_ID=your_client_id
VEEM_CLIENT_SECRET=your_client_secret

# MySQL (optional - for payment history)
MY_SQL_USER=your_mysql_user
MY_SQL_PASSWORD=your_mysql_password
MY_SQL_HOST=your_mysql_host
MY_SQL_PAYMENT_DATABASE=your_database
```

## Benefits of This Structure

1. **Clear Separation of Concerns**
   - Client logic isolated from server logic
   - Shared utilities in dedicated package

2. **Easy to Navigate**
   - Obvious where to find specific functionality
   - Package names clearly indicate purpose

3. **Scalable**
   - Can add new tools to `mcp_server/` without touching client
   - Can add new utilities to `shared/` for reuse

4. **Testable**
   - Each package can be tested independently
   - Tests organized in dedicated directory

5. **Maintainable**
   - Changes to MCP server don't affect client code
   - Configuration separated by concern
   - Clear import paths prevent circular dependencies
