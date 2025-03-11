#!/usr/bin/env python
"""
Test script for market order placement with stop loss and take profit.

This script tests the place_market_order function with stop loss and take profit parameters.
"""
import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import MetaTrader5 as mt5

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from algotrader.trader.trade import OrderManager, OrderType
from algotrader.integrations.mt5.client import MT5Client
from algotrader.config.settings import get_config
from algotrader.utils.logger import get_logger

# Set up logging
logger = get_logger(__name__)

async def main():
    """Test the place_market_order function with stop loss and take profit parameters."""
    # Load environment variables
    load_dotenv()
    
    logger.info("Starting market order test with stop loss and take profit")
    
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
        # Make sure the symbol is enabled in Market Watch
        if not mt5.symbol_select(symbol, True):
            error = mt5.last_error()
            logger.error(f"Failed to select symbol {symbol}. Error: {error}")
            return
        
        # Get current price for the symbol
        logger.info(f"Getting tick information for {symbol}")
        symbol_info_tick = mt5.symbol_info_tick(symbol)
        
        if symbol_info_tick is None:
            error = mt5.last_error()
            logger.error(f"Failed to get tick information for {symbol}. Error: {error}")
            return
        
        current_bid = symbol_info_tick.bid
        current_ask = symbol_info_tick.ask
        
        logger.info(f"Current price for {symbol}: Bid={current_bid}, Ask={current_ask}")
        
        # Calculate stop loss and take profit levels for buy order
        # For buy order: stop loss below current price, take profit above current price
        buy_stop_loss = round(current_ask - (0.0020), 5)  # 20 pips below ask price
        buy_take_profit = round(current_ask + (0.0030), 5)  # 30 pips above ask price
        
        logger.info(f"Buy order parameters: Entry={current_ask}, SL={buy_stop_loss}, TP={buy_take_profit}")
        
        # Test market buy order with stop loss and take profit
        logger.info(f"Testing market buy order for {symbol} with volume {volume}, SL={buy_stop_loss}, TP={buy_take_profit}")
        
        buy_result = order_manager.place_market_order(
            symbol=symbol,
            order_type=OrderType.MARKET_BUY,
            volume=volume,
            stop_loss=buy_stop_loss,
            take_profit=buy_take_profit,
            comment="Test market buy order with SL/TP"
        )
        
        logger.info(f"Market buy order result: {buy_result}")
        
        if buy_result.get('success', False):
            logger.info("Market buy order with SL/TP placed successfully")
            
            # Wait for notification to be sent
            logger.info("Waiting for notification to be sent...")
            await asyncio.sleep(3)
            
            # Calculate stop loss and take profit levels for sell order
            # For sell order: stop loss above current price, take profit below current price
            sell_stop_loss = round(current_bid + (0.0020), 5)  # 20 pips above bid price
            sell_take_profit = round(current_bid - (0.0030), 5)  # 30 pips below bid price
            
            logger.info(f"Sell order parameters: Entry={current_bid}, SL={sell_stop_loss}, TP={sell_take_profit}")
            
            # Test market sell order with stop loss and take profit
            logger.info(f"Testing market sell order for {symbol} with volume {volume}, SL={sell_stop_loss}, TP={sell_take_profit}")
            
            sell_result = order_manager.place_market_order(
                symbol=symbol,
                order_type=OrderType.MARKET_SELL,
                volume=volume,
                stop_loss=sell_stop_loss,
                take_profit=sell_take_profit,
                comment="Test market sell order with SL/TP"
            )
            
            logger.info(f"Market sell order result: {sell_result}")
            
            if sell_result.get('success', False):
                logger.info("Market sell order with SL/TP placed successfully")
                
                # Wait for notification to be sent
                logger.info("Waiting for notification to be sent...")
                await asyncio.sleep(3)
            else:
                logger.error(f"Market sell order failed: {sell_result.get('error', 'Unknown error')}")
        else:
            logger.error(f"Market buy order failed: {buy_result.get('error', 'Unknown error')}")
    
    except Exception as e:
        logger.exception(f"An error occurred during testing: {str(e)}")
    
    finally:
        # Ensure we disconnect from MT5 even if there's an error
        logger.info("Disconnecting from MT5 terminal")
        mt5_client.disconnect()
        logger.info("Disconnected from MT5 terminal")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 