# Veem User Info MCP Project

This project implements a Model Context Protocol (MCP) server and client for retrieving Veem user account information.

## Project Structure

```
veem_user_info_mcp/
├── veem_user_info_server.py  # MCP server with get_user_info tool
├── application.py              # Client application with multiple modes
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variable template
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## Features

- **MCP Server**: Exposes the `get_user_info` tool via the Model Context Protocol
- **Client Application**: Three modes of operation:
  - `list`: Display available tools
  - `interactive`: Chat-based interface for querying user info
  - `example`: Run a predefined example query

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or using uv:

```bash
uv pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add:
- `VEEM_ACCESS_TOKEN`: Your Veem API access token
- `VEEM_ACCOUNT_ID`: Your Veem account ID
- `OPENAI_API_KEY`: Your OpenAI API key (for the agent)

## Usage

### List Available Tools

```bash
python application.py list
```

This will display all tools available from the MCP server.

### Interactive Mode (Default)

```bash
python application.py interactive
# or simply
python application.py
```

This starts an interactive chat session where you can ask questions about user accounts.

Example queries:
- "Get user information for account ID 12345 using the access token from environment"
- "What information can you retrieve about a user?"

### Run Example

```bash
python application.py example
```

Runs a predefined example query (you'll need to modify the account ID in the code).

## MCP Server Details

### Tool: `get_user_info`

**Description**: Get user information given the account id.

**Parameters**:
- `accountId` (int): The ID of the user account to retrieve information for
- `accessToken` (str): The access token for authentication

**Returns**: JSON string containing:
```json
{
  "data": {
    "status": "success",
    "response": { /* Veem API response */ }
  },
  "errors": [],
  "tool": "get_user_info"
}
```

**Error Response**:
```json
{
  "data": null,
  "errors": ["error message"],
  "tool": "get_user_info"
}
```

## API Endpoint

The server calls the Veem QA API:
```
GET https://api.qa.veem.com/veem/v1.2/account/{accountId}
```

## Logging

The server includes comprehensive logging:
- Request details (method, URL, headers with redacted tokens)
- Response details (status code, body)
- Error information

## Architecture

### MCP Server (`veem_user_info_server.py`)

- Built with `fastmcp` library
- Implements the `get_user_info` tool
- Handles API requests to Veem
- Provides standardized responses
- Includes error handling and logging

### Client Application (`application.py`)

- Uses the `agents` library with MCP support
- Creates an AI agent that can use the MCP server tools
- Supports multiple interaction modes
- Handles tracing for debugging

## Development

### Running the Server Standalone

```bash
uv run veem_user_info_server.py
```

The server runs in stdio mode and communicates via standard input/output.

### Testing the Tool

You can test the tool by running the client in interactive mode and asking it to retrieve user information.

## Security Notes

- Access tokens are redacted in logs
- Never commit `.env` file to version control
- Use environment variables for sensitive data
- The server uses HTTPS for API communication

## Troubleshooting

### "Command not found: uv"

Install uv:
```bash
pip install uv
```

### "Invalid access token"

Ensure your `VEEM_ACCESS_TOKEN` in `.env` is valid and not expired.

### "Connection timeout"

The client has a 60-second timeout. If the server takes longer, increase the `client_session_timeout_seconds` parameter.

## Future Enhancements

- Add more Veem API tools (contacts, payments, etc.)
- Implement caching for frequently accessed data
- Add resource endpoints for account data
- Support batch operations
- Add unit tests

## License

[Your License Here]

## Contact

[Your Contact Information]
