"""
Example usage of notification utilities in different parts of the application.
"""
import asyncio
import sys
import os
import random
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from algotrader.utils.notify import notify_trade, notify_error, notify_signal, notify_system

# Example 1: Using notifications in a trading module
async def example_trading_module():
    """Simulate a trading module that sends notifications."""
    print("Simulating trading module...")
    
    # Simulate trade execution
    print("Executing trade...")
    
    # Generate random trade data
    symbol = random.choice(["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"])
    trade_type = random.choice(["BUY", "SELL"])
    entry_price = round(random.uniform(20000, 70000), 2)
    
    # Calculate stop loss and take profit
    sl = round(entry_price * 0.98 if trade_type == "BUY" else entry_price * 1.02, 2)
    tp = round(entry_price * 1.05 if trade_type == "BUY" else entry_price * 0.95, 2)
    volume = round(random.uniform(0.01, 0.1), 2)
    
    # Send trade notification
    await notify_trade(
        trade_action="opened",
        message=f"New {trade_type} trade opened for {symbol}",
        trade_data={
            'symbol': symbol,
            'type': trade_type,
            'entry': entry_price,
            'sl': sl,
            'tp': tp,
            'volume': volume
        }
    )
    
    print(f"Trade executed: {trade_type} {volume} {symbol} at {entry_price}")

# Example 2: Using notifications in an error handler
async def example_error_handler():
    """Simulate an error handler that sends notifications."""
    print("Simulating error handler...")
    
    # Simulate different types of errors
    error_types = [
        ("api_failure", "Failed to connect to exchange API", {"exchange": "Binance", "endpoint": "/api/v3/ticker/price"}),
        ("authentication_failure", "Invalid API credentials", {"exchange": "Bybit"}),
        ("rate_limit", "Rate limit exceeded", {"exchange": "Binance", "limit": "10 requests/second"})
    ]
    
    # Choose a random error
    error_type, error_message, error_data = random.choice(error_types)
    
    # Send error notification
    await notify_error(
        error_type=error_type,
        message=error_message,
        error_data=error_data
    )
    
    print(f"Error handled: {error_type} - {error_message}")

# Example 3: Using notifications in a strategy module
async def example_strategy_module():
    """Simulate a strategy module that sends signal notifications."""
    print("Simulating strategy module...")
    
    # Simulate strategy analysis
    print("Analyzing market data...")
    
    # Generate random signal data
    strategy_name = random.choice(["RSI_Divergence", "MACD_Crossover", "Bollinger_Breakout"])
    symbol = random.choice(["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"])
    action = random.choice(["BUY", "SELL"])
    price = round(random.uniform(20000, 70000), 2)
    
    # Additional signal data based on strategy
    signal_data = {}
    if strategy_name == "RSI_Divergence":
        signal_data = {
            'rsi': round(random.uniform(20, 80), 1),
            'divergence_type': 'bullish' if action == "BUY" else 'bearish',
            'timeframe': random.choice(['1h', '4h', '1d'])
        }
    elif strategy_name == "MACD_Crossover":
        signal_data = {
            'macd': round(random.uniform(-100, 100), 2),
            'signal': round(random.uniform(-100, 100), 2),
            'histogram': round(random.uniform(-50, 50), 2),
            'timeframe': random.choice(['1h', '4h', '1d'])
        }
    else:  # Bollinger_Breakout
        signal_data = {
            'upper_band': round(price * 1.02, 2),
            'lower_band': round(price * 0.98, 2),
            'volatility': round(random.uniform(1, 5), 2),
            'timeframe': random.choice(['1h', '4h', '1d'])
        }
    
    # Send signal notification
    await notify_signal(
        strategy_name=strategy_name,
        symbol=symbol,
        action=action,
        price=price,
        signal_data=signal_data
    )
    
    print(f"Signal generated: {strategy_name} - {action} {symbol} at {price}")

# Example 4: Using notifications in a system module
async def example_system_module():
    """Simulate a system module that sends system notifications."""
    print("Simulating system module...")
    
    # Simulate system events
    system_events = [
        ("startup", "HaruTrader system started successfully", {"version": "1.0.0", "mode": "live"}),
        ("config_change", "Trading configuration updated", {"changes": ["max_trades", "risk_per_trade"]}),
        ("performance", "System performance report", {"cpu_usage": "45%", "memory_usage": "1.2GB"})
    ]
    
    # Choose a random system event
    event_type, message, data = random.choice(system_events)
    
    # Send system notification
    await notify_system(
        system_event=event_type,
        message=message,
        data=data
    )
    
    print(f"System event: {event_type} - {message}")

async def run_examples():
    """Run all examples."""
    print("Running notification examples...\n")
    
    print("\n=== Example 1: Trading Module ===")
    await example_trading_module()
    await asyncio.sleep(1)  # Wait to avoid rate limiting
    
    print("\n=== Example 2: Error Handler ===")
    await example_error_handler()
    await asyncio.sleep(1)  # Wait to avoid rate limiting
    
    print("\n=== Example 3: Strategy Module ===")
    await example_strategy_module()
    await asyncio.sleep(1)  # Wait to avoid rate limiting
    
    print("\n=== Example 4: System Module ===")
    await example_system_module()
    
    print("\nAll examples completed!")

if __name__ == "__main__":
    print("Starting notification examples...")
    asyncio.run(run_examples())
    print("Examples completed.") 