"""
Notification utility module.

This module provides a simple interface for sending notifications from anywhere in the application.
"""
from typing import Dict, Any, Optional
from ..controller.notification import NotificationManager

async def notify(
    event_type: str,
    event_name: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    priority: str = "normal",
    category: str = "system"
) -> bool:
    """
    Send a notification for any application event.
    
    This is a convenience function that can be imported and used from anywhere
    in the application to send notifications without having to create a
    NotificationManager instance.
    
    Args:
        event_type (str): Type of event (e.g., 'trade', 'system', 'error', 'signal')
        event_name (str): Specific name of the event (e.g., 'order_placed', 'startup', 'api_error')
        message (str): Human-readable message describing the event
        data (Optional[Dict[str, Any]]): Additional data related to the event
        priority (str): Priority level ('high', 'normal', 'low')
        category (str): Category for grouping similar events
        
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    notification_manager = NotificationManager.get_instance()
    return await notification_manager.notify_event(
        event_type=event_type,
        event_name=event_name,
        message=message,
        data=data,
        priority=priority,
        category=category
    )

# Convenience functions for common notification types

async def notify_trade(
    trade_action: str,
    message: str,
    trade_data: Dict[str, Any],
    priority: str = "normal"
) -> bool:
    """
    Send a trade-related notification.
    
    Args:
        trade_action (str): Action related to the trade (e.g., 'opened', 'closed', 'modified')
        message (str): Human-readable message describing the trade event
        trade_data (Dict[str, Any]): Trade-related data
        priority (str): Priority level ('high', 'normal', 'low')
        
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    return await notify(
        event_type="trade",
        event_name=trade_action,
        message=message,
        data=trade_data,
        priority=priority,
        category="trade"
    )

async def notify_error(
    error_type: str,
    message: str,
    error_data: Optional[Dict[str, Any]] = None,
    priority: str = "high"
) -> bool:
    """
    Send an error notification.
    
    Args:
        error_type (str): Type of error (e.g., 'api_failure', 'connection_error')
        message (str): Human-readable error message
        error_data (Optional[Dict[str, Any]]): Error-related data
        priority (str): Priority level ('high', 'normal', 'low')
        
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    return await notify(
        event_type="error",
        event_name=error_type,
        message=message,
        data=error_data,
        priority=priority,
        category="error"
    )

async def notify_signal(
    strategy_name: str,
    symbol: str,
    action: str,
    price: float,
    signal_data: Optional[Dict[str, Any]] = None,
    priority: str = "normal"
) -> bool:
    """
    Send a trading signal notification.
    
    Args:
        strategy_name (str): Name of the strategy generating the signal
        symbol (str): Trading symbol (e.g., 'BTCUSDT')
        action (str): Signal action (e.g., 'buy', 'sell')
        price (float): Price at which the signal was generated
        signal_data (Optional[Dict[str, Any]]): Additional signal-related data
        priority (str): Priority level ('high', 'normal', 'low')
        
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    data = signal_data or {}
    data.update({
        'strategy': strategy_name,
        'symbol': symbol,
        'action': action,
        'price': price
    })
    
    return await notify(
        event_type="signal",
        event_name=strategy_name,
        message=f"{action.upper()} signal for {symbol} at {price}",
        data=data,
        priority=priority,
        category="signal"
    )

async def notify_system(
    system_event: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    priority: str = "normal"
) -> bool:
    """
    Send a system notification.
    
    Args:
        system_event (str): Type of system event (e.g., 'startup', 'shutdown', 'config_change')
        message (str): Human-readable message describing the system event
        data (Optional[Dict[str, Any]]): Additional system-related data
        priority (str): Priority level ('high', 'normal', 'low')
        
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    return await notify(
        event_type="system",
        event_name=system_event,
        message=message,
        data=data,
        priority=priority,
        category="system"
    ) 