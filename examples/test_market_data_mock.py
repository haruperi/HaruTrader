#!/usr/bin/env python
"""
Example script to test the get_market_data function with mock data.

This script demonstrates how to test the DataAcquisitionManager's data processing
capabilities without requiring an actual MetaTrader 5 connection.
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from unittest.mock import patch, MagicMock

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import project modules
from algotrader.controller.data_acquisition import DataAcquisitionManager
from algotrader.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)
logging.getLogger().setLevel(logging.INFO)

def generate_mock_market_data(symbol, timeframe, start_time, end_time):
    """
    Generate mock market data for testing.
    
    Args:
        symbol (str): Trading symbol
        timeframe (str): Timeframe
        start_time (datetime): Start time
        end_time (datetime): End time
        
    Returns:
        pd.DataFrame: Mock market data
    """
    # Calculate number of periods based on timeframe
    if timeframe == 'M1':
        freq = 'T'  # minute
        periods = int((end_time - start_time).total_seconds() / 60)
    elif timeframe == 'M5':
        freq = '5T'  # 5 minutes
        periods = int((end_time - start_time).total_seconds() / 300)
    elif timeframe == 'M15':
        freq = '15T'  # 15 minutes
        periods = int((end_time - start_time).total_seconds() / 900)
    elif timeframe == 'M30':
        freq = '30T'  # 30 minutes
        periods = int((end_time - start_time).total_seconds() / 1800)
    elif timeframe == 'H1':
        freq = 'h'  # hour (using 'h' instead of 'H' to avoid deprecation warning)
        periods = int((end_time - start_time).total_seconds() / 3600)
    elif timeframe == 'H4':
        freq = '4h'  # 4 hours
        periods = int((end_time - start_time).total_seconds() / 14400)
    elif timeframe == 'D1':
        freq = 'D'  # day
        periods = (end_time - start_time).days
    else:
        freq = 'h'  # default to hourly
        periods = int((end_time - start_time).total_seconds() / 3600)
    
    # Generate datetime index
    date_range = pd.date_range(start=start_time, periods=periods, freq=freq)
    
    # Generate random price data with a trend
    np.random.seed(42)  # For reproducibility
    
    # Start price
    start_price = 1.2000 if symbol.startswith('EUR') else 100.0
    
    # Generate price with random walk and some trend
    price_changes = np.random.normal(0, 0.001, periods).cumsum()
    trend = np.linspace(0, 0.05, periods)  # Add a slight upward trend
    
    close_prices = start_price + price_changes + trend
    
    # Generate OHLC data
    high_prices = close_prices + np.random.uniform(0.001, 0.005, periods)
    low_prices = close_prices - np.random.uniform(0.001, 0.005, periods)
    open_prices = close_prices - np.random.normal(0, 0.002, periods)
    
    # Generate volume data
    volumes = np.random.randint(100, 1000, periods)
    
    # Create DataFrame
    df = pd.DataFrame({
        'DateTime': date_range,
        'Open': open_prices,
        'High': high_prices,
        'Low': low_prices,
        'Close': close_prices,
        'Volume': volumes
    })
    
    # Set DateTime as index
    df.set_index('DateTime', inplace=True)
    
    # Add some missing values for testing
    mask = np.random.random(len(df)) < 0.05  # 5% of data will be NaN
    df.loc[mask, 'Close'] = np.nan
    
    # Add some outliers for testing
    outlier_mask = np.random.random(len(df)) < 0.02  # 2% of data will be outliers
    df.loc[outlier_mask, 'Volume'] = df.loc[outlier_mask, 'Volume'] * 10
    
    return df

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
        ax1.set_title(f'{symbol} - {timeframe} Timeframe (Mock Data)')
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
        output_file = os.path.join(output_dir, f'{symbol}_{timeframe_suffix}_mock_data.png')
        plt.savefig(output_file)
        logger.info(f"Plot saved to {output_file}")
        
        # Show the plot
        plt.show()
        
    except Exception as e:
        logger.exception(f"Error plotting data: {str(e)}")

def test_get_market_data_with_mock():
    """Test the get_market_data function with mock data."""
    logger.info("Testing get_market_data with mock data...")
    
    # Define test parameters
    symbol = "EURUSD"
    timeframe = "H1"
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    # Method 1: Time-based retrieval
    logger.info("Method 1: Time-based retrieval with mock data")
    logger.info(f"Generating mock data for {symbol}, timeframe: {timeframe}")
    logger.info(f"Time range: {start_time} to {end_time}")
    
    # Generate mock data for time-based retrieval
    mock_data_time = generate_mock_market_data(symbol, timeframe, start_time, end_time)
    
    # Create a mock MT5Client that returns our mock data
    mock_mt5_client = MagicMock()
    mock_mt5_client.get_rates.return_value = mock_data_time
    mock_mt5_client.is_connected.return_value = True
    mock_mt5_client.connect.return_value = True
    
    # Patch the MT5Client in DataAcquisitionManager
    with patch('algotrader.controller.data_acquisition.MT5Client', return_value=mock_mt5_client):
        # Create DataAcquisitionManager with the mock
        data_manager = DataAcquisitionManager()
        
        # Get market data using time-based parameters
        df_time = data_manager.get_market_data(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
            include_volume=True
        )
    
    # Check if data was processed successfully
    if df_time.empty:
        logger.error("No data processed for time-based retrieval.")
    else:
        # Display data information
        logger.info(f"Processed {len(df_time)} data points for time-based retrieval")
        logger.info(f"Data range: {df_time.index.min()} to {df_time.index.max()}")
        
        # Display the first few rows
        print("\nData Sample (Time-based):")
        print(df_time.head())
        
        # Display basic statistics
        print("\nData Statistics (Time-based):")
        print(df_time.describe())
        
        # Plot the data
        plot_market_data(df_time, symbol, f"{timeframe}_time_based_mock")
    
    # Method 2: Position-based retrieval
    logger.info("\nMethod 2: Position-based retrieval with mock data")
    start_pos = 0
    end_pos = 100
    
    logger.info(f"Generating mock data for {symbol}, timeframe: {timeframe}")
    logger.info(f"Position range: {start_pos} to {end_pos}")
    
    # Generate mock data for position-based retrieval
    # For demonstration, we'll use the same mock data but slice it
    mock_data_pos = mock_data_time.iloc[0:end_pos-start_pos]
    
    # Update the mock MT5Client to return position-based mock data
    mock_mt5_client.get_rates.return_value = mock_data_pos
    
    # Patch the MT5Client in DataAcquisitionManager
    with patch('algotrader.controller.data_acquisition.MT5Client', return_value=mock_mt5_client):
        # Create DataAcquisitionManager with the mock
        data_manager = DataAcquisitionManager()
        
        # Get market data using position-based parameters
        df_pos = data_manager.get_market_data(
            symbol=symbol,
            timeframe=timeframe,
            start_pos=start_pos,
            end_pos=end_pos,
            include_volume=True
        )
    
    # Check if data was processed successfully
    if df_pos.empty:
        logger.error("No data processed for position-based retrieval.")
    else:
        # Display data information
        logger.info(f"Processed {len(df_pos)} data points for position-based retrieval")
        logger.info(f"Data range: {df_pos.index.min()} to {df_pos.index.max()}")
        
        # Display the first few rows
        print("\nData Sample (Position-based):")
        print(df_pos.head())
        
        # Display basic statistics
        print("\nData Statistics (Position-based):")
        print(df_pos.describe())
        
        # Plot the data
        plot_market_data(df_pos, symbol, f"{timeframe}_position_based_mock")

if __name__ == "__main__":
    try:
        test_get_market_data_with_mock()
    except Exception as e:
        logger.exception(f"Error in test_get_market_data_with_mock: {str(e)}") 