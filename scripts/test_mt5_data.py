#!/usr/bin/env python
"""
Test script for MetaTrader 5 data retrieval.

This script tests the connection to the MetaTrader 5 terminal,
retrieves available symbols, and fetches recent price data.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import MetaTrader5 as mt5

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

def test_symbols(mt5_conn):
    """Test retrieving available symbols."""
    logger.info("Testing symbol retrieval...")
    
    # Get all symbols
    symbols = mt5.symbols_get()
    if not symbols:
        logger.error("Failed to get symbols")
        return False
    
    # Display the total number of symbols
    logger.info(f"Total symbols available: {len(symbols)}")
    
    # Display the first 5 forex symbols
    forex_symbols = [s.name for s in symbols if s.name.endswith('USD') or 'USD' in s.name][:5]
    logger.info(f"Sample forex symbols: {forex_symbols}")
    
    return True

def test_market_data(mt5_conn, symbol="EURUSD", timeframe=mt5.TIMEFRAME_M5, bars=10):
    """Test retrieving market data."""
    logger.info(f"Testing market data retrieval for {symbol}...")
    
    # Define time range
    to_date = datetime.now()
    from_date = to_date - timedelta(days=1)
    
    # Get historical data
    rates = mt5.copy_rates_range(
        symbol,
        timeframe,
        from_date,
        to_date
    )
    
    if rates is None or len(rates) == 0:
        logger.error(f"Failed to get market data for {symbol}")
        return False
    
    # Convert to pandas DataFrame
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Display the data
    logger.info(f"Retrieved {len(df)} bars for {symbol}")
    logger.info(f"Last {min(bars, len(df))} bars:")
    pd.set_option('display.max_columns', 10)
    pd.set_option('display.width', 1000)
    logger.info(f"\n{df.tail(bars)}")
    
    return True

def test_tick_data(mt5_conn, symbol="EURUSD", ticks=10):
    """Test retrieving tick data."""
    logger.info(f"Testing tick data retrieval for {symbol}...")
    
    # Get the last N ticks
    ticks_data = mt5.copy_ticks_from(
        symbol,
        datetime.now() - timedelta(minutes=5),
        ticks,
        mt5.COPY_TICKS_ALL
    )
    
    if ticks_data is None or len(ticks_data) == 0:
        logger.error(f"Failed to get tick data for {symbol}")
        return False
    
    # Convert to pandas DataFrame
    df = pd.DataFrame(ticks_data)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Display the data
    logger.info(f"Retrieved {len(df)} ticks for {symbol}")
    logger.info(f"Last {min(ticks, len(df))} ticks:")
    pd.set_option('display.max_columns', 10)
    pd.set_option('display.width', 1000)
    logger.info(f"\n{df}")
    
    return True

def main():
    """Main function."""
    try:
        logger.info("Testing MT5 connection and data retrieval...")
        
        # Create a connection instance
        mt5_conn = MT5Connection()
        
        # Try to connect
        if not mt5_conn.connect():
            logger.error("Failed to connect to MT5")
            sys.exit(1)
        
        # Get account information
        account_info = mt5_conn.get_account_info()
        if account_info:
            logger.info("Connection successful!")
            logger.info("Account Information:")
            for key, value in account_info.items():
                logger.info(f"  {key}: {value}")
        else:
            logger.error("Failed to get account information")
            sys.exit(1)
        
        # Test symbols
        if not test_symbols(mt5_conn):
            sys.exit(1)
        
        # Test market data
        if not test_market_data(mt5_conn):
            sys.exit(1)
        
        # Test tick data
        if not test_tick_data(mt5_conn):
            sys.exit(1)
        
        # Disconnect
        mt5_conn.disconnect()
        logger.info("MT5 data retrieval test completed successfully")
        sys.exit(0)
        
    except Exception as e:
        logger.exception(f"Error testing MT5 data retrieval: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 