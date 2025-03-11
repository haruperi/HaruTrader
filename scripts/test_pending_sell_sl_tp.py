#!/usr/bin/env python
"""
Test script for pending sell orders with stop loss and take profit.

This script tests placing both limit sell and stop sell orders with stop loss and take profit levels.
"""
import os
import sys
import asyncio
from datetime import datetime, timedelta
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
    """Test placing pending sell orders with stop loss and take profit."""
    # Load environment variables
    load_dotenv()
    
    logger.info("Starting test for pending sell orders with SL/TP")
    
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
    
    # Get current price
    try:
        # Get the latest price data (1 minute timeframe, 1 bar)
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=1)
        
        # Use the MT5Client to get the latest price data
        price_data = mt5_client.get_rates(
            symbol=symbol,
            timeframe="M1",
            start_time=start_time,
            end_time=end_time,
            include_volume=False
        )
        
        if price_data.empty:
            logger.error(f"Failed to get price data for {symbol}")
            return
        
        # Get the latest price
        logger.info(f"Price data columns: {price_data.columns.tolist()}")
        logger.info(f"Price data shape: {price_data.shape}")
        
        latest_price = price_data.iloc[-1]
        logger.info(f"Latest price data: {latest_price.to_dict()}")
        
        # Use the correct column names
        close_col = 'Close'
        high_col = 'High'
        low_col = 'Low'
        
        current_ask = latest_price[close_col] + (latest_price[high_col] - latest_price[low_col]) * 0.1  # Approximate ask
        current_bid = latest_price[close_col] - (latest_price[high_col] - latest_price[low_col]) * 0.1  # Approximate bid
        
        logger.info(f"Current price for {symbol}: Ask={current_ask}, Bid={current_bid}")
    except Exception as e:
        logger.exception(f"Error getting price data: {str(e)}")
        return
    
    # Calculate prices for pending orders
    # For limit sell: price above current bid
    limit_sell_price = round(current_bid * 1.005, 5)  # 0.5% above current bid
    
    # For stop sell: price below current bid
    stop_sell_price = round(current_bid * 0.995, 5)  # 0.5% below current bid
    
    # Calculate SL/TP levels
    # For limit sell: SL above entry, TP below entry
    limit_sell_sl = round(limit_sell_price * 1.01, 5)  # 1% above entry
    limit_sell_tp = round(limit_sell_price * 0.98, 5)  # 2% below entry
    
    # For stop sell: SL above entry, TP below entry
    stop_sell_sl = round(stop_sell_price * 1.01, 5)  # 1% above entry
    stop_sell_tp = round(stop_sell_price * 0.98, 5)  # 2% below entry
    
    # Set expiry time (24 hours from now)
    expiry_time = datetime.now() + timedelta(days=1)
    
    try:
        # Test limit sell order with SL/TP
        logger.info(f"Testing LIMIT SELL order for {symbol} with price {limit_sell_price}")
        logger.info(f"Stop Loss: {limit_sell_sl}, Take Profit: {limit_sell_tp}")
        
        limit_sell_result = order_manager.place_pending_order(
            symbol=symbol,
            order_type=OrderType.LIMIT_SELL,
            volume=volume,
            price=limit_sell_price,
            stop_loss=limit_sell_sl,
            take_profit=limit_sell_tp,
            expiry=expiry_time,
            comment="Test limit sell with SL/TP"
        )
        
        logger.info(f"Limit sell order result: {limit_sell_result}")
        
        if limit_sell_result.get('success', False):
            logger.info("Limit sell order placed successfully")
        else:
            logger.error(f"Limit sell order failed: {limit_sell_result.get('error', 'Unknown error')}")
        
        # Wait a moment before placing the next order
        await asyncio.sleep(2)
        
        # Test stop sell order with SL/TP
        logger.info(f"Testing STOP SELL order for {symbol} with price {stop_sell_price}")
        logger.info(f"Stop Loss: {stop_sell_sl}, Take Profit: {stop_sell_tp}")
        
        stop_sell_result = order_manager.place_pending_order(
            symbol=symbol,
            order_type=OrderType.STOP_SELL,
            volume=volume,
            price=stop_sell_price,
            stop_loss=stop_sell_sl,
            take_profit=stop_sell_tp,
            expiry=expiry_time,
            comment="Test stop sell with SL/TP"
        )
        
        logger.info(f"Stop sell order result: {stop_sell_result}")
        
        if stop_sell_result.get('success', False):
            logger.info("Stop sell order placed successfully")
        else:
            logger.error(f"Stop sell order failed: {stop_sell_result.get('error', 'Unknown error')}")
        
        # Wait for notifications to be sent
        logger.info("Waiting for notifications to be sent...")
        await asyncio.sleep(3)
    
    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")
    
    finally:
        # Ensure we disconnect from MT5 even if there's an error
        logger.info("Disconnecting from MT5 terminal")
        mt5_client.disconnect()
        logger.info("Disconnected from MT5 terminal")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 