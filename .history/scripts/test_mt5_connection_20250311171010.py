#!/usr/bin/env python
"""
Test script for MetaTrader 5 connection.

This script tests the connection to the MetaTrader 5 terminal
and displays account information if the connection is successful.
"""
import os
import sys
import logging
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import the MT5Connection class
from algotrader.integrations.mt5 import MT5Connection

def test_connection():
    """Test the connection to MetaTrader 5."""
    logger.info("Testing MT5 connection...")
    
    # Create a connection instance
    mt5_conn = MT5Connection()
    
    # Try to connect
    if not mt5_conn.connect():
        logger.error("Failed to connect to MT5")
        return False
    
    # Get account information
    account_info = mt5_conn.get_account_info()
    if account_info:
        logger.info("Connection successful!")
        logger.info("Account Information:")
        for key, value in account_info.items():
            logger.info(f"  {key}: {value}")
    else:
        logger.error("Failed to get account information")
        return False
    
    # Disconnect
    mt5_conn.disconnect()
    logger.info("MT5 connection test completed")
    return True

def main():
    """Main function."""
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception(f"Error testing MT5 connection: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 