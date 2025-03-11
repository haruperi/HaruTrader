#!/usr/bin/env python
"""
Comprehensive example of using the logger in a real-world scenario.
Demonstrates logging in different functions and modules.
"""

import logging
import os
import sys
import time
import random
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Get base directory
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = os.getenv('LOG_DIR', str(BASE_DIR / 'logs'))

# Create logs directory if it doesn't exist
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

def setup_logger(name="example", log_level=logging.DEBUG):
    """Set up and return a logger instance."""
    logger = logging.getLogger(name)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
        
    logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)
    
    # File handler
    log_file = Path(LOG_DIR) / f"{name}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
    
    return logger

# Create a main logger
logger = setup_logger("trading_app")

# Create module-specific loggers
data_logger = setup_logger("trading_app.data")
strategy_logger = setup_logger("trading_app.strategy")
execution_logger = setup_logger("trading_app.execution")

class DataFetcher:
    """Example class for fetching market data."""
    
    def __init__(self):
        self.logger = data_logger
        self.logger.info("DataFetcher initialized")
        
    def fetch_data(self, symbol):
        """Simulate fetching market data."""
        self.logger.debug(f"Fetching data for {symbol}")
        
        # Simulate API call
        time.sleep(0.5)
        
        # Simulate occasional errors
        if random.random() < 0.2:
            self.logger.error(f"Failed to fetch data for {symbol}")
            return None
            
        price = round(random.uniform(100, 200), 2)
        self.logger.info(f"Fetched price for {symbol}: ${price}")
        return price

class TradingStrategy:
    """Example class for a trading strategy."""
    
    def __init__(self):
        self.logger = strategy_logger
        self.logger.info("TradingStrategy initialized")
        
    def analyze(self, symbol, price):
        """Analyze market data and generate signals."""
        if price is None:
            self.logger.warning(f"Cannot analyze {symbol} - no price data")
            return None
            
        self.logger.debug(f"Analyzing {symbol} at ${price}")
        
        # Simple strategy: buy if price < 150, sell if price > 150
        if price < 150:
            signal = "BUY"
        else:
            signal = "SELL"
            
        self.logger.info(f"Generated {signal} signal for {symbol} at ${price}")
        return signal

class OrderExecutor:
    """Example class for executing trading orders."""
    
    def __init__(self):
        self.logger = execution_logger
        self.logger.info("OrderExecutor initialized")
        
    def execute_order(self, symbol, signal, price):
        """Execute a trading order."""
        if signal is None:
            self.logger.warning(f"Cannot execute order for {symbol} - no signal")
            return False
            
        self.logger.debug(f"Executing {signal} order for {symbol} at ${price}")
        
        # Simulate order execution
        time.sleep(0.3)
        
        # Simulate occasional execution failures
        if random.random() < 0.1:
            self.logger.error(f"Failed to execute {signal} order for {symbol}")
            return False
            
        self.logger.info(f"Successfully executed {signal} order for {symbol} at ${price}")
        return True

def run_trading_cycle(symbols):
    """Run a complete trading cycle for a list of symbols."""
    logger.info("Starting trading cycle")
    
    data_fetcher = DataFetcher()
    strategy = TradingStrategy()
    executor = OrderExecutor()
    
    successful_trades = 0
    failed_trades = 0
    
    for symbol in symbols:
        logger.debug(f"Processing {symbol}")
        
        # Fetch data
        price = data_fetcher.fetch_data(symbol)
        
        # Generate signal
        signal = strategy.analyze(symbol, price)
        
        # Execute order
        if price is not None and signal is not None:
            success = executor.execute_order(symbol, signal, price)
            if success:
                successful_trades += 1
            else:
                failed_trades += 1
    
    logger.info(f"Trading cycle completed. Successful trades: {successful_trades}, Failed trades: {failed_trades}")
    return successful_trades, failed_trades

if __name__ == "__main__":
    # List of symbols to trade
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    
    logger.info("=== Trading Application Started ===")
    
    try:
        # Run multiple trading cycles
        for cycle in range(3):
            logger.info(f"Running trading cycle {cycle+1}")
            successful, failed = run_trading_cycle(symbols)
            
            # Log summary statistics
            total = successful + failed
            success_rate = (successful / total) * 100 if total > 0 else 0
            logger.info(f"Cycle {cycle+1} success rate: {success_rate:.2f}%")
            
            # Simulate time between cycles
            time.sleep(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {str(e)}", exc_info=True)
    finally:
        logger.info("=== Trading Application Stopped ===")
        
    print(f"Execution completed. Check the logs at: {LOG_DIR}") 