#!/usr/bin/env python
"""
Example script to test the get_market_data function from DataAcquisitionManager.

This script demonstrates how to retrieve market data for a symbol using the
DataAcquisitionManager class and displays the results.
"""
import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import logging

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import project modules
from app.core.mt5_data import DataAcquisitionManager
from app.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)
logging.getLogger().setLevel(logging.INFO)

def test_get_market_data():
    """Test the get_market_data function with various parameters."""
    logger.info("Initializing DataAcquisitionManager...")
    data_manager = DataAcquisitionManager()
    
    # Define test parameters
    symbol = "EURUSD"  # Example symbol
    timeframe = "H1"   # 1-hour timeframe
    
    # Method 1: Time-based retrieval
    logger.info("Method 1: Time-based retrieval")
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)  # Get 7 days of data
    
    logger.info(f"Retrieving market data for {symbol}, timeframe: {timeframe}")
    logger.info(f"Time range: {start_time} to {end_time}")
    
    # Get market data using time-based parameters
    market_data_time = data_manager.get_market_data(
        symbol=symbol,
        timeframe=timeframe,
        start_time=start_time,
        end_time=end_time,
        include_volume=True
    )
    
    # Check if data was retrieved successfully
    if len(market_data_time) == 0:
        logger.error("No data retrieved using time-based parameters. Check connection to MetaTrader 5.")
    else:
        # Get the DataFrame from the MarketData object
        df_time = market_data_time.data
        
        # Display data information
        logger.info(f"Retrieved {len(market_data_time)} data points using time-based parameters")
        logger.info(f"Data range: {df_time.index.min()} to {df_time.index.max()}")
        
        # Display the first few rows
        print("\nData Sample (Time-based):")
        print(df_time.head())
        
        # Display basic statistics
        print("\nData Statistics (Time-based):")
        print(df_time.describe())
        
        # Plot the data
        plot_market_data(df_time, symbol, f"{timeframe}_time_based")
    
    # Method 2: Position-based retrieval
    logger.info("\nMethod 2: Position-based retrieval")
    start_pos = 0    # Current bar
    end_pos = 100    # Get 100 bars from the current bar
    
    logger.info(f"Retrieving market data for {symbol}, timeframe: {timeframe}")
    logger.info(f"Position range: {start_pos} to {end_pos}")
    
    # Get market data using position-based parameters
    market_data_pos = data_manager.get_market_data(
        symbol=symbol,
        timeframe=timeframe,
        start_pos=start_pos,
        end_pos=end_pos,
        include_volume=True
    )
    
    # Check if data was retrieved successfully
    if len(market_data_pos) == 0:
        logger.error("No data retrieved using position-based parameters. Check connection to MetaTrader 5.")
    else:
        # Get the DataFrame from the MarketData object
        df_pos = market_data_pos.data
        
        # Display data information
        logger.info(f"Retrieved {len(market_data_pos)} data points using position-based parameters")
        logger.info(f"Data range: {df_pos.index.min()} to {df_pos.index.max()}")
        
        # Display the first few rows
        print("\nData Sample (Position-based):")
        print(df_pos.head())
        
        # Display basic statistics
        print("\nData Statistics (Position-based):")
        print(df_pos.describe())
        
        # Plot the data
        plot_market_data(df_pos, symbol, f"{timeframe}_position_based")
    
    # Test MarketData specific methods
    if len(market_data_time) > 0:
        logger.info("\nTesting MarketData specific methods:")
        
        # Get latest bar
        latest_bar = market_data_time.get_latest_bar()
        if latest_bar is not None:
            logger.info(f"Latest bar: {latest_bar}")
        
        # Get latest close price
        latest_close = market_data_time.get_latest_close()
        if latest_close is not None:
            logger.info(f"Latest close price: {latest_close}")
        
        # Get data range
        subset_data = market_data_time.get_data_range(num_bars=10)
        logger.info(f"Last 10 bars: {len(subset_data)} records")
        
        # Check if data is fresh
        is_fresh = market_data_time.is_data_fresh()
        logger.info(f"Is data fresh? {is_fresh}")

def plot_market_data(df, symbol, timeframe_suffix):
    """
    Plot the market data using matplotlib and seaborn.
    
    Args:
        df (pd.DataFrame): Market data DataFrame
        symbol (str): Trading symbol
        timeframe_suffix (str): Timeframe with optional suffix for the filename
    """
    try:
        # Extract the base timeframe (e.g., "H1" from "H1_time_based")
        timeframe = timeframe_suffix.split('_')[0] if '_' in timeframe_suffix else timeframe_suffix
        
        # Set the style
        sns.set_style('darkgrid')
        
        # Create a figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
        
        # Plot price data on the first subplot
        ax1.plot(df.index, df['Close'], label='Close Price', color='blue')
        ax1.set_title(f'{symbol} - {timeframe} Timeframe')
        ax1.set_ylabel('Price')
        ax1.legend()
        ax1.grid(True)
        
        # Plot volume data on the second subplot
        if 'Volume' in df.columns:
            ax2.bar(df.index, df['Volume'], color='green', alpha=0.5)
            ax2.set_ylabel('Volume')
            ax2.grid(True)
        
        # Format the x-axis to show dates nicely
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save the plot
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'plots')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f'{symbol}_{timeframe_suffix}_market_data.png')
        plt.savefig(output_file)
        logger.info(f"Plot saved to {output_file}")
        
        # Show the plot
        plt.show()
        
    except Exception as e:
        logger.exception(f"Error plotting data: {str(e)}")

if __name__ == "__main__":
    try:
        test_get_market_data()
    except Exception as e:
        logger.exception(f"Error in test_get_market_data: {str(e)}") 