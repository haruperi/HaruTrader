"""
Simple script to test Telegram notifications.
"""
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from algotrader.controller.notification import NotificationManager

async def test_telegram():
    """Test sending a simple Telegram message."""
    print("Initializing NotificationManager...")
    notification_manager = NotificationManager()
    
    print("Sending test message...")
    result = await notification_manager.send_telegram_message(
        message="🧪 Test message from HaruTrader notification system",
        parse_mode="HTML",
        disable_notification=False
    )
    
    if result:
        print("✅ Message sent successfully!")
    else:
        print("❌ Failed to send message!")
    
    return result

if __name__ == "__main__":
    print("Starting Telegram notification test...")
    asyncio.run(test_telegram())
    print("Test completed.") 