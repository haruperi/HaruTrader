#!/usr/bin/env python
"""
Test script for market sell order placement.

This script tests the place_market_order function with a MARKET_SELL order type.
"""
import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from algotrader.trader.trade import OrderManager, OrderType
from algotrader.integrations.mt5.client import MT5Client
from algotrader.config.settings import get_config
from algotrader.utils.logger import get_logger

# Set up logging
logger = get_logger(__name__)

async def main():
    """Test the place_market_order function with a MARKET_SELL order."""
    # Load environment variables
    load_dotenv()
    
    logger.info("Starting market sell order test")
    
    # Initialize MT5 client
    mt5_client = MT5Client()
    connection_result = mt5_client.connect()
    
    if not connection_result:
        logger.error("Failed to connect to MT5 terminal")
        return
    
    logger.info("Connected to MT5 terminal")
    
    # Get configuration
    config = get_config()
    
    # Initialize OrderManager
    order_manager = OrderManager()
    
    # Test parameters
    symbol = config['testing']['test_symbol']
    volume = config['testing']['test_volume']
    
    try:
        # Test market sell order
        logger.info(f"Testing market sell order for {symbol} with volume {volume}")
        
        sell_result = order_manager.place_market_order(
            symbol=symbol,
            order_type=OrderType.MARKET_SELL,
            volume=volume,
            comment="Test market sell order"
        )
        
        logger.info(f"Market sell order result: {sell_result}")
        
        if sell_result.get('success', False):
            logger.info("Market sell order placed successfully")
            
            # Wait for notification to be sent
            logger.info("Waiting for notification to be sent...")
            await asyncio.sleep(3)
        else:
            logger.error(f"Market sell order failed: {sell_result.get('error', 'Unknown error')}")
    
    finally:
        # Ensure we disconnect from MT5 even if there's an error
        logger.info("Disconnecting from MT5 terminal")
        mt5_client.disconnect()
        logger.info("Disconnected from MT5 terminal")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 