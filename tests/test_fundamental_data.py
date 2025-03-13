#!/usr/bin/env python
"""
Test script for fundamental data retrieval functionality.

This script demonstrates how to use the DataAcquisitionManager to retrieve
fundamental data for a trading symbol from multiple sources.
"""
import os
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import logging

# Add the parent directory to the path so we can import the app package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the necessary modules
from app.core.mt5_data import DataAcquisitionManager
from app.utils.logger import get_logger

# Set up logging
logger = get_logger(__name__)

def test_get_fundamental_data():
    """Test the get_fundamental_data function with various parameters."""
    logger.info("Initializing DataAcquisitionManager...")
    data_manager = DataAcquisitionManager()
    
    # Define test parameters
    symbol = "EURUSD"  # Example symbol
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Get 30 days of data
    
    logger.info(f"Retrieving fundamental data for {symbol}")
    logger.info(f"Time range: {start_date} to {end_date}")
    
    # Method 1: Get data from all sources
    logger.info("Method 1: Get data from all sources")
    fundamental_data_all = data_manager.get_fundamental_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        data_sources=['all'],
        include_sentiment=True
    )
    
    # Display the results
    display_fundamental_data(fundamental_data_all, "All Sources")
    
    # Method 2: Get data from specific sources
    logger.info("Method 2: Get data from specific sources")
    fundamental_data_specific = data_manager.get_fundamental_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        data_sources=['investpy', 'forex_factory'],
        include_sentiment=False
    )
    
    # Display the results
    display_fundamental_data(fundamental_data_specific, "Specific Sources (No Sentiment)")
    
    # Plot sentiment data if available
    if fundamental_data_all.get('sentiment') and 'social_media' in fundamental_data_all['sentiment']:
        plot_sentiment_data(fundamental_data_all, symbol)
    
    # Plot economic events if available
    if not fundamental_data_all.get('economic_events', pd.DataFrame()).empty:
        plot_economic_events(fundamental_data_all, symbol)
    
    logger.info("Fundamental data test completed")

def display_fundamental_data(data, source_description):
    """
    Display the fundamental data in a readable format.
    
    Args:
        data (Dict[str, Any]): Fundamental data
        source_description (str): Description of the data source
    """
    logger.info(f"=== Fundamental Data from {source_description} ===")
    
    # Display metadata
    logger.info("Metadata:")
    sources_used = data.get('source_metadata', {}).get('sources_used', [])
    logger.info(f"  Sources used: {', '.join(sources_used)}")
    
    retrieval_time = data.get('source_metadata', {}).get('retrieval_time')
    if retrieval_time:
        logger.info(f"  Retrieval time: {retrieval_time}")
    
    # Display data quality
    data_quality = data.get('source_metadata', {}).get('data_quality', {})
    if data_quality:
        logger.info("Data Quality:")
        logger.info(f"  Completeness score: {data_quality.get('completeness_score', 0):.2f}")
        
        for key, value in data_quality.items():
            if key != 'completeness_score':
                logger.info(f"  {key}: {value}")
    
    # Display warnings
    warnings = data.get('source_metadata', {}).get('warnings', [])
    if warnings:
        logger.info("Warnings:")
        for warning in warnings:
            logger.info(f"  - {warning}")
    
    # Display company info
    company_info = data.get('company_info', {})
    if company_info:
        logger.info("Company Information:")
        for key, value in company_info.items():
            logger.info(f"  {key}: {value}")
    
    # Display economic events
    economic_events = data.get('economic_events', pd.DataFrame())
    if not economic_events.empty:
        logger.info("Economic Events:")
        logger.info(f"  Number of events: {len(economic_events)}")
        if len(economic_events) > 0:
            logger.info("  Sample events:")
            sample = economic_events.head(3)
            for _, row in sample.iterrows():
                event_info = []
                for col in sample.columns:
                    event_info.append(f"{col}: {row[col]}")
                logger.info(f"    - {', '.join(event_info)}")
    
    # Display sentiment data
    sentiment = data.get('sentiment', {})
    if sentiment:
        logger.info("Sentiment Data:")
        for source, values in sentiment.items():
            if source != 'mentions_history':
                logger.info(f"  {source}:")
                for key, value in values.items():
                    logger.info(f"    {key}: {value:.4f}")
    
    # Display market sentiment
    market_sentiment = data.get('market_sentiment', {})
    if market_sentiment:
        logger.info("Market Sentiment:")
        for source, values in market_sentiment.items():
            logger.info(f"  {source}:")
            for key, value in values.items():
                logger.info(f"    {key}: {value:.4f}")
    
    logger.info("=" * 50)

