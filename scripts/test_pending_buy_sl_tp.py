#!/usr/bin/env python
"""
Test script for pending buy orders with stop loss and take profit.

This script tests placing both limit buy and stop buy orders with stop loss and take profit levels.
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
    """Test placing pending buy orders with stop loss and take profit."""
    # Load environment variables
    load_dotenv()
    
    logger.info("Starting test for pending buy orders with SL/TP")
    
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
        logger.info(f"Price data head:\n{price_data.head()}")
        
        latest_price = price_data.iloc[-1]
        logger.info(f"Latest price data: {latest_price.to_dict()}")
        
        # Check column names and use appropriate ones
        if 'close' in price_data.columns:
            close_col = 'close'
        elif 'Close' in price_data.columns:
            close_col = 'Close'
        else:
            # Try to find a column that might contain close price
            potential_cols = [col for col in price_data.columns if 'close' in col.lower()]
            if potential_cols:
                close_col = potential_cols[0]
            else:
                logger.error(f"Could not find close price column in {price_data.columns}")
                return
        
        if 'high' in price_data.columns:
            high_col = 'high'
        elif 'High' in price_data.columns:
            high_col = 'High'
        else:
            potential_cols = [col for col in price_data.columns if 'high' in col.lower()]
            if potential_cols:
                high_col = potential_cols[0]
            else:
                logger.error(f"Could not find high price column in {price_data.columns}")
                return
        
        if 'low' in price_data.columns:
            low_col = 'low'
        elif 'Low' in price_data.columns:
            low_col = 'Low'
        else:
            potential_cols = [col for col in price_data.columns if 'low' in col.lower()]
            if potential_cols:
                low_col = potential_cols[0]
            else:
                logger.error(f"Could not find low price column in {price_data.columns}")
                return
        
        logger.info(f"Using columns: close={close_col}, high={high_col}, low={low_col}")
        
        # Use the correct column names directly
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
    # For limit buy: price below current ask
    limit_buy_price = round(current_ask * 0.995, 5)  # 0.5% below current ask
    
    # For stop buy: price above current ask
    stop_buy_price = round(current_ask * 1.005, 5)  # 0.5% above current ask
    
    # Calculate SL/TP levels
    # For limit buy: SL below entry, TP above entry
    limit_buy_sl = round(limit_buy_price * 0.99, 5)  # 1% below entry
    limit_buy_tp = round(limit_buy_price * 1.02, 5)  # 2% above entry
    
    # For stop buy: SL below entry, TP above entry
    stop_buy_sl = round(stop_buy_price * 0.99, 5)  # 1% below entry
    stop_buy_tp = round(stop_buy_price * 1.02, 5)  # 2% above entry
    
    # Set expiry time (24 hours from now)
    expiry_time = datetime.now() + timedelta(days=1)
    
    try:
        # Test limit buy order with SL/TP
        logger.info(f"Testing LIMIT BUY order for {symbol} with price {limit_buy_price}")
        logger.info(f"Stop Loss: {limit_buy_sl}, Take Profit: {limit_buy_tp}")
        
        limit_buy_result = order_manager.place_pending_order(
            symbol=symbol,
            order_type=OrderType.LIMIT_BUY,
            volume=volume,
            price=limit_buy_price,
            stop_loss=limit_buy_sl,
            take_profit=limit_buy_tp,
            expiry=expiry_time,
            comment="Test limit buy with SL/TP"
        )
        
        logger.info(f"Limit buy order result: {limit_buy_result}")
        
        if limit_buy_result.get('success', False):
            logger.info("Limit buy order placed successfully")
        else:
            logger.error(f"Limit buy order failed: {limit_buy_result.get('error', 'Unknown error')}")
        
        # Wait a moment before placing the next order
        await asyncio.sleep(2)
        
        # Test stop buy order with SL/TP
        logger.info(f"Testing STOP BUY order for {symbol} with price {stop_buy_price}")
        logger.info(f"Stop Loss: {stop_buy_sl}, Take Profit: {stop_buy_tp}")
        
        stop_buy_result = order_manager.place_pending_order(
            symbol=symbol,
            order_type=OrderType.STOP_BUY,
            volume=volume,
            price=stop_buy_price,
            stop_loss=stop_buy_sl,
            take_profit=stop_buy_tp,
            expiry=expiry_time,
            comment="Test stop buy with SL/TP"
        )
        
        logger.info(f"Stop buy order result: {stop_buy_result}")
        
        if stop_buy_result.get('success', False):
            logger.info("Stop buy order placed successfully")
        else:
            logger.error(f"Stop buy order failed: {stop_buy_result.get('error', 'Unknown error')}")
        
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