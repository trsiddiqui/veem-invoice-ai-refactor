"""
MCP Server Configuration

Settings for the Veem API server including database and API configuration.
"""

from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# MySQL database configuration for payment history
MY_SQL_PAYMENT_PARAMS = {
    'user': os.getenv('MY_SQL_USER'),
    'password': os.getenv('MY_SQL_PASSWORD'),
    'host': os.getenv('MY_SQL_HOST'),
    'database': os.getenv('MY_SQL_PAYMENT_DATABASE')
}

# Veem API base URL
VEEM_API_BASE_URL = "https://api.qa.veem.com/veem/v1.2"
