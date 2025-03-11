#!/usr/bin/env python
"""
Script to check MT5 constants.
"""
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import MetaTrader5 as mt5
from algotrader.integrations.mt5.client import MT5Client
from algotrader.utils.logger import get_logger

# Set up logging
logger = get_logger(__name__)

def main():
    """Check MT5 constants."""
    # Load environment variables
    load_dotenv()
    
    # Initialize MT5 client
    mt5_client = MT5Client()
    connection_result = mt5_client.connect()
    
    if not connection_result:
        logger.error("Failed to connect to MT5 terminal")
        return
    
    logger.info("Connected to MT5 terminal")
    
    # Print MT5 constants
    logger.info("MT5 Trade Action Constants:")
    
    # Check if constants exist
    constants_to_check = [
        "TRADE_ACTION_DEAL",
        "TRADE_ACTION_PENDING",
        "TRADE_ACTION_SLTP",
        "TRADE_ACTION_MODIFY",
        "TRADE_ACTION_REMOVE",
        "TRADE_ACTION_CLOSE_BY"
    ]
    
    for const_name in constants_to_check:
        try:
            const_value = getattr(mt5, const_name)
            logger.info(f"{const_name} = {const_value}")
        except AttributeError:
            logger.error(f"{const_name} is not defined in MT5 module")
    
    # Print order types
    logger.info("\nMT5 Order Type Constants:")
    order_types = [
        "ORDER_TYPE_BUY",
        "ORDER_TYPE_SELL",
        "ORDER_TYPE_BUY_LIMIT",
        "ORDER_TYPE_SELL_LIMIT",
        "ORDER_TYPE_BUY_STOP",
        "ORDER_TYPE_SELL_STOP",
        "ORDER_TYPE_BUY_STOP_LIMIT",
        "ORDER_TYPE_SELL_STOP_LIMIT"
    ]
    
    for order_type in order_types:
        try:
            type_value = getattr(mt5, order_type)
            logger.info(f"{order_type} = {type_value}")
        except AttributeError:
            logger.error(f"{order_type} is not defined in MT5 module")
    
    # Try to place a simple pending order and check the error
    logger.info("\nTesting pending order placement:")
    
    # Get a symbol
    symbol = "EURUSD"
    
    # Get current price
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        logger.error(f"Failed to get symbol info for {symbol}")
    else:
        current_price = symbol_info.ask
        logger.info(f"Current price for {symbol}: {current_price}")
        
        # Create a simple pending order request
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": 0.01,
            "type": mt5.ORDER_TYPE_BUY_LIMIT,
            "price": current_price * 0.99,  # 1% below current price
            "deviation": 10,
            "magic": 123456,
            "comment": "Test pending order",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Try to send the order
        result = mt5.order_send(request)
        
        if result is None:
            error = mt5.last_error()
            logger.error(f"Failed to send order. Error code: {error[0]}, Error description: {error[1]}")
        else:
            logger.info(f"Order result: {result}")
            logger.info(f"Order retcode: {result.retcode}")
            
            # Check if there's an error
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed with retcode: {result.retcode}, Comment: {result.comment}")

            # Print information about retcodes
            logger.info(f"TRADE_RETCODE_DONE = {mt5.TRADE_RETCODE_DONE}")
            logger.info(f"Result retcode = {result.retcode}")
            
            # Check if the order was successful
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info("Order was successful (TRADE_RETCODE_DONE)")
            else:
                logger.info(f"Order had a different retcode: {result.retcode}")
                
                # Check some common retcodes
                retcodes = {
                    "TRADE_RETCODE_REQUOTE": 10004,
                    "TRADE_RETCODE_REJECT": 10006,
                    "TRADE_RETCODE_DONE": 10009,
                    "TRADE_RETCODE_DONE_PARTIAL": 10010,
                    "TRADE_RETCODE_ERROR": 10013,
                    "TRADE_RETCODE_TIMEOUT": 10008,
                    "TRADE_RETCODE_INVALID": 10014,
                    "TRADE_RETCODE_INVALID_VOLUME": 10015,
                    "TRADE_RETCODE_INVALID_PRICE": 10016,
                    "TRADE_RETCODE_INVALID_STOPS": 10017,
                    "TRADE_RETCODE_MARKET_CLOSED": 10018,
                    "TRADE_RETCODE_NO_MONEY": 10019,
                    "TRADE_RETCODE_PRICE_CHANGED": 10020,
                    "TRADE_RETCODE_PRICE_OFF": 10021,
                    "TRADE_RETCODE_INVALID_EXPIRATION": 10022,
                    "TRADE_RETCODE_ORDER_CHANGED": 10023,
                    "TRADE_RETCODE_TOO_MANY_REQUESTS": 10024,
                    "TRADE_RETCODE_NO_CHANGES": 10025,
                    "TRADE_RETCODE_SERVER_DISABLES_AT": 10026,
                    "TRADE_RETCODE_CLIENT_DISABLES_AT": 10027,
                    "TRADE_RETCODE_LOCKED": 10028,
                    "TRADE_RETCODE_FROZEN": 10029,
                    "TRADE_RETCODE_INVALID_FILL": 10030,
                    "TRADE_RETCODE_CONNECTION": 10031,
                    "TRADE_RETCODE_ONLY_REAL": 10032,
                    "TRADE_RETCODE_LIMIT_ORDERS": 10033,
                    "TRADE_RETCODE_LIMIT_VOLUME": 10034,
                    "TRADE_RETCODE_INVALID_ORDER": 10035,
                    "TRADE_RETCODE_POSITION_CLOSED": 10036,
                    "TRADE_RETCODE_INVALID_CLOSE_VOLUME": 10038,
                    "TRADE_RETCODE_CLOSE_ORDER_EXIST": 10039,
                    "TRADE_RETCODE_LIMIT_POSITIONS": 10040,
                    "TRADE_RETCODE_REJECT_CANCEL": 10041,
                    "TRADE_RETCODE_LONG_ONLY": 10042,
                    "TRADE_RETCODE_SHORT_ONLY": 10043,
                    "TRADE_RETCODE_CLOSE_ONLY": 10044,
                }
                
                for name, code in retcodes.items():
                    if result.retcode == code:
                        logger.info(f"Retcode matches: {name}")
                        break
    
    # Disconnect from MT5
    mt5_client.disconnect()
    logger.info("Disconnected from MT5 terminal")

if __name__ == "__main__":
    main() 