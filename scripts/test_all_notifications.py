"""
Comprehensive script to test all notification methods.
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from algotrader.controller.notification import NotificationManager

async def test_all_notifications():
    """Test all notification methods."""
    print("Initializing NotificationManager...")
    notification_manager = NotificationManager()
    
    # Test 1: Simple Telegram message
    print("\n1. Testing simple Telegram message...")
    result = await notification_manager.send_telegram_message(
        message="🧪 Test message from HaruTrader notification system",
        parse_mode="HTML",
        disable_notification=False
    )
    print("✅ Simple message test:", "Passed" if result else "Failed")
    
    # Wait to avoid rate limiting
    await asyncio.sleep(1)
    
    # Test 2: Trade notification (opened)
    print("\n2. Testing trade opened notification...")
    trade_data = {
        'symbol': 'BTCUSDT',
        'type': 'BUY',
        'entry': 65432.10,
        'sl': 64500.00,
        'tp': 67000.00,
        'volume': 0.05,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    result = await notification_manager.send_trade_notification(
        trade_type='trade_opened',
        trade_data=trade_data
    )
    print("✅ Trade opened notification test:", "Passed" if result else "Failed")
    
    # Wait to avoid rate limiting
    await asyncio.sleep(1)
    
    # Test 3: Trade notification (closed)
    print("\n3. Testing trade closed notification...")
    trade_data = {
        'symbol': 'BTCUSDT',
        'type': 'BUY',
        'entry': 65432.10,
        'exit': 66500.25,
        'profit': 53.41,
        'profit_pips': 106.8,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    result = await notification_manager.send_trade_notification(
        trade_type='trade_closed',
        trade_data=trade_data
    )
    print("✅ Trade closed notification test:", "Passed" if result else "Failed")
    
    # Wait to avoid rate limiting
    await asyncio.sleep(1)
    
    # Test 4: Error notification
    print("\n4. Testing error notification...")
    result = await notification_manager.send_error_notification(
        error_type="api_failure",
        error_message="Failed to connect to exchange API",
        error_data={
            'exchange': 'Binance',
            'endpoint': '/api/v3/ticker/price',
            'status_code': 503
        }
    )
    print("✅ Error notification test:", "Passed" if result else "Failed")
    
    # Wait to avoid rate limiting
    await asyncio.sleep(1)
    
    # Test 5: Signal notification
    print("\n5. Testing signal notification...")
    signal_data = {
        'symbol': 'ETHUSDT',
        'action': 'BUY',
        'price': 3245.75,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    result = await notification_manager.send_signal_notification(
        strategy_name='RSI_Divergence',
        signal_data=signal_data
    )
    print("✅ Signal notification test:", "Passed" if result else "Failed")
    
    # Wait to avoid rate limiting
    await asyncio.sleep(1)
    
    # Test 6: System notification
    print("\n6. Testing system notification...")
    result = await notification_manager.send_system_notification(
        notification_type="startup",
        message="HaruTrader system started successfully",
        data={
            'version': '1.0.0',
            'mode': 'live',
            'exchanges': ['Binance', 'Bybit']
        }
    )
    print("✅ System notification test:", "Passed" if result else "Failed")
    
    # Wait to avoid rate limiting
    await asyncio.sleep(1)
    
    # Test 7: Batch notifications
    print("\n7. Testing batch notifications...")
    notifications = [
        {
            'type': 'system',
            'system_type': 'info',
            'message': 'System info message 1',
            'data': {'timestamp': datetime.now().isoformat()}
        },
        {
            'type': 'system',
            'system_type': 'info',
            'message': 'System info message 2',
            'data': {'timestamp': datetime.now().isoformat()}
        },
        {
            'type': 'error',
            'error_type': 'warning',
            'message': 'Warning message',
            'data': {'source': 'test_batch'}
        }
    ]
    
    results = await notification_manager.send_batch_notifications(notifications)
    batch_success = len(results) == 3 and all(results.values())
    print("✅ Batch notifications test:", "Passed" if batch_success else "Failed")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    print("Starting comprehensive notification tests...")
    asyncio.run(test_all_notifications())
    print("Tests completed.") 