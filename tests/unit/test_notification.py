"""
Test module for notification functionality.
"""
import asyncio
import pytest
from datetime import datetime
from algotrader.controller.notification import NotificationManager

@pytest.mark.asyncio
async def test_send_telegram_message():
    """Test sending a simple Telegram message."""
    notification_manager = NotificationManager()
    
    # Test basic message
    result = await notification_manager.send_telegram_message(
        message="🧪 Test message from HaruTrader notification system",
        parse_mode="HTML",
        disable_notification=False
    )
    
    assert result is True, "Failed to send basic Telegram message"
    
    # Allow some time between messages to avoid rate limiting
    await asyncio.sleep(1)
    
    # Test message with Markdown
    result = await notification_manager.send_telegram_message(
        message="*Bold text* and _italic text_ in a test message",
        parse_mode="Markdown",
        disable_notification=True
    )
    
    assert result is True, "Failed to send Markdown Telegram message"

@pytest.mark.asyncio
async def test_send_trade_notification():
    """Test sending a trade notification."""
    notification_manager = NotificationManager()
    
    # Test trade opened notification
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
    
    assert result is True, "Failed to send trade opened notification"
    
    # Allow some time between messages to avoid rate limiting
    await asyncio.sleep(1)
    
    # Test trade closed notification
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
    
    assert result is True, "Failed to send trade closed notification"

@pytest.mark.asyncio
async def test_send_error_notification():
    """Test sending an error notification."""
    notification_manager = NotificationManager()
    
    result = await notification_manager.send_error_notification(
        error_type="api_failure",
        error_message="Failed to connect to exchange API",
        error_data={
            'exchange': 'Binance',
            'endpoint': '/api/v3/ticker/price',
            'status_code': 503
        }
    )
    
    assert result is True, "Failed to send error notification"

@pytest.mark.asyncio
async def test_send_signal_notification():
    """Test sending a signal notification."""
    notification_manager = NotificationManager()
    
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
    
    assert result is True, "Failed to send signal notification"

@pytest.mark.asyncio
async def test_send_system_notification():
    """Test sending a system notification."""
    notification_manager = NotificationManager()
    
    result = await notification_manager.send_system_notification(
        notification_type="startup",
        message="HaruTrader system started successfully",
        data={
            'version': '1.0.0',
            'mode': 'live',
            'exchanges': ['Binance', 'Bybit']
        }
    )
    
    assert result is True, "Failed to send system notification"

@pytest.mark.asyncio
async def test_send_batch_notifications():
    """Test sending batch notifications."""
    notification_manager = NotificationManager()
    
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
    
    assert len(results) == 3, "Not all notifications were processed"
    assert all(results.values()), "Not all notifications were sent successfully"

if __name__ == "__main__":
    # Run the tests directly
    async def run_tests():
        print("Testing send_telegram_message...")
        await test_send_telegram_message()
        
        print("Testing send_trade_notification...")
        await test_send_trade_notification()
        
        print("Testing send_error_notification...")
        await test_send_error_notification()
        
        print("Testing send_signal_notification...")
        await test_send_signal_notification()
        
        print("Testing send_system_notification...")
        await test_send_system_notification()
        
        print("Testing send_batch_notifications...")
        await test_send_batch_notifications()
        
        print("All tests completed successfully!")
    
    asyncio.run(run_tests()) 