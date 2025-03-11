"""
Test script for the notification utility functions.
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from algotrader.utils.notify import (
    notify,
    notify_trade,
    notify_error,
    notify_signal,
    notify_system
)

async def test_notification_utils():
    """Test all notification utility functions."""
    print("Starting notification utility tests...")
    
    # Test 1: Generic notification
    print("\n1. Testing generic notification...")
    result = await notify(
        event_type="test",
        event_name="generic_test",
        message="This is a generic test notification",
        data={"test_id": 1, "timestamp": datetime.now().isoformat()},
        priority="normal",
        category="test"
    )
    print("✅ Generic notification test:", "Passed" if result else "Failed")
    
    # Wait to avoid rate limiting
    await asyncio.sleep(1)
    
    # Test 2: Trade notification
    print("\n2. Testing trade notification...")
    result = await notify_trade(
        trade_action="opened",
        message="New trade opened",
        trade_data={
            'symbol': 'BTCUSDT',
            'type': 'BUY',
            'entry': 65432.10,
            'sl': 64500.00,
            'tp': 67000.00,
            'volume': 0.05
        }
    )
    print("✅ Trade notification test:", "Passed" if result else "Failed")
    
    # Wait to avoid rate limiting
    await asyncio.sleep(1)
    
    # Test 3: Error notification
    print("\n3. Testing error notification...")
    result = await notify_error(
        error_type="connection_error",
        message="Failed to connect to exchange API",
        error_data={
            'exchange': 'Binance',
            'endpoint': '/api/v3/ticker/price',
            'status_code': 503
        }
    )
    print("✅ Error notification test:", "Passed" if result else "Failed")
    
    # Wait to avoid rate limiting
    await asyncio.sleep(1)
    
    # Test 4: Signal notification
    print("\n4. Testing signal notification...")
    result = await notify_signal(
        strategy_name="RSI_Divergence",
        symbol="ETHUSDT",
        action="BUY",
        price=3245.75,
        signal_data={
            'rsi': 32.5,
            'divergence_type': 'bullish',
            'timeframe': '4h'
        }
    )
    print("✅ Signal notification test:", "Passed" if result else "Failed")
    
    # Wait to avoid rate limiting
    await asyncio.sleep(1)
    
    # Test 5: System notification
    print("\n5. Testing system notification...")
    result = await notify_system(
        system_event="startup",
        message="HaruTrader system started successfully",
        data={
            'version': '1.0.0',
            'mode': 'live',
            'exchanges': ['Binance', 'Bybit']
        }
    )
    print("✅ System notification test:", "Passed" if result else "Failed")
    
    print("\nAll notification utility tests completed!")

if __name__ == "__main__":
    print("Starting notification utility tests...")
    asyncio.run(test_notification_utils())
    print("Tests completed.") 