def plot_sentiment_data(data, symbol):
    """
    Plot sentiment data.
    
    Args:
        data (Dict[str, Any]): Fundamental data
        symbol (str): Trading symbol
    """
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'plots')
    os.makedirs(output_dir, exist_ok=True)
    
    # Set up the plot
    plt.figure(figsize=(12, 6))
    sns.set_style('whitegrid')
    
    # Extract sentiment data
    sentiment = data.get('sentiment', {})
    
    # Plot social media sentiment if available
    social_sentiment = sentiment.get('social_media', {})
    if social_sentiment:
        labels = ['Bullish', 'Bearish', 'Neutral']
        values = [
            social_sentiment.get('bullish', 0),
            social_sentiment.get('bearish', 0),
            social_sentiment.get('neutral', 0)
        ]
        
        plt.bar(labels, values, color=['green', 'red', 'blue'], alpha=0.7)
        plt.title(f'Social Media Sentiment for {symbol}')
        plt.ylabel('Sentiment Score')
        plt.ylim(0, 1.0)
        
        # Add value labels on top of bars
        for i, v in enumerate(values):
            plt.text(i, v + 0.02, f'{v:.2f}', ha='center')
        
        # Save the plot
        output_path = os.path.join(output_dir, f'{symbol}_sentiment.png')
        plt.savefig(output_path)
        logger.info(f"Sentiment plot saved to {output_path}")
        plt.close()
    
    # Plot mentions history if available
    mentions_history = sentiment.get('mentions_history')
    if mentions_history is not None and not mentions_history.empty:
        plt.figure(figsize=(12, 6))
        
        # Assuming mentions_history has 'date' and 'count' columns
        if 'date' in mentions_history.columns and 'count' in mentions_history.columns:
            sns.lineplot(x='date', y='count', data=mentions_history)
            plt.title(f'Social Media Mentions for {symbol}')
            plt.xlabel('Date')
            plt.ylabel('Number of Mentions')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save the plot
            output_path = os.path.join(output_dir, f'{symbol}_mentions.png')
            plt.savefig(output_path)
            logger.info(f"Mentions plot saved to {output_path}")
            plt.close()

def plot_economic_events(data, symbol):
    """
    Plot economic events.
    
    Args:
        data (Dict[str, Any]): Fundamental data
        symbol (str): Trading symbol
    """
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'plots')
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract economic events
    economic_events = data.get('economic_events', pd.DataFrame())
    
    if not economic_events.empty and 'date' in economic_events.columns and 'importance' in economic_events.columns:
        # Count events by date and importance
        if 'importance' in economic_events.columns:
            # Convert to datetime if not already
            if not pd.api.types.is_datetime64_any_dtype(economic_events['date']):
                economic_events['date'] = pd.to_datetime(economic_events['date'])
            
            # Group by date and importance
            event_counts = economic_events.groupby([
                economic_events['date'].dt.date, 'importance'
            ]).size().unstack(fill_value=0)
            
            # Plot
            plt.figure(figsize=(14, 7))
            event_counts.plot(kind='bar', stacked=True, colormap='viridis')
            plt.title(f'Economic Events Affecting {symbol}')
            plt.xlabel('Date')
            plt.ylabel('Number of Events')
            plt.xticks(rotation=45)
            plt.legend(title='Importance')
            plt.tight_layout()
            
            # Save the plot
            output_path = os.path.join(output_dir, f'{symbol}_economic_events.png')
            plt.savefig(output_path)
            logger.info(f"Economic events plot saved to {output_path}")
            plt.close()

def main():
    """Main function to run the test."""
    try:
        test_get_fundamental_data()
    except Exception as e:
        logger.exception(f"Error in test_get_fundamental_data: {str(e)}")

if __name__ == "__main__":
    main() 