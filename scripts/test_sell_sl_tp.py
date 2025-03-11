#!/usr/bin/env python
"""
Simple test script for market sell order with stop loss and take profit.

This script tests placing a market sell order with stop loss and take profit levels.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from algotrader.trader.trade import OrderManager, OrderType
from algotrader.config.settings import get_config
from algotrader.utils.logger import get_logger

# Set up logging
logger = get_logger(__name__)

async def main():
    """Test placing a market sell order with stop loss and take profit."""
    # Load environment variables
    load_dotenv()
    
    logger.info("Starting simple test for market sell order with SL/TP")
    
    # Get configuration
    config = get_config()
    
    # Initialize OrderManager
    order_manager = OrderManager()
    
    # Test parameters
    symbol = config['testing']['test_symbol']
    volume = config['testing']['test_volume']
    
    # Fixed stop loss and take profit levels for testing
    # These should be reasonable values for EURUSD
    # For a sell order: stop loss above current price, take profit below current price
    stop_loss = 1.0950  # Fixed stop loss level (above current price)
    take_profit = 1.0900  # Fixed take profit level (below current price)
    
    logger.info(f"Testing market sell order for {symbol} with volume {volume}")
    logger.info(f"Stop Loss: {stop_loss}, Take Profit: {take_profit}")
    
    try:
        # Place market sell order with stop loss and take profit
        result = order_manager.place_market_order(
            symbol=symbol,
            order_type=OrderType.MARKET_SELL,
            volume=volume,
            stop_loss=stop_loss,
            take_profit=take_profit,
            comment="Test sell order with SL/TP"
        )
        
        logger.info(f"Order result: {result}")
        
        if result.get('success', False):
            logger.info("Order placed successfully")
            
            # Wait for notification to be sent
            logger.info("Waiting for notification to be sent...")
            await asyncio.sleep(3)
        else:
            logger.error(f"Order failed: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 