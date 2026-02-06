"""
Veem API MCP Server

This MCP server provides access to Veem API tools organized by category:
- Account tools: get_user_info
- Contact tools: get_payees
- Funding tools: get_payment_methods
- History tools: get_payment_history
- Payment tools: create_payment, schedule_payment
"""

import sys
import logging
from pathlib import Path

# Add parent directory (src/) to Python path to enable package imports
current_file = Path(__file__).resolve()
src_dir = current_file.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from dotenv import load_dotenv
from mcp_server.server_instance import mcp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import tool modules to register tools with the server
# Each module imports mcp from server_instance and registers its tools
logger.info("Loading tool modules...")
from mcp_server.tools import get_account
logger.info("✓ get_account loaded")
from mcp_server.tools import get_contacts
logger.info("✓ get_contacts loaded")
from mcp_server.tools import get_payment_methods
logger.info("✓ get_payment_methods loaded")
from mcp_server.tools import get_payment_history
logger.info("✓ get_payment_history loaded")
from mcp_server.tools import create_payment
logger.info("✓ create_payment loaded")
logger.info("All tool modules loaded successfully")


if __name__ == "__main__":
    mcp.run(transport='stdio')
